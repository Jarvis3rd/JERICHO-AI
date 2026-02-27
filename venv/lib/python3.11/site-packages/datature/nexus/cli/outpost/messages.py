#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   messages.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Outpost information messages.
"""

from datature.nexus.cli.outpost.consts import DOCS_ERROR_HANDLING_URL, SUPPORT_EMAIL

INSTALL_PIP_PACKAGE_ERROR_MESSAGE = (
    "Failed to install {package_name}.\n"
    "You may need to install manually by running `pip install {package_name}` in your environment.\n"
    "Also ensure that your pip version is up-to-date by running `pip install --upgrade pip`."
)

OUTPOST_UNKNOWN_ERROR_MESSAGE = (
    "Error: An unknown error occurred while processing Datature Outpost. Full traceback logged to {}.\n"
    f"For more information, visit: {DOCS_ERROR_HANDLING_URL} or contact support: {SUPPORT_EMAIL}"
)
OUTPOST_TRACEBACK_MESSAGE = "Full traceback logged to {}."


SERVER_CONNECTION_ERROR_MESSAGE = (
    "Error: Failed to connect to server. Ensure you have an active internet connection.\n"
    f"For more information, visit: {DOCS_ERROR_HANDLING_URL} or contact support: {SUPPORT_EMAIL}"
)
FEATURE_NOT_AVAILABLE_ERROR_MESSAGE = (
    "Error: Your workspace does not have access to this feature.\n"
    f"For more information, visit: {DOCS_ERROR_HANDLING_URL} or contact support: {SUPPORT_EMAIL}"
)
INSUFFICIENT_DEVICE_QUOTA_ERROR_MESSAGE = (
    "Error: Your workspace has reached the maximum number of devices.\n"
    "Please remove any unused devices from your workspace.\n"
    f"For more information on quotas, visit: {DOCS_ERROR_HANDLING_URL} "
    f"or contact support if you wish to increase your quotas: {SUPPORT_EMAIL}"
)
SERVER_FORBIDDEN_ERROR_MESSAGE = (
    "Error: Failed to ping server. "
    "The Workspace ID / Secret Key combination has been invalidated. "
    "A user in your workspace may have generated a new key.\n"
    "Please obtain the new key, or regenerate one for your workspace on Nexus: "
    "https://nexus.datature.io/workspace/{}/settings#key\n"
    f"For more information, visit: {DOCS_ERROR_HANDLING_URL} or contact support: {SUPPORT_EMAIL}"
)
SERVER_UNKNOWN_ERROR_MESSAGE = (
    "{}\n"
    "Error: Failed to ping server.\n"
    f"For more details, visit: {DOCS_ERROR_HANDLING_URL} or contact support: {SUPPORT_EMAIL}"
)

MISSING_CONFIGURATION_FILES_ERROR_MESSAGE = (
    "Error: Missing configuration files detected. Your provided folder should contain the following files: {}\n"
    "Please run `datature outpost configure` to create the configuration files.\n"
    f"For more information, visit: {DOCS_ERROR_HANDLING_URL} or contact support: {SUPPORT_EMAIL}"
)
