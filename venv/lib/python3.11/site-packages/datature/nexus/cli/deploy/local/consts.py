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
@Desc    :   Constants for local deployment
"""

from pathlib import Path

# Server Configuration
DEPLOY_CONFIG_ROOT_DIR = Path.home() / ".config/datature"
DEPLOY_CONFIGS_FILE_PATH = DEPLOY_CONFIG_ROOT_DIR / "datature_local_deploy_configs"
DEFAULT_PORT = 9449

DEFAULT_ALLOWED_ORIGINS = ["https://nexus.datature.io"]
DEFAULT_ALLOWED_METHODS = ["GET", "POST", "OPTIONS"]
DEFAULT_MAX_AGE = 3600

DEFAULT_RUNTIME = "CPU"
DEFAULT_DEVICES = "auto"

# Model Configuration
DEFAULT_MODEL_DIR = Path.home() / ".datature" / "models"
DEFAULT_TIMEOUT = 120

# Runtime Configuration
RUNTIME_OPTIONS = {
    "CPU": "CPUExecutionProvider",
    "GPU": "CUDAExecutionProvider",
}
