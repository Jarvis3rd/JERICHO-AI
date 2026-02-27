#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██
@File    :   server.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Local deployment server.
"""

# pylint: disable=R0913,R0917

from typing import List, Optional, Union

import litserve as ls
from starlette.middleware.cors import CORSMiddleware

from datature.nexus.cli.deploy.local.api import InferenceAPI
from datature.nexus.cli.deploy.local.consts import (
    DEFAULT_ALLOWED_METHODS,
    DEFAULT_ALLOWED_ORIGINS,
    DEFAULT_MAX_AGE,
    DEFAULT_PORT,
    DEFAULT_RUNTIME,
    DEFAULT_TIMEOUT,
)
from datature.nexus.cli.deploy.local.endpoints import add_custom_endpoints
from datature.nexus.cli.deploy.local.logger import LOGGING_CONFIG


def start_server(
    deployment_id: str,
    secret_key: str,
    project_id: str,
    project_name: str,
    artifact_id: str,
    artifact_name: str,
    runtime: str = DEFAULT_RUNTIME,
    devices: Union[str, int] = "auto",
    port: int = DEFAULT_PORT,
    allowed_origins: Optional[List[str]] = None,
):
    """Start the local deployment server

    Args:
        deployment_id: The deployment ID
        secret_key: The project secret key
        project_id: The project ID
        project_name: The project name
        artifact_id: The artifact ID
        runtime: The runtime to use (CPU or GPU), defaults to CPU
        port: The port to use, defaults to 9449
        allowed_origins: The origins to allow as a comma-separated string,
            defaults to https://nexus.datature.io
    """
    if allowed_origins is None:
        allowed_origins = DEFAULT_ALLOWED_ORIGINS.copy()

    # Initialize the inference API
    api = InferenceAPI(secret_key, project_id, artifact_id, runtime)

    cors_middleware = (
        CORSMiddleware,
        {
            "allow_origins": allowed_origins,
            "allow_methods": DEFAULT_ALLOWED_METHODS,
            "allow_headers": ["*"],
            "allow_credentials": True,
            "max_age": DEFAULT_MAX_AGE,
        },
    )

    server = ls.LitServer(
        api,
        accelerator="cpu" if runtime == DEFAULT_RUNTIME else "cuda",
        devices=devices,
        middlewares=[cors_middleware],
        model_metadata={
            "deployment_id": deployment_id,
            "project_id": project_id,
            "artifact_id": artifact_id,
            "artifact_name": artifact_name,
        },
        track_requests=True,
        timeout=DEFAULT_TIMEOUT,
        healthcheck_path="/datature-local-deployment-ping",
    )

    server = add_custom_endpoints(
        server, project_id.removeprefix("proj_"), project_name
    )

    server.run(
        port=port,
        log_config=LOGGING_CONFIG,
        generate_client_file=False,
        num_api_servers=int(devices) if devices != "auto" else None,
    )
