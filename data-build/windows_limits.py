"""Windows job limits for local profiling, applied only to the profiling process."""

import ctypes
from ctypes import wintypes
from contextlib import contextmanager
import os
import time


_handles = []


@contextmanager
def prevent_idle_sleep():
    if os.name != "nt":
        raise RuntimeError("Idle-sleep prevention uses a Windows execution-state request.")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.SetThreadExecutionState.argtypes = [wintypes.DWORD]
    kernel.SetThreadExecutionState.restype = wintypes.DWORD
    previous = kernel.SetThreadExecutionState(0x80000000 | 0x00000001 | 0x00000002)
    if not previous:
        raise RuntimeError("Could not request benchmark-only idle-sleep prevention.")
    try:
        yield
    finally:
        if not kernel.SetThreadExecutionState(previous):
            raise RuntimeError("Could not restore the benchmark thread's execution state.")


def constrain(cpu_cores=.1, memory_mib=512):
    if os.name != "nt":
        raise RuntimeError("This constrained profiler uses Windows Job Objects.")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    kernel.CreateJobObjectW.restype = wintypes.HANDLE
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    kernel.QueryInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p,
                                                wintypes.DWORD, ctypes.c_void_p]
    kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]

    class Basic(ctypes.Structure):
        _fields_ = [("PerProcessUserTimeLimit", ctypes.c_longlong), ("PerJobUserTimeLimit", ctypes.c_longlong),
                    ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                    ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
                    ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD),
                    ("SchedulingClass", wintypes.DWORD)]

    class Io(ctypes.Structure):
        _fields_ = [(name, ctypes.c_ulonglong) for name in ("ReadOperationCount", "WriteOperationCount",
                    "OtherOperationCount", "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]

    class Extended(ctypes.Structure):
        _fields_ = [("BasicLimitInformation", Basic), ("IoInfo", Io),
                    ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                    ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]

    class Cpu(ctypes.Structure):
        _fields_ = [("ControlFlags", wintypes.DWORD), ("CpuRate", wintypes.DWORD)]

    def check(success):
        if not success:
            raise ctypes.WinError(ctypes.get_last_error())

    handle = kernel.CreateJobObjectW(None, None)
    check(handle)
    _handles.append(handle)
    limits = Extended()
    limits.BasicLimitInformation.LimitFlags = 0x100 | 0x200
    limits.ProcessMemoryLimit = limits.JobMemoryLimit = memory_mib * 1024 * 1024
    check(kernel.SetInformationJobObject(handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)))
    rate = max(1, round(10000 * cpu_cores / os.cpu_count()))
    cpu = Cpu(0x1 | 0x4, rate)
    check(kernel.SetInformationJobObject(handle, 15, ctypes.byref(cpu), ctypes.sizeof(cpu)))
    check(kernel.AssignProcessToJobObject(handle, kernel.GetCurrentProcess()))
    actual_cpu, actual_limits = Cpu(), Extended()
    check(kernel.QueryInformationJobObject(handle, 15, ctypes.byref(actual_cpu), ctypes.sizeof(actual_cpu), None))
    check(kernel.QueryInformationJobObject(handle, 9, ctypes.byref(actual_limits), ctypes.sizeof(actual_limits), None))
    started, cpu_started = time.perf_counter(), time.process_time()
    value = 1
    while time.perf_counter() - started < 5:
        value = (value * 13 + 7) % 999983
    measured = (time.process_time() - cpu_started) / (time.perf_counter() - started)
    return {"requestedCpuCoreEquivalent": cpu_cores, "cpuRateUnitsPer10000": actual_cpu.CpuRate,
            "logicalCpuCount": os.cpu_count(), "memoryCommitLimitBytes": actual_limits.JobMemoryLimit,
            "calibrationCpuSecondsPerWallSecond": measured,
            "method": "Windows Job Object CPU hard cap and 512 MiB process/job committed-memory cap"}
