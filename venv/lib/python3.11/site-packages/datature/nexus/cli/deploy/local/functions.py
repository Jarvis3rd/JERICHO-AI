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
@Desc    :   Configuration functions for the local deployment server.
"""

# pylint: disable=W0718,R0913,R0917

import sys
from datetime import datetime
from typing import Dict, Tuple
from uuid import uuid4

import requests
from InquirerPy import inquirer
from InquirerPy.base.control import Choice

from datature.nexus.cli.config import Config
from datature.nexus.cli.deploy.local.config import DeploymentConfig, DeploymentConfigs
from datature.nexus.cli.deploy.local.server import start_server
from datature.nexus.cli.functions import get_default_datature_client
from datature.nexus.config import REQUEST_TIME_OUT_SECONDS


def get_project_credentials() -> Dict[str, str]:
    """Get project credentials from config"""
    config = Config()
    project = config.get_default_project()

    if project is None:
        print("No project found. Please set a default project.")
        sys.exit(1)

    return project


def select_artifact() -> Tuple[str, str]:
    """Prompt user to select an artifact"""
    client = get_default_datature_client()
    artifacts = client.artifacts.list()

    artifact_choices = [
        Choice(name=f"{artifact.display_name} [{artifact.id[-6:]}]", value=artifact)
        for artifact in artifacts
    ]

    artifact = inquirer.fuzzy(
        message="Select a default model/artifact for this device:",
        choices=artifact_choices,
        max_height=10,
        border=True,
    ).execute()

    return artifact.id, artifact.display_name


def get_custom_config(
    deployment_id: str,
    secret_key: str,
    project_id: str,
    project_name: str,
    artifact_id: str,
    artifact_name: str,
) -> DeploymentConfig:
    """Get configuration for custom setup"""

    runtime_choices = [
        Choice(name="CPU", value="CPU"),
        Choice(name="GPU", value="GPU"),
    ]

    runtime = inquirer.select(
        message="Do you want to use CPU or GPU?",
        choices=runtime_choices,
        default="CPU",
        border=True,
    ).execute()

    gpu_count = 0
    if runtime == "GPU":
        gpu_count = int(
            inquirer.number(
                "How many GPUs do you want to use? (0 for all GPUs):",
                default=1,
            ).execute()
        )

    port = int(
        inquirer.number(
            "Which port do you want to use for the local deployment server?",
            default=9449,
        ).execute()
    )

    allow_origins_input = inquirer.text(
        message="Enter the allowed origins (comma-separated list):",
        default="https://nexus.datature.io",
    ).execute()

    # Clean up the origins list by stripping whitespace
    allow_origins = [
        origin.strip() for origin in allow_origins_input.split(",") if origin.strip()
    ]

    print()  # newline

    return DeploymentConfig(
        deployment_id=deployment_id,
        secret_key=secret_key,
        project_id=project_id,
        project_name=project_name,
        artifact_id=artifact_id,
        artifact_name=artifact_name,
        runtime=runtime,
        devices=gpu_count if runtime == "GPU" else "auto",
        port=port,
        allowed_origins=allow_origins,
    )


def prompt_config() -> DeploymentConfig:
    """Prompt the user for the local deploy configuration"""
    deployment_id = str(uuid4())[-6:]

    project = get_project_credentials()

    setup_choices = [
        Choice(name="Simple (Default Configuration)", value="simple"),
        Choice(name="Advanced (Custom Configuration)", value="custom"),
    ]

    setup_type = inquirer.select(
        message="Select the setup type:",
        choices=setup_choices,
        default="simple",
        border=True,
    ).execute()

    artifact_id, artifact_name = select_artifact()

    if setup_type == "simple":
        deployment_config = DeploymentConfig(
            deployment_id=deployment_id,
            secret_key=project.get("project_secret", ""),
            project_id=project.get("project_id", ""),
            project_name=project.get("project_name", ""),
            artifact_id=artifact_id,
            artifact_name=artifact_name,
        )

        print()  # newline
        print("Using default configuration...")
        print(f"Project: {deployment_config.project_name}")
        print(f"Runtime: {deployment_config.runtime}")
        print(f"Devices: {deployment_config.devices}")
        print(f"Port: {deployment_config.port}")
        print(f"Allowed Origins: {deployment_config.allowed_origins}")
        print()  # newline

        return deployment_config

    return get_custom_config(
        deployment_id=deployment_id,
        secret_key=project.get("project_secret", ""),
        project_id=project.get("project_id", ""),
        project_name=project.get("project_name", ""),
        artifact_id=artifact_id,
        artifact_name=artifact_name,
    )


def start_local_deployment():
    """Start the local deployment server."""
    deployment_configs = DeploymentConfigs.read_from_file()

    deployment_config = prompt_config()

    deployment_configs.configs.append(deployment_config)
    deployment_configs.write_to_file()

    print("Starting local deployment server...")

    try:
        start_server(
            deployment_id=deployment_config.deployment_id,
            secret_key=deployment_config.secret_key,
            project_id=deployment_config.project_id,
            project_name=deployment_config.project_name,
            artifact_id=deployment_config.artifact_id,
            artifact_name=deployment_config.artifact_name,
            runtime=deployment_config.runtime,
            devices=deployment_config.devices,
            port=deployment_config.port,
            allowed_origins=deployment_config.allowed_origins,
        )

    except KeyboardInterrupt:
        print("\nKeyboard interrupt detected. Shutting down...")

    except Exception as exc:
        print(f"An error occurred: {exc}")

    finally:
        deployment_configs = DeploymentConfigs.read_from_file()
        deployment_configs.configs.remove(deployment_config)
        deployment_configs.write_to_file()


def show_logs():
    """Show the logs of the local deployment server."""
    deployment_configs = DeploymentConfigs.read_from_file()

    if not deployment_configs.configs:
        print(
            "No local deployment server found. Please start a local deployment server "
            "first by running `datature local deploy start`."
        )
        sys.exit(1)

    deployment_choices = [
        Choice(
            name=f"{deployment_config.deployment_id} [Port: {deployment_config.port}]",
            value=deployment_config,
        )
        for deployment_config in deployment_configs.configs
    ]

    deployment = inquirer.select(
        message="Select the local deployment server to show logs for:",
        choices=deployment_choices,
        border=True,
    ).execute()

    try:
        url = f"http://localhost:{deployment.port}/all-logs"
        response = requests.get(url, timeout=REQUEST_TIME_OUT_SECONDS).json()

        for log in response["logs"]:
            timestamp = datetime.fromtimestamp(log["timestamp"] / 1000).strftime(
                "%Y-%m-%d %H:%M:%S.%f"
            )
            print(f"{timestamp}\t{log['message']}")

    except requests.exceptions.RequestException as exc:
        print(f"An error occurred: {exc}")
        sys.exit(1)
