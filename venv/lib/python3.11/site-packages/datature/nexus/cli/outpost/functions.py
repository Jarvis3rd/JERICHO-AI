#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   functions.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Outpost user functions.
"""

# pylint: disable=W0718,E1120

import logging
import re
import sys

import pytz
from InquirerPy import inquirer
from InquirerPy.validator import ValidationError, Validator

import datature.nexus.cli.consts as CONSTS
import datature.nexus.cli.outpost.consts as OUTPOST_CONSTS
from datature import nexus
from datature.nexus.cli import messages
from datature.nexus.cli.config import Config
from datature.nexus.cli.outpost.common import log_errors
from datature.nexus.cli.outpost.consts import (
    OUTPOST_CONFIG_ROOT_DIR,
    RESERVED_DEVICE_TAGS,
)
from datature.nexus.cli.outpost.manager import OutpostManager
from datature.nexus.cli.outpost.types import OutpostDeviceConfig
from datature.nexus.cli.outpost.utils import check_system_specs, validate_device
from datature.nexus.error import Error

TIMEZONE_RE = r"[A-Za-z]+/[A-Za-z_]+"


class UniqueNameAndIdValidator(Validator):
    """Validator to check if the name is unique."""

    def __init__(self, outpost_device_config: OutpostDeviceConfig):
        self.outpost_device_config = outpost_device_config

    def validate(self, document) -> None:
        """Validate the input.

        :param document: Input document.
        """
        display_name = document.text.strip()
        if len(display_name) <= 0:
            raise ValidationError(
                message="Name cannot be empty.",
                cursor_position=document.cursor_position,
            )

        validation_errors = validate_device(
            self.outpost_device_config, display_name
        ).get("validationErrors", [])

        if "DisplayNameConflict" in validation_errors:
            raise ValidationError(
                message="A registered device with the same name has been found. Please enter a unique name.",
                cursor_position=document.cursor_position,
            )


def prompt_outpost_details(outpost_device_config: OutpostDeviceConfig):
    """Prompt for Outpost device details.

    :param outpost_device_config (OutpostDeviceConfig): Outpost device configuration.
    """
    print()

    outpost_device_config.name = (
        inquirer.text(
            message="Enter a descriptive name for this device:",
            mandatory=True,
            validate=UniqueNameAndIdValidator(outpost_device_config),
        )
        .execute()
        .strip()
    )

    timezone_choices = [tz for tz in pytz.all_timezones if re.match(TIMEZONE_RE, tz)]
    timezone = inquirer.fuzzy(
        message="Select your preferred timezone for metrics and logs display:",
        choices=timezone_choices,
        match_exact=True,
        default="UTC",
        exact_symbol="",
        max_height=CONSTS.INQUIRER_CHOICES_MAX_VISIBLE_ENTRIES,
        border=True,
    ).execute()

    outpost_device_config.tags["timezone"] = str(pytz.timezone(timezone).zone)

    tags = (
        inquirer.text(
            message="Enter device tags as name:value pairs, separated by commas (optional):",
            default="",
            long_instruction=(
                "Tags are key-value pairs that can be used to filter and group devices for "
                "fleet management. For example, you can tag devices with "
                "location:warehouse-a, floor:2, etc."
            ),
            validate=lambda result: all(
                tag.split(":")[0].strip() not in RESERVED_DEVICE_TAGS
                for tag in result.split(",")
            ),
            invalid_message=(
                "Please ensure that your tag list does not contain any of the reserved tags:"
                f" {', '.join(RESERVED_DEVICE_TAGS)}"
            ),
        )
        .execute()
        .split(",")
    )

    for tag in tags:
        if ":" in tag:
            tag_name, tag_value = tag.split(":")
            outpost_device_config.tags[tag_name.strip()] = tag_value.strip()

    outpost_device_config.write_to_file()


def create_configuration():
    """Create new Outpost configuration."""
    OUTPOST_CONFIG_ROOT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        outpost_device_config = OutpostDeviceConfig.read_from_file()

        logging.basicConfig(level=logging.CRITICAL)
        cli_config = Config()
        outpost_device_config.device_credentials.secret_key = (
            cli_config.get_default_project().get("project_secret", "")
        )
        outpost_device_config.device_credentials.default_project_id = (
            cli_config.get_default_project().get("project_id", "")
        )
        outpost_device_config.device_credentials.workspace_id = (
            nexus.Client(outpost_device_config.device_credentials.secret_key)
            .get_info()
            .id.strip("ws_")
        )

        logging.basicConfig(level=logging.INFO)
    except Error as exc:
        if "Workspace ID / Secret Key combination" in exc.message:
            outpost_device_config.device_credentials.secret_key = ""
            outpost_device_config.device_credentials.workspace_id = ""
        elif "No access rights" in exc.message:
            print(messages.AUTHENTICATION_FAILED_MESSAGE)
            sys.exit(1)
        else:
            print(exc)
            sys.exit(1)

    outpost_device_config.write_to_file()

    OutpostManager().create_configuration()


def install_outpost():
    """Install Outpost on device."""
    OUTPOST_CONFIG_ROOT_DIR.mkdir(parents=True, exist_ok=True)

    if not OUTPOST_CONSTS.OUTPOST_CONFIG_FILE_PATH.exists():
        OUTPOST_CONSTS.OUTPOST_CONFIG_FILE_PATH.touch()

    try:
        outpost_device_config = OutpostDeviceConfig.read_from_file()

        logging.basicConfig(level=logging.CRITICAL)
        cli_config = Config()
        outpost_device_config.device_credentials.secret_key = (
            cli_config.get_default_project().get("project_secret", "")
        )
        outpost_device_config.device_credentials.default_project_id = (
            cli_config.get_default_project().get("project_id", "").strip("proj_")
        )
        outpost_device_config.device_credentials.workspace_id = (
            nexus.Client(outpost_device_config.device_credentials.secret_key)
            .get_info()
            .id.strip("ws_")
        )

        logging.basicConfig(level=logging.INFO)
    except Error as exc:
        if "Workspace ID / Secret Key combination" in exc.message:
            outpost_device_config.device_credentials.secret_key = ""
            outpost_device_config.device_credentials.workspace_id = ""
        elif "No access rights" in exc.message:
            print(messages.AUTHENTICATION_FAILED_MESSAGE)
            sys.exit(1)
        else:
            print(exc)
            sys.exit(1)

    try:
        check_system_specs(outpost_device_config)

        print()
        license_agreed = inquirer.confirm(
            message=(
                "Please confirm that you have reviewed and accepted the "
                "Datature Outpost License Agreement.\n\n"
                "By proceeding with installation, you acknowledge compliance "
                "with the terms and conditions.\n"
                "Full agreement available at: https://datature.io/legal/outpost/license.txt"
            ),
            default=False,
        ).execute()

        if not license_agreed:
            sys.exit(0)

        prompt_outpost_details(outpost_device_config)
    except KeyboardInterrupt:
        sys.exit(0)
    except Error as exc:
        print(exc)
        sys.exit(1)
    except Exception as exc:
        print(exc)
        sys.exit(1)

    OutpostManager().install()


def uninstall_outpost():
    """Uninstall Outpost from device."""
    try:
        outpost_device_config = OutpostDeviceConfig.read_from_file()
        if not outpost_device_config.id:
            print(messages.NO_OUTPOST_DEVICE_REGISTERED_MESSAGE)
            sys.exit(1)

        continue_uninstall = inquirer.confirm(
            message="Please confirm that you want to uninstall Datature Outpost from this device:",
            default=False,
        ).execute()

        if not continue_uninstall:
            sys.exit(0)

        OutpostManager().uninstall()
    except KeyboardInterrupt:
        sys.exit(0)
    except (Error, Exception):
        log_errors()
        sys.exit(1)


def pause_outpost():
    """Pause Outpost manually on device."""
    try:
        outpost_device_config = OutpostDeviceConfig.read_from_file()
        if not outpost_device_config.id:
            print(messages.NO_OUTPOST_DEVICE_REGISTERED_MESSAGE)
            sys.exit(1)

        OutpostManager().pause()

    except KeyboardInterrupt:
        sys.exit(1)
    except (Error, Exception):
        log_errors()
        sys.exit(1)


def resume_outpost():
    """Resume Outpost manually on device."""
    try:
        outpost_device_config = OutpostDeviceConfig.read_from_file()
        if not outpost_device_config.id:
            print(messages.NO_OUTPOST_DEVICE_REGISTERED_MESSAGE)
            sys.exit(1)

        OutpostManager().resume()

    except KeyboardInterrupt:
        sys.exit(1)
    except (Error, Exception):
        log_errors()
        sys.exit(1)


def display_outpost_status():
    """Displays Outpost device status."""

    try:
        outpost_device_config = OutpostDeviceConfig.read_from_file()
        if not outpost_device_config.id:
            print(messages.NO_OUTPOST_DEVICE_REGISTERED_MESSAGE)
            sys.exit(1)

        OutpostManager().status()

    except KeyboardInterrupt:
        sys.exit(1)
    except (Error, Exception):
        log_errors()
        sys.exit(1)
