#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   utils.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Outpost utility functions.
"""

# pylint: disable=W0718

import json
import os
import queue
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from uuid import uuid4

import msgspec
import requests
import yaml
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from InquirerPy import inquirer

from datature.nexus.cli.outpost import consts as CONSTS
from datature.nexus.cli.outpost import messages as MESSAGES
from datature.nexus.cli.outpost.types import (
    DeviceStatusMessage,
    DeviceStatusProperties,
    MetadataSpec,
    OutpostDeviceConfig,
    OutpostDeviceConfiguration,
    RegistrationStatus,
    RuntimeStatus,
    UpdaterStatus,
)
from datature.nexus.cli.outpost.utils import (
    DEVICE_CONFIG,
    interpolate_config_variables,
    start_spinner,
)
from datature.nexus.config import REQUEST_TIME_OUT_SECONDS
from datature.nexus.error import Error

RUNTIME_CREDENTIALS_DIR = Path("/home/datature/.datature/ssl")
DEFAULT_CREDENTIALS_DIR = Path.home() / ".datature" / "ssl"


def validate_device(
    outpost_device_config: OutpostDeviceConfig, display_name: str
) -> Dict[str, Any]:
    """Validate whether the device name has been taken or not."""
    response = requests.post(
        (
            f"{CONSTS.NEXUS_ENDPOINT}/workspaces/ws_"
            f"{outpost_device_config.device_credentials.workspace_id}"
            f"/outpost/deviceValidation"
        ),
        headers={
            "Secret-Key": outpost_device_config.device_credentials.secret_key,
            "Content-Type": "application/json",
        },
        data=json.dumps({"id": outpost_device_config.id, "displayName": display_name}),
        timeout=REQUEST_TIME_OUT_SECONDS,
    )

    return response.json()


def list_devices(outpost_device_config: OutpostDeviceConfig) -> Dict[str, Any]:
    """List all devices in the workspace."""
    try:
        response = requests.get(
            (
                f"{CONSTS.NEXUS_ENDPOINT}/workspaces/ws_"
                f"{outpost_device_config.device_credentials.workspace_id}"
                f"/outpost/devices?limit=1000"
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

        raise Error(
            MESSAGES.SERVER_UNKNOWN_ERROR_MESSAGE.format(response.text)
        ) from exc

    return response.json()


def get_device(outpost_device_config: OutpostDeviceConfig) -> Dict[str, Any]:
    """Get the current device registration information."""
    try:
        response = requests.get(
            (
                f"{CONSTS.NEXUS_ENDPOINT}/workspaces/ws_"
                f"{outpost_device_config.device_credentials.workspace_id}"
                f"/outpost/devices/{outpost_device_config.id}"
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

        raise Error(
            MESSAGES.SERVER_UNKNOWN_ERROR_MESSAGE.format(response.text)
        ) from exc

    return response.json()


def patch_device(
    outpost_device_config: OutpostDeviceConfig, data: Dict[str, Any]
) -> None:
    """Patch the device registration information."""
    if "id" in data:
        del data["id"]

    try:
        response = requests.patch(
            (
                f"{CONSTS.NEXUS_ENDPOINT}/workspaces/ws_"
                f"{outpost_device_config.device_credentials.workspace_id}"
                f"/outpost/devices/{outpost_device_config.id}"
            ),
            headers={
                "Secret-Key": outpost_device_config.device_credentials.secret_key,
                "Content-Type": "application/json",
            },
            data=json.dumps(data),
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

        raise Error(
            MESSAGES.SERVER_UNKNOWN_ERROR_MESSAGE.format(response.text)
        ) from exc


def get_runtime_status_message(outpost_device_config: OutpostDeviceConfig) -> str:
    """Get the status message of the Outpost runtime."""
    return get_device(outpost_device_config).get("status", {}).get("message")


def register_device(outpost_device_config: OutpostDeviceConfig) -> None:
    """Register the current device with the server."""
    registration_data = {
        "id": outpost_device_config.id,
        "name": outpost_device_config.name,
        "spec": {
            "registrationStatus": RegistrationStatus.REGISTERED.value,
            "tags": dict(outpost_device_config.tags),
            "deviceInfo": msgspec.to_builtins(outpost_device_config.device_info),
            "runtime": {
                "kind": "Outpost",
                "version": outpost_device_config.runtime.id,
                "configuration": outpost_device_config.configuration.id,
            },
            "revisionId": str(outpost_device_config.runtime.version),
            "collectedMetrics": [],
        },
    }

    try:
        response = requests.post(
            (
                f"{CONSTS.NEXUS_ENDPOINT}/workspaces/ws_"
                f"{outpost_device_config.device_credentials.workspace_id}/outpost/devices"
            ),
            headers={
                "Secret-Key": outpost_device_config.device_credentials.secret_key,
                "Content-Type": "application/json",
            },
            data=json.dumps(registration_data),
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

        if response.status_code == 409:
            inquirer.confirm(
                message=(
                    f"A device with ID {outpost_device_config.id} "
                    "has already been registered. Do you want to overwrite it?"
                ),
                default=False,
            ).execute()
            patch_device(outpost_device_config, registration_data)
            return

        raise Error(
            MESSAGES.SERVER_UNKNOWN_ERROR_MESSAGE.format(response.text)
        ) from exc

    device_response = response.json()

    device_status = device_response["status"]

    if device_status["message"] != DeviceStatusMessage.REGISTERING.value:
        raise Error("Error: Device registration failed. Please try again.")

    outpost_device_config.uid = device_response["uid"]
    outpost_device_config.metadata_generation = device_response["metadataGeneration"]
    outpost_device_config.write_to_file()


def generate_pem_keys() -> Tuple[bytes, bytes]:
    """Generate a 3072-bit RSA key pair and save them to PEM files."""
    # Generate a 3072-bit RSA key
    private_key = rsa.generate_private_key(
        public_exponent=65537,  # Standard value for RSA
        key_size=3072,
    )

    # Serialize the private key to PEM format
    pem_private_key = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    Path(DEFAULT_CREDENTIALS_DIR).mkdir(parents=True, exist_ok=True)

    private_key_path = DEFAULT_CREDENTIALS_DIR / "key.pvt.pem"
    with open(private_key_path, "wb") as f:
        f.write(pem_private_key)

    # Extract the public key
    public_key = private_key.public_key()

    # Serialize the public key to PEM format
    pem_public_key = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    public_key_path = DEFAULT_CREDENTIALS_DIR / "key.pub.pem"
    with open(public_key_path, "wb") as f:
        f.write(pem_public_key)

    return pem_private_key, pem_public_key


@start_spinner
def setup_outpost_credentials(
    outpost_device_config: OutpostDeviceConfig, message_queue: queue.Queue
):
    """Make a certificate signing request to the server."""
    message_queue.put("Generating device certificate...")

    certificate_id = f"outpostdevicecertificate_{str(uuid4()).replace('-', '')[-11:]}"
    _, pem_public_key = generate_pem_keys()

    certificate_data = {
        "id": certificate_id,
        "spec": {
            "certificateSigningRequest": {
                "kind": "PublicKey",
                "key": pem_public_key.decode("utf-8").strip(),
            }
        },
    }
    try:
        response = requests.post(
            (
                f"{CONSTS.NEXUS_ENDPOINT}/workspaces/ws_"
                f"{outpost_device_config.device_credentials.workspace_id}"
                f"/outpost/devices/{outpost_device_config.id}/certificates"
            ),
            headers={
                "Secret-Key": outpost_device_config.device_credentials.secret_key,
                "Content-Type": "application/json",
            },
            data=json.dumps(certificate_data),
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

    certificate_status = response.json()["status"]

    if certificate_status["message"] != "Issued":
        raise Error("Error: Certificate signing request failed. Please try again.")

    certificate_path = DEFAULT_CREDENTIALS_DIR / "device.crt"
    with open(certificate_path, "w", encoding="utf-8") as certificate_file:
        certificate_file.write(certificate_status["pemCertificate"])

    os.chmod(
        certificate_path,
        stat.S_IRUSR  # Owner read
        | stat.S_IWUSR  # Owner write
        | stat.S_IRGRP  # Group read
        | stat.S_IROTH,  # Others read
    )

    validate_certificate(outpost_device_config)

    return (
        f"Certificate signing request successful. "
        f"Device certificate saved to {certificate_path}."
    )


@start_spinner
def get_outpost_device_config_files(
    outpost_device_config: OutpostDeviceConfig, message_queue: queue.Queue
) -> str:
    """Download the Outpost configuration files."""
    message_queue.put("Downloading Outpost configuration files...")

    try:
        response = requests.get(
            (
                f"{CONSTS.NEXUS_ENDPOINT}/"
                f"workspaces/ws_{outpost_device_config.device_credentials.workspace_id}"
                f"/outpost/configurations/{outpost_device_config.configuration.id}"
            ),
            headers={
                "Secret-Key": outpost_device_config.device_credentials.secret_key,
                "Content-Type": "application/json",
            },
            verify=True,
            timeout=(60, 3600),
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

    try:
        config_dir = Path(outpost_device_config.runtime_dir) / "runtime" / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        raise Error(f"Error creating config directory: {str(exc)}") from exc

    config_variables = {
        name: entry.default
        for name, entry in outpost_configuration.spec.config_variables.items()
    }

    for (
        config_filename,
        config_file_contents,
    ) in outpost_configuration.spec.config_data.items():
        config_file_contents = interpolate_config_variables(
            config_file_contents, config_variables
        )

        config_file_path = config_dir / config_filename
        with open(config_file_path, "w", encoding="utf-8") as config_file:
            config_file.write(config_file_contents)

    generate_device_config(outpost_device_config, config_dir)
    generate_metadata_spec(outpost_device_config, config_variables, config_dir)
    generate_device_info(outpost_device_config, config_dir)

    return "Outpost configuration files successfully downloaded."


def generate_device_config(
    outpost_device_config: OutpostDeviceConfig, config_dir: Path
) -> None:
    """Generate the device configuration file."""
    config_file_path = config_dir / "device-config.yml"

    variables = {
        "device_id": outpost_device_config.id,
        "device_name": outpost_device_config.name,
        "workspace_id": outpost_device_config.device_credentials.workspace_id,
    }

    device_config_template_str = msgspec.yaml.encode(DEVICE_CONFIG).decode("utf-8")
    device_config_str = interpolate_config_variables(
        device_config_template_str, variables
    )

    with open(config_file_path, "w", encoding="utf-8") as config_file:
        config_file.write(device_config_str)


@start_spinner
def get_outpost_runtime_files(
    outpost_device_config: OutpostDeviceConfig, message_queue: queue.Queue
) -> None:
    """Download the Outpost runtime files."""
    message_queue.put("Downloading Outpost runtime files...")

    signed_url = outpost_device_config.runtime.link.url

    download_response = requests.get(
        signed_url,
        headers={
            "Secret-Key": outpost_device_config.device_credentials.secret_key,
            "Content-Type": "application/json",
        },
        timeout=REQUEST_TIME_OUT_SECONDS,
        stream=True,
    )

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        for data in download_response.iter_content(chunk_size=1024):
            temp_file.write(data)

    try:
        Path(outpost_device_config.runtime_dir).mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        raise Error(f"Error creating runtime directory: {str(exc)}") from exc

    with zipfile.ZipFile(temp_file.name, "r") as zip_ref:
        zip_ref.extractall(outpost_device_config.runtime_dir)

    return "Outpost runtime files successfully downloaded."


def generate_metadata_spec(
    outpost_device_config: OutpostDeviceConfig,
    config_variables: Dict[str, Any],
    config_dir: Path,
) -> None:
    """Generate the metadata specification file."""
    metadata_spec = MetadataSpec(
        device_uid=outpost_device_config.uid,
        tags=outpost_device_config.tags,
        metadata_generation=outpost_device_config.metadata_generation,
        revision_id=str(outpost_device_config.runtime.version),
        configuration=outpost_device_config.configuration,
        runtime=outpost_device_config.runtime,
        runtime_variables=config_variables,
    )

    metadata_spec_dict = msgspec.to_builtins(metadata_spec)

    with open(config_dir / "metadata-spec.yml", "w", encoding="utf-8") as config_file:
        yaml.dump(metadata_spec_dict, config_file, indent=4, default_flow_style=False)


def generate_device_info(
    outpost_device_config: OutpostDeviceConfig, config_dir: Path
) -> None:
    """Generate the device information file."""
    device_info_dict = msgspec.to_builtins(outpost_device_config.device_info)

    with open(config_dir / "device-info.yml", "w", encoding="utf-8") as config_file:
        yaml.dump(device_info_dict, config_file, indent=4, default_flow_style=False)


def install_runtime(outpost_device_config: OutpostDeviceConfig) -> None:
    """Install the Outpost runtime on the device."""
    with subprocess.Popen(
        [
            "sudo",
            "bash",
            f"{outpost_device_config.runtime_dir}/runtime/scripts/setup.sh",
            "--runtime-version",
            str(outpost_device_config.runtime.version),
            "--config-version",
            str(outpost_device_config.configuration.spec.config_version),
            "--working-dir",
            f"{outpost_device_config.runtime_dir}/runtime",
            "--python",
            outpost_device_config.python_version,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    ) as installation_process:
        for line in installation_process.stdout:
            print(line, end="")
            sys.stdout.flush()

        # Wait for the process to complete and get the return code
        return_code = installation_process.wait()

        if return_code != 0:
            error_output = installation_process.stderr.read()
            raise Error(
                f"Error installing runtime (code {return_code}): {error_output}"
            )

        print("Runtime installation successful.")


@start_spinner
def deregister_device(
    outpost_device_config: OutpostDeviceConfig, message_queue: queue.Queue
):
    """Deregister the current device from the server."""
    message_queue.put("Deregistering device...")
    try:
        response = requests.delete(
            (
                f"{CONSTS.NEXUS_ENDPOINT}/workspaces/ws_"
                f"{outpost_device_config.device_credentials.workspace_id}"
                f"/outpost/devices/{outpost_device_config.id}"
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

        if response.status_code == 404:
            return "Device not found. It may have already been deregistered."

        if response.status_code != 405:
            raise Error(
                MESSAGES.SERVER_UNKNOWN_ERROR_MESSAGE.format(response.text)
            ) from exc

    if response.json()["deleted"]:
        return "Device deregistration successful."

    raise Error("Error deregistering device. Please try again.")


def uninstall_runtime(outpost_device_config: OutpostDeviceConfig):
    """Uninstall the Outpost runtime from the device."""
    try:
        with subprocess.Popen(
            [
                "sudo",
                "bash",
                f"{outpost_device_config.runtime_dir}/runtime/scripts/uninstall.sh",
                "--yes",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        ) as process:
            # Stream output in real-time
            for line in process.stdout:
                sys.stdout.write(line)
                sys.stdout.flush()

            # Wait for the process to complete and check return code
            return_code = process.wait()
            if return_code != 0:
                raise subprocess.CalledProcessError(return_code, process.args)

        shutil.rmtree(outpost_device_config.runtime_dir)

    except subprocess.CalledProcessError as exc:
        raise Error(
            f"Uninstall script failed with return code: {exc.returncode}"
        ) from exc

    except Exception as exc:
        raise Error(f"Error running uninstall script: {str(exc)}") from exc

    print("Outpost runtime uninstalled successfully.")


def get_certificate_expiry(certificate_path: Path) -> datetime:
    """Read a certificate file and return its expiration date."""

    with open(certificate_path, "rb") as cert_file:
        cert_data = cert_file.read()

    try:
        cert = x509.load_pem_x509_certificate(cert_data, default_backend())

    except Exception as exc:
        raise Error(f"Error parsing current certificate: {exc}") from exc

    # Get expiration date
    expiry_date = cert.not_valid_after_utc

    return expiry_date


def validate_certificate(outpost_device_config: OutpostDeviceConfig) -> None:
    """Check the validity of the device certificate."""
    certificate_path = None
    for path in [
        RUNTIME_CREDENTIALS_DIR / "device.crt",
        DEFAULT_CREDENTIALS_DIR / "device.crt",
    ]:
        if path.exists():
            certificate_path = path
            break

    if not certificate_path:
        raise Error(
            "Error: Device certificate not found. "
            "Please re-run `datature outpost install` to generate a new certificate."
        )

    outpost_device_config.device_status.certificate_expires_at = get_certificate_expiry(
        certificate_path
    )
    if outpost_device_config.device_status.certificate_expires_at and (
        datetime.now(timezone.utc)
        < outpost_device_config.device_status.certificate_expires_at
    ):
        outpost_device_config.device_status.valid_certificate = True
    else:
        outpost_device_config.device_status.valid_certificate = False


def get_outpost_runtime_status(
    outpost_device_config: OutpostDeviceConfig, user: str = "datature"
):
    """Get the status of the Outpost runtime.

    Args:
        outpost_device_config: Outpost device configuration.
        user: The user under which the service is running.
    """
    device_info = get_device(outpost_device_config)
    overall_status = device_info.get("status", {})
    outpost_device_config.device_status.status = DeviceStatusProperties(
        message=overall_status.get("message"),
        last_connected_at=overall_status.get("lastConnectedAt"),
        sample_prediction=overall_status.get("samplePrediction"),
    )

    try:
        updater_status, updater_pid, updater_status_output = get_service_status(
            "datature-outpost-updater", user
        )
    except Exception as e:
        updater_status = "error"
        updater_pid = None
        updater_status_output = f"Error retrieving status: {str(e)}"

    # Check runtime manager service
    try:
        runtime_status, runtime_pid, runtime_status_output = get_service_status(
            "datature-outpost-runtime-manager", user
        )
    except Exception as e:
        runtime_status = "error"
        runtime_pid = None
        runtime_status_output = f"Error retrieving status: {str(e)}"

    outpost_device_config.device_status.updater_status = UpdaterStatus(
        status=updater_status,
        pid=updater_pid,
        status_output=updater_status_output,
    )

    outpost_device_config.device_status.runtime_status = RuntimeStatus(
        status=runtime_status,
        pid=runtime_pid,
        status_output=runtime_status_output,
    )

    outpost_device_config.write_to_file()


def get_service_status(
    service_name: str,
    user: str = "datature",
) -> Tuple[str, Optional[int], str]:
    """Get the status of a systemd service for a specific user.

    Args:
        service_name: The name of the service to check.
        user: The user under which the service is running.

    Returns:
        Tuple of (active_state, pid, full_output)
    """
    cmd = [
        "sudo",
        "-u",
        user,
        "bash",
        "-c",
        f"XDG_RUNTIME_DIR=/run/user/$(id -u {user}) systemctl --user status {service_name}",
    ]

    try:
        # Run the command and capture output
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,  # Don't raise exception on non-zero exit code
        )

        # Parse the output to extract status information
        return parse_systemctl_output(result.stdout)

    except subprocess.SubprocessError as exc:
        raise SystemError(
            f"Error running systemctl as user {user}: {str(exc)}"
        ) from exc


def parse_systemctl_output(output: str) -> Tuple[str, Optional[int], str]:
    """
    Parse systemctl status output to extract active state and PID.

    Args:
        output: The output from systemctl status command

    Returns:
        Tuple of (active_state, pid, full_output)
    """
    active_state = "unknown"
    pid = None

    # Process output line by line
    for line in output.splitlines():
        line = line.strip()

        # Extract active state
        if "Active:" in line:
            parts = line.split(":", 1)[1].strip()
            active_state = parts.split()[0].lower()

        # Extract PID
        if "Main PID:" in line:
            pid_part = line.split(":", 1)[1].strip().split()[0]
            try:
                pid = int(pid_part)
            except ValueError:
                pass

    return active_state, pid, output


def format_outpost_runtime_status(
    outpost_device_config: OutpostDeviceConfig, current_device_info: Dict[str, Any]
) -> None:
    """Format and print the Outpost runtime status.

    Args:
        outpost_device_config: Outpost device configuration.
        current_device_info: Current device information.
    """
    overall_status = outpost_device_config.device_status.status
    updater_status = outpost_device_config.device_status.updater_status
    runtime_status = outpost_device_config.device_status.runtime_status

    certificate_expires_in = (
        outpost_device_config.device_status.certificate_expires_at
        - datetime.now(timezone.utc)
    ).days

    is_certificate_valid = (
        outpost_device_config.device_status.valid_certificate
        and certificate_expires_in > 0
    )

    if certificate_expires_in < 0:
        certificate_status = "Expired"
    elif certificate_expires_in < 7:
        certificate_status = "Expiring soon, please renew"
    elif is_certificate_valid:
        certificate_status = "Valid"
    else:
        certificate_status = "Invalid"

    cpu_cores_used = round(current_device_info["cpu_cores_used"], 2)
    cpu_memory_used_gib = round(current_device_info["cpu_memory_used_bytes"] / 1e9, 2)
    disk_space_used_gib = round(current_device_info["disk_space_used_bytes"] / 1e9, 2)
    cameras_in_use = current_device_info["cameras_in_use"]

    print(f"+{'-' * 63}+")
    print(f"| {'NAME':<30} {'ID':<30} |")
    print(
        f"| {outpost_device_config.name:<30} "
        f"{outpost_device_config.id.strip('outpostdevice_'):<30} |"
    )
    print(f"|{'=' * 63}|")
    print(f"| {'CERTIFICATE':<30} {'EXPIRES IN':<30} |")
    print(f"| {certificate_status:<30} {certificate_expires_in:<5} {'days':<24} |")
    print(f"|{'-' * 63}|")
    print(f"| {'Status':<30} {overall_status.message:<30} |")
    print(f"| {'+' * 61} |")
    print(f"| {'SERVICE':<30} {'PID':<10} {'STATUS':<19} |")
    print(f"| {'Updater':<30} {updater_status.pid:<10} {updater_status.status:<19} |")
    print(
        f"| {'Runtime Manager':<30} {runtime_status.pid:<10} {runtime_status.status:<19} |"
    )
    print(f"|{'-' * 63}|")
    print(f"| {'RESOURCE UTILIZATION':<61} |")
    print(f"| {'CPU Cores':<30} {cpu_cores_used:<30} |")
    print(f"| {'CPU Memory':<30} {cpu_memory_used_gib:<10} {'GiB':<19} |")
    print(f"| {'Disk Space':<30} {disk_space_used_gib:<10} {'GiB':<19} |")
    print(
        f"| {'Camera IDs':<30} {', '.join(cameras_in_use) if cameras_in_use else str(None):<30} |"
    )
    print(f"+{'-' * 63}+")

    if overall_status.message == "Archived":
        print(
            "\nThis device has already been archived. To uninstall the runtime, please run the following command: "
            "`datature outpost uninstall`"
        )
