#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   endpoint_response.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Endpoint response type.
"""

from typing import List

from msgspec import Struct


class HealthResponse(Struct, kw_only=True, omit_defaults=True, rename="camel"):
    """Health response object.

    Attributes:
        project: The current project ID.
        project_name: The current project name.
        timestamp: The timestamp of the response in milliseconds.
        status: The status of the response.
    """

    project: str
    project_name: str
    timestamp: int
    status: str


class LogEntry(Struct, kw_only=True, omit_defaults=True, rename="camel"):
    """Log entry object.

    Attributes:
        timestamp: The timestamp of the log entry in milliseconds.
        message: The message of the log entry.
    """

    timestamp: int
    message: str


class LogResponse(Struct, kw_only=True, omit_defaults=True, rename="camel"):
    """Log response object.

    Attributes:
        logs: The logs of the response.
    """

    logs: List[LogEntry]
