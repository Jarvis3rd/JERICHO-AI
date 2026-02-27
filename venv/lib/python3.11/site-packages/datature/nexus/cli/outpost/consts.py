#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   consts.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Outpost consts.
"""

import os
from pathlib import Path

NEXUS_ENDPOINT = os.getenv("DATATURE_API_BASE_URL", "https://api.datature.io")
MQTT_ENDPOINT = os.getenv(
    "DATATURE_OUTPOST_MQTT_ENDPOINT", "mqtts://mqtt.outpost.datature.io:8883"
)
DOCS_ENV_SETUP_URL = "https://developers.datature.io/docs/outpost-setup"
DOCS_ERROR_HANDLING_URL = "https://developers.datature.io/docs/outpost-error-handling"
SUPPORT_EMAIL = "support@datature.io"

OUTPOST_CONFIG_ROOT_DIR = Path.home() / ".config/datature"
OUTPOST_CONFIG_FILE_PATH = OUTPOST_CONFIG_ROOT_DIR / "datature_outpost_device_config"
OUTPOST_ERROR_LOG_DIR = Path.home() / ".logs"
OUTPOST_ROOT_DIR = Path.home() / ".datature/outpost"

MINIMUM_RAM_BYTES = 4 * 1024**3
MINIMUM_STORAGE_BYTES = 2 * 1024**3

RESERVED_DEVICE_TAGS = ["group", "timezone"]
