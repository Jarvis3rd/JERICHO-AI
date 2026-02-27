#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   types.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Outpost types.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import msgspec
from msgspec import MsgspecError, Struct, field

from datature.nexus.cli.outpost.consts import OUTPOST_CONFIG_FILE_PATH


class DateTimeEncoder(json.JSONEncoder):
    """JSON encoder for datetime objects."""

    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return json.JSONEncoder.default(self, o)


class ConfigVariable(Struct, rename="camel", kw_only=True):
    """Config variable object."""

    kind: str = ""
    role: str = ""
    default: str = ""


class OutpostDeviceConfigurationSpec(Struct, rename="camel", kw_only=True):
    """Outpost configuration spec struct.

    :param kind: Configuration kind.
    :param config_version: Configuration version.
    :param config_data: Configuration data.
    :param config_variables: Configuration variables.
    """

    kind: str = ""
    config_version: str = ""
    config_data: Dict[str, str] = field(default_factory=dict)
    config_variables: Dict[str, ConfigVariable] = field(default_factory=dict)


class OutpostDeviceConfiguration(Struct, rename="camel", kw_only=True):
    """Outpost configuration struct.

    :param id: Configuration ID.
    :param object: Configuration object type.
    :param workspace_id: Workspace ID.
    :param name: Configuration name.
    :param spec: Configuration spec.
    :param create_date: Configuration creation date.
    :param update_date: Configuration update date.
    :param metadata_generation: Configuration metadata generation.
    """

    id: str = ""
    object: str = ""
    workspace_id: str = ""
    name: str = ""
    spec: OutpostDeviceConfigurationSpec = field(
        default_factory=OutpostDeviceConfigurationSpec
    )
    create_date: int = 0
    update_date: int = 0
    metadata_generation: int = 0


class FrameRate(
    Struct,
    omit_defaults=True,
    rename="camel",
    kw_only=True,
):
    """Frame rate struct.

    :param frames: Number of frames to take in the interval.
    :param interval: Time interval for measuring frame rate in seconds.
    """

    frames: int
    interval: str


class CameraCaptureProfile(
    Struct,
    omit_defaults=True,
    rename="camel",
    kw_only=True,
):
    """Camera capture profile struct.

    :param resolution: Pixel resolution of the camera in [width, height], e.g., [1920, 1080].
    :param max_frame_rate: Frame rate of the camera.
    """

    resolution: List[int]
    max_frame_rate: FrameRate


class CPUCore(
    Struct,
    omit_defaults=True,
    rename="camel",
    tag="CpuCore",
    tag_field="kind",
    kw_only=True,
):
    """CPU core struct.

    :param name: Core name.
    :param count: Number of cores.
    """

    name: str
    count: int


class CPUMemory(
    Struct,
    omit_defaults=True,
    rename="camel",
    tag="CpuMemory",
    tag_field="kind",
    kw_only=True,
):
    """CPU memory struct.

    :param bytes: Total memory in bytes.
    """

    bytes: int


class AcceleratorMemory(Struct, omit_defaults=True, rename="camel", kw_only=True):
    """Accelerator memory struct.

    :param bytes: Total memory in bytes.
    :param shared: Whether the memory is shared.
    """

    bytes: int
    shared: bool


class AcceleratorPerformanceMetric(
    Struct, omit_defaults=True, rename="camel", kw_only=True
):
    """Accelerator performance metric struct.

    :param name: Name of the performance metric.
    :param value: Value of the performance metric.
    """

    name: str
    value: int | float | str


class Accelerator(
    Struct,
    omit_defaults=True,
    rename="camel",
    tag="Accelerator",
    tag_field="kind",
    kw_only=True,
):
    """Accelerator struct.

    :param manufacturer: Manufacturer of the accelerator.
    :param name: Name of the accelerator.
    :param id: Accelerator ID.
    :param memory: Accelerator memory.
    :param performance_metrics: List of performance metrics for the accelerator.
    """

    manufacturer: str
    name: str
    id: str
    memory: AcceleratorMemory
    performance_metrics: list[AcceleratorPerformanceMetric]


class Camera(
    Struct,
    omit_defaults=True,
    rename="camel",
    tag="Camera",
    tag_field="kind",
    kw_only=True,
):
    """Camera struct.

    :param id: Camera ID used for capturing images (this is typically 0, 1, 2, etc.). Default is -1.
    :param name: Camera name or brand.
    :param capture_profiles: List of camera capture profiles.
    """

    id: str
    name: str
    capture_profiles: List[CameraCaptureProfile]


