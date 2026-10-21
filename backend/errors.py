"""Public errors do not echo input, SQL, paths or internal exceptions."""


class ApiError(Exception):
    def __init__(self, status, code, message, *, retryable=False):
        super().__init__(message)
        self.status, self.code, self.message, self.retryable = status, code, message, retryable


class ClientDisconnected(Exception):
    """Internal control flow: there is no connected client to receive an error."""


def unavailable():
    return ApiError(503, "DATA_UNAVAILABLE", "The checked data snapshot is unavailable.", retryable=True)


def timeout():
    return ApiError(503, "QUERY_TIMEOUT", "The request exceeded its resource budget.")
