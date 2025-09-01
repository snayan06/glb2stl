import logging
from logging.config import dictConfig

from .config import settings


def configure_logging() -> None:
    formatters = {
        "default": {"format": "%(asctime)s %(levelname)s %(name)s - %(message)s"},
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        },
    }
    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "level": settings.LOG_LEVEL,
            "formatter": "default" if settings.LOG_FORMAT == "console" else "json",
        }
    }
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": formatters,
            "handlers": handlers,
            "loggers": {
                "": {"handlers": ["console"], "level": settings.LOG_LEVEL},
                "uvicorn": {
                    "handlers": ["console"],
                    "level": settings.LOG_LEVEL,
                    "propagate": False,
                },
                "uvicorn.error": {
                    "handlers": ["console"],
                    "level": settings.LOG_LEVEL,
                    "propagate": False,
                },
                "uvicorn.access": {
                    "handlers": ["console"],
                    "level": settings.LOG_LEVEL,
                    "propagate": False,
                },
            },
        }
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
