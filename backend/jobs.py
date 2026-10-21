"""Admit before submission; a slot belongs to the real worker until it exits."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
import threading
import time

from .errors import ApiError, ClientDisconnected, timeout


@dataclass
class Cancellation:
    deadline: float
    stopped: threading.Event = field(default_factory=threading.Event)

    def cancelled(self):
        return self.stopped.is_set() or time.monotonic() >= self.deadline

    def check(self):
        if self.cancelled():
            raise timeout()


class Jobs:
    def __init__(self, slots, seconds):
        self.slots, self.seconds = slots, seconds
        self.executor = ThreadPoolExecutor(max_workers=slots, thread_name_prefix="fda-sql")
        self.active = {}
        self.closed = False
        self.peak_active = 0
        self.outcomes = {"busy": 0, "completed": 0, "timeout": 0, "disconnect": 0}

    async def run(self, request, operation):
        if self.closed or len(self.active) >= self.slots:
            self.outcomes["busy"] += 1
            raise ApiError(503, "SERVICE_BUSY", "Database capacity is busy; try again.", retryable=True)
        token = Cancellation(request.state.started + self.seconds)
        token.check()
        loop = asyncio.get_running_loop()
        future = loop.run_in_executor(self.executor, operation, token)
        self.active[future] = token
        self.peak_active = max(self.peak_active, len(self.active))

        def finished(done):
            self.active.pop(done, None)
            if not done.cancelled():
                done.exception()  # Consume errors even when the HTTP reader has disconnected.

        future.add_done_callback(finished)
        try:
            while True:
                token.check()
                done, _ = await asyncio.wait({future}, timeout=min(.05, max(0, token.deadline - time.monotonic())))
                if done:
                    result = future.result()
                    token.check()
                    self.outcomes["completed"] += 1
                    return result
                if await request.is_disconnected():
                    raise ClientDisconnected
        except (asyncio.CancelledError, ClientDisconnected):
            self.outcomes["disconnect"] += 1
            raise
        except ApiError as error:
            if error.code == "QUERY_TIMEOUT":
                self.outcomes["timeout"] += 1
            raise
        finally:
            token.stopped.set()

    async def close(self):
        self.closed = True
        for token in self.active.values():
            token.stopped.set()
        if self.active:
            await asyncio.gather(*list(self.active), return_exceptions=True)
        self.executor.shutdown(wait=True, cancel_futures=True)