DeviceComponent = Union[CPUCore, CPUMemory, Camera, Accelerator]


class DeviceInfo(Struct, omit_defaults=True, rename="camel", kw_only=True):
    """Device information struct.

    :param name: Device name.
    :param components: List of device components.
    """

    name: str = ""
    components: List[DeviceComponent] = field(default_factory=list)


class RegistrationStatus(Enum):
    """Registration status enum."""

    ARCHIVED = "Archived"
    FROZEN = "Frozen"
    PAUSED = "Paused"
    REGISTERED = "Registered"
    TESTING = "Testing"


class DeviceStatusMessage(Enum):
    """Device status message enum."""

    ARCHIVED = "Archived"
    ARCHIVED_ROLLING_OUT = "ArchivedRollingOut"
    FROZEN = "Frozen"
    FROZEN_ROLLING_OUT = "FrozenRollingOut"
    OFFLINE = "Offline"
    PAUSED = "Paused"
    PAUSED_ROLLING_OUT = "PausedRollingOut"
    READY = "Ready"
    READY_FAILED_ROLL_OUT = "ReadyFailedRollOut"
    READY_ROLLING_OUT = "ReadyRollingOut"
    REGISTERING = "Registering"


class DeviceStatusProperties(Struct, omit_defaults=True, rename="camel", kw_only=True):
    """Device status properties struct.

    :param message: Status message.
    :param last_connected_at: Last connected timestamp.
    :param sample_prediction: Sample prediction data.
    """

    message: Optional[str] = None
    last_connected_at: Optional[int] = None
    sample_prediction: Optional[Dict[str, Any]] = None


class UpdaterStatus(
    Struct,
    omit_defaults=True,
    rename="camel",
    kw_only=True,
):
    """Updater status struct.

    :param status: Updater status.
    :param pid: Process ID of the updater.
    :param status_output: Output of the updater status.
    """

    status: Optional[str] = None
    pid: Optional[int] = None
    status_output: Optional[str] = None


class RuntimeStatus(
    Struct,
    omit_defaults=True,
    rename="camel",
    kw_only=True,
):
    """Runtime status struct.

    :param status: Runtime status.
    :param pid: Process ID of the runtime.
    :param status_output: Output of the runtime status.
    """

    status: Optional[str] = None
    pid: Optional[int] = None
    status_output: Optional[str] = None


class DeviceStatus(
    Struct,
    omit_defaults=True,
    rename="camel",
    kw_only=True,
):
    """Device status struct.

    :param status: Device status.
    :param updater_status: Updater status.
    :param runtime_status: Runtime status.
    :param last_updated: Last updated timestamp.
    :param valid_certificate: Whether the certificate is valid.
    :param certificate_expires_at: Certificate expiration timestamp.
    """

    status: DeviceStatusProperties = field(default_factory=DeviceStatusProperties)
    updater_status: UpdaterStatus = field(default_factory=UpdaterStatus)
    runtime_status: RuntimeStatus = field(default_factory=RuntimeStatus)
    last_updated: Optional[datetime] = None
    valid_certificate: bool = False
    certificate_expires_at: Optional[datetime] = None


class DeviceCredentials(
    Struct,
    omit_defaults=True,
    rename="camel",
    kw_only=True,
):
    """Device credentials struct.

    :param secret_key: Workspace secret key.
    :param workspace_id: Workspace ID.
    :param default_project_id: Default project ID.
    """

    secret_key: str = ""
    workspace_id: str = ""
    default_project_id: str = ""


class RuntimeVersion(Struct, rename="camel", kw_only=True):
    """Runtime version struct.

    :param major: Major version.
    :param minor: Minor version.
    :param patch: Patch version.
    """

    major: int = 0
    minor: int = 0
    patch: int = 0

    def __str__(self):
        return f"{self.major}.{self.minor}.{self.patch}"


class RuntimeLink(Struct, rename="camel", kw_only=True):
    """Runtime link struct.

    :param url: Signed URL of the runtime zip file.
    :param expires_at: Expiration timestamp of the link.
    """

    url: str = ""
    expires_at: int = 0


