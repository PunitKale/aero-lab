"""Structured application logs."""
import json
import logging

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps({"level":record.levelname,"message":record.getMessage(),"module":record.name})

def configure_logging() -> None:
    """Emit one JSON object per application log record."""
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)
