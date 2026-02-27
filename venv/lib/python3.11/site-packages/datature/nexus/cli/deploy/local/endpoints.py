#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   endpoints.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Custom endpoints for the inference server.
"""

import re
import time
from datetime import datetime
from typing import Tuple

import msgspec
from fastapi.routing import APIRoute
from litserve.server import LitServer
from starlette.responses import RedirectResponse

from datature.nexus.cli.deploy.local.logger import LOG_STREAM, LogStreamTracker
from datature.nexus.cli.deploy.local.types.endpoint_response import (
    HealthResponse,
    LogEntry,
    LogResponse,
)

log_filter_patterns = [
    "GET /health",
    "GET /logs",
]


def remove_terminal_colors(text: str) -> str:
    """Remove ANSI terminal color codes from a string."""
    ansi_escape_pattern = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape_pattern.sub("", text)


def parse_log_line(log_line: str) -> Tuple[int, str]:
    """
    Parse a log line into timestamp and message.

    Args:
        log_line: Log line in format "timestamp message"

    Returns:
        Tuple of (timestamp: int, message: str)
    """
    # split on the second space
    parts = log_line.split("\t", 1)

    if len(parts) == 2:
        try:
            timestamp = int(
                datetime.strptime(parts[0], "%Y-%m-%d %H:%M:%S.%f").timestamp() * 1000
            )
            message = parts[1]
            return timestamp, message
        except ValueError:
            return 0, log_line
    else:
        return 0, log_line


def add_custom_endpoints(server: LitServer, project_id: str, project_name: str):
    """Add custom endpoints to LitServer"""

    @server.app.get("/health")
    async def health(project_id: str = project_id, project_name: str = project_name):
        """Health check endpoint."""
        response = HealthResponse(
            status="ok",
            timestamp=int(time.time() * 1000),
            project=project_id,
            project_name=project_name,
        )
        return msgspec.to_builtins(response)

    @server.app.get("/logs")
    async def get_logs():
        """Get recent server logs."""
        log_lines = [
            remove_terminal_colors(line.strip())
            for line in reversed(
                LOG_STREAM.getvalue()[LogStreamTracker.pointer :].split("\n")
            )
            if line.strip()
            and not any(pattern in line.strip() for pattern in log_filter_patterns)
        ]

        LogStreamTracker.pointer = len(LOG_STREAM.getvalue())

        response = LogResponse(
            logs=[
                LogEntry(timestamp=timestamp, message=message)
                for timestamp, message in map(parse_log_line, log_lines)
            ]
        )

        return msgspec.to_builtins(response)

    @server.app.get("/all-logs")
    async def get_all_logs():
        """Get all historical server logs."""
        log_lines = [
            remove_terminal_colors(line.strip())
            for line in reversed(LOG_STREAM.getvalue().split("\n"))
            if line.strip()
        ]

        response = LogResponse(
            logs=[
                LogEntry(timestamp=timestamp, message=message)
                for timestamp, message in map(parse_log_line, log_lines)
            ]
        )

        return msgspec.to_builtins(response)

    def replace_route(path: str, new_handler, methods=None):
        if methods is None:
            methods = ["GET"]

        for i, route in enumerate(server.app.router.routes):
            if isinstance(route, APIRoute) and route.path == path:
                new_route = APIRoute(path=path, endpoint=new_handler, methods=methods)
                server.app.router.routes[i] = new_route
                break

    async def index():
        """Index endpoint."""
        return RedirectResponse(url="/docs")

    replace_route("/", index)

    return server
