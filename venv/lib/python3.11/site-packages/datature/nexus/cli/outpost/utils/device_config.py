#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   device_config.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Outpost device configuration module.
"""

from pathlib import Path
from typing import Any, Dict, Union

import msgspec
import yaml
from msgspec import Struct, field

from datature.nexus.cli.outpost import consts as CONSTS


class DeviceConfig(Struct, kw_only=True):
    """Device configuration.

    :param device: Device configuration.
    :param authentication: Authentication configuration.
    :param management_api: Management API configuration.
    :param mqtt: MQTT configuration.
    :param statsd: StatsD configuration
    """

    device: Dict[str, Any] = field(default_factory=dict)
    authentication: Dict[str, Any] = field(default_factory=dict)
    management_api: Dict[str, Any] = field(default_factory=dict)
    mqtt: Dict[str, Any] = field(default_factory=dict)
    statsd: Dict[str, Any] = field(default_factory=dict)
    version: str = field(default="1.0.0")

    def write_to_file(self, config_path: Union[Path, str]) -> None:
        """Write service configuration to file."""
        try:
            config_dict = msgspec.to_builtins(self)

            with open(config_path, "w", encoding="utf-8") as config_file:
                yaml.dump(config_dict, config_file, indent=4, default_flow_style=False)

        except Exception as exc:
            raise ValueError(f"Error writing device configuration: {exc}") from exc


DEVICE_CONFIG = DeviceConfig(
    device={
        "name": "${{device_name}}",
        "id": "${{device_id}}",
        "workspace_id": "${{workspace_id}}",
        "config_root_dir": "DATATURE_OUTPOST_CONFIG_DIR",
    },
    authentication={
        "client_certificate": {
            "auto_renewal": {
                "days_before_expiry": 15,
                "issuer": "ManagementApi",
            },
            "certificate_file": "/home/datature/.datature/ssl/device.crt",
            "private_key_file": "/home/datature/.datature/ssl/key.pvt.pem",
        }
    },
    management_api={
        "authentication": {"kind": "ClientCertificate"},
        "endpoint": CONSTS.NEXUS_ENDPOINT,
    },
    mqtt={
        "authentication": {
            "issuing_ca": "/home/datature/.datature/ssl/issuing.ca",
            "kind": "ClientCertificate",
        },
        "endpoint": CONSTS.MQTT_ENDPOINT,
        "keep_alive_interval_seconds": 60,
        "protocol": "OutpostV1",
        "reconnect_delay_seconds": 5,
        "transport": "TLS",
    },
    statsd={"host": "localhost", "port": 8125},
    version="1.0.0",
)
