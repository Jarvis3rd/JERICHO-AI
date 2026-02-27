#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██
@File    :   logger.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Logger configuration for the local deployment server.
"""

from io import StringIO

LOG_STREAM = StringIO()

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(asctime)s.%(msecs)03d\t%(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "use_colors": None,
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": "%(asctime)s.%(msecs)03d\t%(client_addr)s - %(request_line)s %(status_code)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "use_colors": None,
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": LOG_STREAM,
        },
        "default_stdout": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
            "stream": LOG_STREAM,
        },
    },
    "loggers": {
        "uvicorn": {
            "handlers": ["default", "default_stdout"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.error": {"level": "INFO"},
        "uvicorn.access": {
            "handlers": ["access"],
            "level": "INFO",
            "propagate": False,
        },
        "litserve": {
            "handlers": ["default", "default_stdout"],
            "level": "ERROR",
            "propagate": False,
        },
        "litserve.server": {
            "handlers": ["access"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}


class LogStreamTracker:
    """Tracks the position in the log stream across server lifetime."""

    pointer = 0
