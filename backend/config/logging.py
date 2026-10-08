import logging


class RequestContextFilter(logging.Filter):
    """Adds a non-sensitive correlation value without logging user payloads."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = getattr(record, "request_id", "-")
        return True
