# app/logging_config.py
import logging
import logging.config
import logging.config
from uvicorn.logging import AccessFormatter

class TimedAccessFormatter(AccessFormatter):
    def formatMessage(self, record) -> str:
        msg = super().formatMessage(record)
        duration_ms = getattr(record, "duration_ms", None)
        if duration_ms is not None:
            msg = f"{msg} {duration_ms:.2f}ms"
        return msg

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s %(name)s: %(message)s",
            "use_colors": True,
        },
        "access": {
            "()": "app.logging_config.TimedAccessFormatter",
            "fmt": '%(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s',
            "use_colors": True,
        },
    },

    "handlers": {
        "default": {"class": "logging.StreamHandler", "formatter": "default"},
        "access": {"class": "logging.StreamHandler", "formatter": "access"},
    },

    "root": {"handlers": ["default"], "level": "WARNING"},

    "loggers": {
        "uvicorn.error": {"handlers": ["default"], "level": "INFO", "propagate": False},
        "uvicorn.access": {"handlers": [], "level": "CRITICAL", "propagate": False},
        "app.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
        "app": {"handlers": ["default"], "level": "DEBUG", "propagate": False},
    },
}

def setup_logging() -> None:
    logging.config.dictConfig(LOGGING_CONFIG)

def get_logger(name: str = "app") -> logging.Logger:
    return logging.getLogger(name)
