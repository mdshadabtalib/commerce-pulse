from __future__ import annotations

import json
import logging
import logging.handlers
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Any

from .config import settings


class JsonFormatter(logging.Formatter):
    RESERVED_ATTRS: set[str] = {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
        "taskName",
    }

    def format(self, record: logging.LogRecord) -> str:
        log_record: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process_id": record.process,
            "thread_id": record.thread,
        }

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        if record.stack_info:
            log_record["stack_info"] = self.formatStack(record.stack_info)

        for key, value in record.__dict__.items():
            if key not in self.RESERVED_ATTRS and not key.startswith("_"):
                if isinstance(value, (dict, list, tuple, str, int, float, bool, type(None))):
                    log_record[key] = value
                else:
                    log_record[key] = str(value)

        extra_fields = getattr(record, "extra_fields", None)
        if isinstance(extra_fields, dict):
            log_record.update(extra_fields)

        return json.dumps(log_record, default=str, ensure_ascii=False)


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        from contextvars import ContextVar

        request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
        user_id_var: ContextVar[str | None] = ContextVar("user_id", default=None)
        org_id_var: ContextVar[str | None] = ContextVar("org_id", default=None)

        record.request_id = request_id_var.get() or getattr(record, "request_id", None) or str(uuid.uuid4())
        record.user_id = user_id_var.get() or getattr(record, "user_id", None)
        record.organization_id = org_id_var.get() or getattr(record, "organization_id", None)
        record.environment = settings.ENVIRONMENT.value
        record.service = settings.APP_NAME
        return True


def _ensure_log_dir(log_path: str) -> None:
    log_dir = os.path.dirname(log_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)


def _build_formatter(format_type: str) -> logging.Formatter:
    if format_type == "json":
        return JsonFormatter()
    elif format_type == "console":
        return logging.Formatter(
            "%(asctime)s | %(levelname)-7s | %(name)s:%(funcName)s:%(lineno)d | request_id=%(request_id)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    return logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def configure_logging() -> logging.Logger:
    log_level = getattr(logging, settings.LOG_LEVEL, logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    formatter = _build_formatter(settings.LOG_FORMAT)
    context_filter = RequestContextFilter()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(context_filter)
    root_logger.addHandler(console_handler)

    if settings.LOG_FILE_PATH:
        _ensure_log_dir(settings.LOG_FILE_PATH)
        file_handler = logging.handlers.RotatingFileHandler(
            filename=settings.LOG_FILE_PATH,
            maxBytes=settings.LOG_MAX_BYTES,
            backupCount=settings.LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(context_filter)
        root_logger.addHandler(file_handler)

    noisy_loggers = {
        "uvicorn.access": logging.WARNING,
        "uvicorn.error": logging.INFO,
        "sqlalchemy.engine": logging.WARNING,
        "sqlalchemy.pool": logging.WARNING,
        "botocore": logging.WARNING,
        "boto3": logging.WARNING,
        "urllib3": logging.WARNING,
        "stripe": logging.WARNING,
        "httpx": logging.WARNING,
        "httpcore": logging.WARNING,
        "celery": logging.INFO,
        "kombu": logging.WARNING,
    }
    for logger_name, level in noisy_loggers.items():
        target = logging.getLogger(logger_name)
        target.setLevel(level)

    app_logger = logging.getLogger(settings.APP_NAME.lower())
    app_logger.setLevel(log_level)

    return app_logger


def get_logger(name: str) -> logging.Logger:
    if not logging.getLogger().handlers:
        configure_logging()
    return logging.getLogger(name)
