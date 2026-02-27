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
@Desc    :   Outpost runtime configuration functions.
"""

# pylint: disable=R0914

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import msgspec
import requests
from colorama import Fore
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.validator import EmptyInputValidator

import datature.nexus.cli.consts as CONSTS
from datature.nexus import Client
from datature.nexus.cli import messages
from datature.nexus.cli.outpost import consts as OUTPOST_CONSTS
from datature.nexus.cli.outpost import messages as MESSAGES
from datature.nexus.cli.outpost.types import (
    OutpostDeviceConfig,
    OutpostDeviceConfiguration,
    OutpostDeviceRuntime,
)
from datature.nexus.config import REQUEST_TIME_OUT_SECONDS
from datature.nexus.error import Error

CONFIGURATION_FILE_INCLUSIONS = [
    "outpost-active-learning.yml",
    "outpost-logging.yml",
    "outpost-metrics.yml",
    "outpost-prediction.yml",
    "runtime-manager.yml",
]


def select_default_artifact(outpost_device_config: OutpostDeviceConfig) -> None:
    """Select default artifact for the configuration."""
    client = Client(
        secret_key=outpost_device_config.device_credentials.secret_key,
        endpoint=OUTPOST_CONSTS.NEXUS_ENDPOINT,
    )
    workspace_artifacts = client.list_artifacts()

    if not workspace_artifacts:
        print(messages.NO_ARTIFACTS_MESSAGE)
        sys.exit(1)

    artifact_choices = [
        Choice(name=f"{artifact.display_name} [{artifact.id[-6:]}]", value=artifact)
        for artifact in workspace_artifacts
    ]

    artifact = inquirer.fuzzy(
        message="Select a default artifact for this device:",
        choices=artifact_choices,
        max_height=CONSTS.INQUIRER_CHOICES_MAX_VISIBLE_ENTRIES,
        border=True,
    ).execute()

    outpost_device_config.default_artifact_id = artifact.id
    outpost_device_config.device_credentials.default_project_id = artifact.project_id


def get_sample_configuration(
    outpost_device_config: OutpostDeviceConfig,
) -> Dict[str, Any]:
    """Get sample configuration from the server."""
    response = requests.get(
        (
            f"{OUTPOST_CONSTS.NEXUS_ENDPOINT}/workspaces/ws_"
            f"{outpost_device_config.device_credentials.workspace_id}/metadata/outpost"
        ),
        headers={
            "Secret-Key": outpost_device_config.device_credentials.secret_key,
            "Content-Type": "application/json",
        },
        timeout=REQUEST_TIME_OUT_SECONDS,
    )
    return response.json()["sampleSpec"]


def create_configuration(
    outpost_device_config: OutpostDeviceConfig,
) -> OutpostDeviceConfiguration:
    """Create a new Outpost configuration."""
    configuration_id = str(uuid4()).replace("-", "")[-15:]

    configuration_name = (
        inquirer.text(
            message="Enter a descriptive name for this configuration:",
            mandatory=True,
            validate=EmptyInputValidator(),
        )
        .execute()
        .strip()
    )

    configuration_choices = [
        Choice(name="default", value="default"),
        Choice(name="Custom", value="custom"),
    ]
    configuration_spec_type = inquirer.fuzzy(
        message="Specify which configuration spec you want to use:",
        choices=configuration_choices,
        mandatory=True,
        max_height=CONSTS.INQUIRER_CHOICES_MAX_VISIBLE_ENTRIES,
        border=True,
    ).execute()

    if configuration_spec_type == "default":
        configuration_spec = get_sample_configuration(outpost_device_config)

    else:
        configuration_version = (
            inquirer.text(
                message="Enter the configuration version:",
                default="1.0.0",
                validate=EmptyInputValidator(),
            )
            .execute()
            .strip()
        )

        configuration_folder = (
            inquirer.filepath(
                message="Enter the path to the folder containing the configuration files:",
                validate=EmptyInputValidator(),
            )
            .execute()
            .strip()
        )

        configuration_folder = Path(os.path.expanduser(configuration_folder)).resolve()
        configuration_data = {}

        for file in configuration_folder.iterdir():
            if file.is_file() and file.name in CONFIGURATION_FILE_INCLUSIONS:
                with open(file, "r", encoding="utf-8") as config_file:
                    configuration_data[file.name] = config_file.read()

        if len(configuration_data) != len(CONFIGURATION_FILE_INCLUSIONS):
            print(
                MESSAGES.MISSING_CONFIGURATION_FILES_ERROR_MESSAGE.format(
                    ", ".join(CONFIGURATION_FILE_INCLUSIONS)
                )
            )
            sys.exit(1)

        configuration_spec = {
            "kind": "OutpostRuntime",
            "configVersion": configuration_version,
            "configData": configuration_data,
        }

    select_default_artifact(outpost_device_config)

    try:
        config_data = {
            "id": f"outpostconfig_{configuration_id}",
            "name": configuration_name,
            "spec": {
                "kind": configuration_spec["kind"],
                "configVersion": configuration_spec["configVersion"],
                "configData": configuration_spec["configData"],
                "configVariables": {
                    "project_id": {
                        "kind": "String",
                        "role": "ProjectId",
                        "default": outpost_device_config.device_credentials.default_project_id,
                    },
                    "artifact_id": {
                        "kind": "String",
                        "role": "ArtifactId",
                        "default": outpost_device_config.default_artifact_id,
                    },
                },
            },
        }

        response = requests.post(
            (
                f"{OUTPOST_CONSTS.NEXUS_ENDPOINT}/workspaces/ws_"
                f"{outpost_device_config.device_credentials.workspace_id}/outpost/configurations"
            ),
            headers={
                "Secret-Key": outpost_device_config.device_credentials.secret_key,
                "Content-Type": "application/json",
            },
            data=json.dumps(config_data),
            timeout=REQUEST_TIME_OUT_SECONDS,
        )
        response.raise_for_status()

    except requests.exceptions.ConnectionError as exc:
        raise Error(MESSAGES.SERVER_CONNECTION_ERROR_MESSAGE) from exc

    except requests.exceptions.HTTPError as exc:
        if response.status_code == 400:
            raise Error(MESSAGES.INSUFFICIENT_DEVICE_QUOTA_ERROR_MESSAGE) from exc

        if response.status_code == 402:
            raise Error(MESSAGES.FEATURE_NOT_AVAILABLE_ERROR_MESSAGE) from exc

        if response.status_code == 403:
            raise Error(
                MESSAGES.SERVER_FORBIDDEN_ERROR_MESSAGE.format(
                    outpost_device_config.device_credentials.workspace_id
                )
            ) from exc

        if response.status_code != 405:
            raise Error(
                MESSAGES.SERVER_UNKNOWN_ERROR_MESSAGE.format(response.text)
            ) from exc

    outpost_configuration = msgspec.json.decode(
        json.dumps(response.json()), type=OutpostDeviceConfiguration
    )

    print(f"{Fore.GREEN}✓{Fore.RESET} Configuration created successfully.")
    print(f"\n\tConfiguration ID: {outpost_configuration.id}")
    print(f"\tConfiguration Name: {outpost_configuration.name}")
    print(f"\tConfiguration Version: {outpost_configuration.spec.config_version}")
    print("\tConfiguration Files:")
    for file_name in outpost_configuration.spec.config_data.keys():
        print(f"\t\t{file_name}")
    print()

    return outpost_configuration


def list_configurations(
    outpost_device_config: OutpostDeviceConfig,
) -> List[OutpostDeviceConfiguration]:
    """List all Outpost configurations."""
    try:
        response = requests.get(
            (
                f"{OUTPOST_CONSTS.NEXUS_ENDPOINT}/workspaces/ws_"
                f"{outpost_device_config.device_credentials.workspace_id}/outpost/configurations"
            ),
            headers={
                "Secret-Key": outpost_device_config.device_credentials.secret_key,
                "Content-Type": "application/json",
            },
            timeout=REQUEST_TIME_OUT_SECONDS,
        )
        response.raise_for_status()

    except requests.exceptions.ConnectionError as exc:
        raise Error(MESSAGES.SERVER_CONNECTION_ERROR_MESSAGE) from exc

    except requests.exceptions.HTTPError as exc:
        if response.status_code == 400:
            raise Error(MESSAGES.INSUFFICIENT_DEVICE_QUOTA_ERROR_MESSAGE) from exc

        if response.status_code == 402:
            raise Error(MESSAGES.FEATURE_NOT_AVAILABLE_ERROR_MESSAGE) from exc

        if response.status_code == 403:
            raise Error(
                MESSAGES.SERVER_FORBIDDEN_ERROR_MESSAGE.format(
                    outpost_device_config.device_credentials.workspace_id
                )
            ) from exc

        if response.status_code != 405:
            raise Error(
                MESSAGES.SERVER_UNKNOWN_ERROR_MESSAGE.format(response.text)
            ) from exc

    outpost_configurations = msgspec.json.decode(
        json.dumps(response.json()["data"]), type=List[OutpostDeviceConfiguration]
    )

    return outpost_configurations


def prompt_for_configuration_version(
    outpost_device_config: OutpostDeviceConfig,
) -> None:
    """Prompt for configuration version."""
    configurations = list_configurations(outpost_device_config)

    has_existing_configurations = len(configurations) > 0

    configuration_choices = [
        (
            Choice(name="Select an Existing Configuration", value="existing")
            if has_existing_configurations
            else None
        ),
        Choice(name="Register a New Configuration", value="new"),
    ]
    configuration_choices = [choice for choice in configuration_choices if choice]

    configuration_type = inquirer.select(
        message="Select deployment configuration type:",
        choices=configuration_choices,
        default="new" if not has_existing_configurations else "existing",
        border=True,
    ).execute()

    if configuration_type == "new":
        configuration = create_configuration(outpost_device_config)

    else:
        configuration_choices = [
            Choice(
                name=f"{configuration.name} (v{configuration.spec.config_version})",
                value=configuration,
            )
            for configuration in sorted(
                configurations, key=lambda c: c.create_date, reverse=True
            )
        ]

        configuration = inquirer.fuzzy(
            message="Select a configuration to deploy:",
            choices=configuration_choices,
            max_height=CONSTS.INQUIRER_CHOICES_MAX_VISIBLE_ENTRIES,
            border=True,
        ).execute()

    outpost_device_config.configuration = configuration
    outpost_device_config.write_to_file()


def prompt_for_runtime_config(outpost_device_config: OutpostDeviceConfig) -> None:
    """Prompt for runtime configuration."""
    runtimes_response = requests.get(
        (
            f"{OUTPOST_CONSTS.NEXUS_ENDPOINT}/workspaces/ws_"
            f"{outpost_device_config.device_credentials.workspace_id}"
            f"/outpost/runtimes"
        ),
        headers={
            "Secret-Key": outpost_device_config.device_credentials.secret_key,
            "Content-Type": "application/json",
        },
        timeout=REQUEST_TIME_OUT_SECONDS,
    )

    available_runtimes = msgspec.json.decode(
        json.dumps(runtimes_response.json()["data"]), type=List[OutpostDeviceRuntime]
    )

    sorted_runtimes = sorted(
        available_runtimes, key=lambda r: r.create_date, reverse=True
    )

    runtime_choices = []
    if sorted_runtimes:
        runtime_choices.append(
            Choice(
                name=f"latest (v{str(sorted_runtimes[0].version)}, recommended)",
                value=sorted_runtimes[0],
            )
        )
        runtime_choices.extend(
            [
                Choice(
                    name=f"v{str(runtime.version)}",
                    value=runtime,
                )
                for runtime in sorted_runtimes[1:]
            ]
        )

    runtime = inquirer.fuzzy(
        message="Select a runtime version to deploy:",
        choices=runtime_choices,
        default="latest",
        max_height=CONSTS.INQUIRER_CHOICES_MAX_VISIBLE_ENTRIES,
        border=True,
    ).execute()

    runtime_dir = inquirer.filepath(
        message="Specify destination folder for runtime files:",
        long_instruction=(
            "The system will create a `/runtime` subfolder at your specified location. "
            "If you leave this field empty, files will be installed in the default location:"
            f" `{OUTPOST_CONSTS.OUTPOST_ROOT_DIR}`."
        ),
        mandatory=True,
        only_directories=True,
        default=str(OUTPOST_CONSTS.OUTPOST_ROOT_DIR),
        validate=lambda result: len(result) > 0,
    ).execute()

    # convert to absolute path
    runtime_dir = Path(os.path.expanduser(runtime_dir)).resolve()

    outpost_device_config.runtime = runtime
    outpost_device_config.runtime_dir = str(runtime_dir)
    outpost_device_config.write_to_file()


def prompt_for_python_version(outpost_device_config: OutpostDeviceConfig) -> None:
    """Prompt for Python version selection."""
    python_choices = [
        Choice(name="3.10", value="python3.10"),
        Choice(name="3.11", value="python3.11"),
        Choice(name="3.12", value="python3.12"),
    ]

    python_version = inquirer.select(
        message="Select Python version for runtime:",
        choices=python_choices,
        default="python3.10",
        border=True,
    ).execute()

    outpost_device_config.python_version = python_version
    outpost_device_config.write_to_file()
