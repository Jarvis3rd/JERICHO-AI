#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   consts.py
@Author  :   Wei Loon Cheng, Kai Xuan Lee
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Custom runner constants.
"""

import os
from pathlib import Path

NEXUS_ENDPOINT = os.getenv("DATATURE_API_BASE_URL", "https://api.datature.io")
DOCS_ENV_SETUP_URL = (
    "https://developers.datature.io/docs/self-hosted-gpu-runner-environment-setup"
)
DOCS_ERROR_HANDLING_URL = (
    "https://developers.datature.io/docs/self-hosted-gpu-runner-error-handling"
)
SUPPORT_EMAIL = "support@datature.io"

APT_PACKAGE_LIST = ["curl", "jq"]
MICROK8S_ADDONS_LIST = ["dns", "hostpath-storage", "nvidia", "registry"]

RUNNER_INIT_ROOT_DIR = Path.home() / ".config/datature"
RUNNER_LOG_DIR = Path("/var/log/datature")
ERROR_LOG_DIR = Path.home() / ".logs"
RUNNER_CONFIG_FILE_PATH = RUNNER_INIT_ROOT_DIR / "datature_runner_config"
K8S_CONFIG_DIR = Path.home() / ".kube"
K8S_CONFIG_FILE_PATH = K8S_CONFIG_DIR / "config"

MIN_NVIDIA_DRIVER_VERSION = 515
MAX_NVIDIA_DRIVER_VERSION = 550
MINIMUM_RAM_BYTES = 8 * 1024**3
MINIMUM_STORAGE_BYTES = 754 * 1024**2

DOCKER_REGISTRY_SECRET = "datature-regcred"

RUNNER_DEPLOYMENT_NAME = "datature-runner"
RUNNER_DEPLOYMENT_CONFIG_NAME = "datature-runner-cfg"
RUNNER_INITIALIZATION_NUM_CHECKS = 100
RUNNER_INITIALIZATION_SLEEP_SECONDS = 6
RUNNER_WAIT_RESPONSE_NUM_CHECKS = 180

DELETE_JOB_LABEL_SELECTORS = ["app=datature-trainer", "app=datature-image-pull"]
RUNNER_WAIT_DELETE_RUNS_SECONDS = 5
RUNNER_WAIT_DETECT_DELETED_JOBS_SECONDS = 45
