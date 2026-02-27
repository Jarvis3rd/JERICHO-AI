#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   config.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Configuration for local deployment
"""

# pylint: disable=R0902

from __future__ import annotations

import json
import os
from typing import List, Union

import msgspec
from msgspec import MsgspecError, Struct, field

from datature.nexus.cli.deploy.local.consts import (
    DEFAULT_ALLOWED_ORIGINS,
    DEFAULT_DEVICES,
    DEFAULT_PORT,
    DEFAULT_RUNTIME,
    DEPLOY_CONFIGS_FILE_PATH,
)


class DeploymentConfig(Struct, rename="camel", kw_only=True):
    """Configuration for local deployment"""

    deployment_id: str
    secret_key: str
    project_id: str
    project_name: str
    artifact_id: str
    artifact_name: str
    runtime: str = DEFAULT_RUNTIME
    devices: Union[str, int] = DEFAULT_DEVICES
    port: int = DEFAULT_PORT
    allowed_origins: List[str] = field(default_factory=lambda: DEFAULT_ALLOWED_ORIGINS)


class DeploymentConfigs(Struct, rename="camel", kw_only=True):
    """Configuration list for local deployment"""

    configs: List[DeploymentConfig] = field(default_factory=list)

    def __post_init__(self):
        if not DEPLOY_CONFIGS_FILE_PATH.exists():
            os.makedirs(DEPLOY_CONFIGS_FILE_PATH.parent, exist_ok=True)
            with open(DEPLOY_CONFIGS_FILE_PATH, "w", encoding="utf-8") as config_file:
                config_file.write("[]")

    def write_to_file(self) -> None:
        """Write DeploymentConfigs to file."""
        try:
            with open(DEPLOY_CONFIGS_FILE_PATH, "w", encoding="utf-8") as config_file:
                json.dump(msgspec.to_builtins(self), config_file)

        except (IOError, MsgspecError) as exc:
            print(
                f"Error writing DeploymentConfigs to {DEPLOY_CONFIGS_FILE_PATH}: {exc}"
            )
            raise exc

    @classmethod
    def read_from_file(cls) -> DeploymentConfigs:
        """Read DeploymentConfigs from file."""
        if not DEPLOY_CONFIGS_FILE_PATH.exists():
            return cls()

        with open(DEPLOY_CONFIGS_FILE_PATH, "r", encoding="utf-8") as config_file:
            json_data = json.loads(config_file.read())
            return msgspec.convert(json_data, type=DeploymentConfigs)