class OutpostDeviceRuntime(Struct, rename="camel", kw_only=True):
    """Outpost runtime struct.

    :param id: Runtime ID.
    :param object: Runtime object type.
    :param build: Runtime build.
    :param version: Runtime version.
    :param link: Runtime link.
    :param description: Runtime description.
    :param is_visible: Whether the runtime is visible.
    :param yanked: Whether the runtime is yanked.
    :param create_date: Runtime creation date.
    :param update_date: Runtime update date.
    :param metadata_generation: Runtime metadata generation.
    """

    id: str = ""
    object: str = ""
    build: str = ""
    version: RuntimeVersion = field(default_factory=RuntimeVersion)
    link: RuntimeLink = field(default_factory=RuntimeLink)
    description: str = ""
    is_visible: bool = True
    yanked: bool = False
    create_date: int = 0
    update_date: int = 0
    metadata_generation: int = 0


class MetadataSpec(Struct, rename="camel", kw_only=True):
    """Metadata spec struct.

    :param device_uid: Device UID.
    :param tags: Device tags.
    :param metadata_generation: Metadata generation.
    :param configuration: Device configuration.
    :param runtime: Device runtime.
    """

    device_uid: str = ""
    tags: Dict[str, str] = field(default_factory=dict)
    metadata_generation: int = 0
    revision_id: str = ""
    configuration: OutpostDeviceConfiguration = field(
        default_factory=OutpostDeviceConfiguration
    )
    runtime: OutpostDeviceRuntime = field(default_factory=OutpostDeviceRuntime)
    runtime_variables: Dict[str, Any] = field(default_factory=dict)


class OutpostDeviceConfig(
    Struct,
    omit_defaults=True,
    rename="camel",
    kw_only=True,
):
    """Outpost device configuration struct.

    :param id: Device ID.
    :param uid: Device UID.
    :param name: Device name.
    :param tags: Device tags.
    :param default_artifact_id: Default artifact ID.
    :param metadata_generation: Metadata generation.
    :param configuration: Device configuration.
    :param runtime: Device runtime.
    :param runtime_dir: Runtime directory.
    :param python_version: Python version for runtime installation.
    :param device_info: Device information.
    :param device_status: Device status.
    :param device_credentials: Device credentials.
    """

    id: str = ""
    uid: str = ""
    name: str = ""
    tags: Dict[str, str] = field(default_factory=dict)
    default_artifact_id: str = ""
    metadata_generation: int = 0
    configuration: OutpostDeviceConfiguration = field(
        default_factory=OutpostDeviceConfiguration
    )
    runtime: OutpostDeviceRuntime = field(default_factory=OutpostDeviceRuntime)
    runtime_dir: str = ""
    python_version: str = "python3.10"
    device_info: DeviceInfo = field(default_factory=DeviceInfo)
    device_status: DeviceStatus = field(default_factory=DeviceStatus)
    device_credentials: DeviceCredentials = field(default_factory=DeviceCredentials)

    def __post_init__(self):
        if not OUTPOST_CONFIG_FILE_PATH.exists():
            with open(OUTPOST_CONFIG_FILE_PATH, "w", encoding="utf-8"):
                pass

    def write_to_file(self) -> None:
        """Write Outpost configuration to file."""
        try:
            outpost_device_config_dict = msgspec.to_builtins(self)

            with open(OUTPOST_CONFIG_FILE_PATH, "w", encoding="utf-8") as config_file:
                json.dump(
                    outpost_device_config_dict,
                    config_file,
                    cls=DateTimeEncoder,
                    indent=4,
                )

        except (IOError, MsgspecError) as exc:
            print(f"Error writing Outpost config to {OUTPOST_CONFIG_FILE_PATH}: {exc}")
            sys.exit(1)

    @classmethod
    def read_from_file(cls) -> OutpostDeviceConfig:
        """Read Outpost configuration from file."""
        if not OUTPOST_CONFIG_FILE_PATH.exists():
            print(
                "Device not registered. "
                "Please run 'datature outpost install' to register this device."
            )
            sys.exit(1)

        try:
            if OUTPOST_CONFIG_FILE_PATH.stat().st_size == 0:
                return cls()

            with open(OUTPOST_CONFIG_FILE_PATH, "r", encoding="utf-8") as config_file:
                json_data = json.loads(config_file.read())
                return msgspec.convert(json_data, type=OutpostDeviceConfig)

        except (IOError, MsgspecError) as exc:
            print(
                f"Error reading Outpost config from {OUTPOST_CONFIG_FILE_PATH}: {exc}"
            )
            sys.exit(1)

    def remove_from_file(self) -> None:
        """Remove Outpost configuration from file."""

        with open(OUTPOST_CONFIG_FILE_PATH, "w", encoding="utf-8") as config_file:
            config_file.write("")
