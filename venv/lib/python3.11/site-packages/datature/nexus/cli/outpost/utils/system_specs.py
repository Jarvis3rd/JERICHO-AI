#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   system_specs.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Outpost system specifications module.
"""

# pylint: disable=R0914,W0718,E1102

import queue
import subprocess
import sys
from typing import List

from datature.nexus.cli.outpost import consts as CONSTS
from datature.nexus.cli.outpost import messages as MESSAGES
from datature.nexus.cli.outpost.common import install_pip_package
from datature.nexus.cli.outpost.types import (
    Accelerator,
    AcceleratorMemory,
    AcceleratorPerformanceMetric,
    Camera,
    CameraCaptureProfile,
    CPUCore,
    CPUMemory,
    DeviceInfo,
    FrameRate,
    OutpostDeviceConfig,
)
from datature.nexus.cli.outpost.utils import start_spinner
from datature.nexus.error import Error

try:
    import psutil
except ImportError as exc:
    if not install_pip_package("psutil"):
        raise Error(
            MESSAGES.INSTALL_PIP_PACKAGE_ERROR_MESSAGE.format(package_name="psutil")
        ) from exc
    import psutil

try:
    import pyudev
except ImportError as exc:
    if not install_pip_package("pyudev"):
        raise Error(
            MESSAGES.INSTALL_PIP_PACKAGE_ERROR_MESSAGE.format(package_name="pyudev")
        ) from exc
    import pyudev

try:
    from linuxpy.video.device import BufferType, Device, V4L2Error
except ImportError as exc:
    if not install_pip_package("linuxpy"):
        raise Error(
            MESSAGES.INSTALL_PIP_PACKAGE_ERROR_MESSAGE.format(package_name="linuxpy")
        ) from exc
    from linuxpy.video.device import BufferType, Device, V4L2Error

try:
    import pynvml
except ImportError as exc:
    if not install_pip_package("nvidia-ml-py"):
        raise Error(
            MESSAGES.INSTALL_PIP_PACKAGE_ERROR_MESSAGE.format(
                package_name="nvidia-ml-py"
            )
        ) from exc
    import pynvml


def create_device_id():
    """
    Create unique device ID, which is a combination of 'outpostdevice_' and the last 22 characters
    of the machine ID.
    """
    with open("/etc/machine-id", "r", encoding="utf-8") as machine_id_file:
        device_id = f"outpostdevice_{str(machine_id_file.read().strip())[-22:]}"
    return device_id


def get_cameras_info():
    """Get camera information."""
    cameras = []
    try:
        context = pyudev.Context()
        for device in context.list_devices(subsystem="video4linux"):
            with Device(device.device_node) as video_input:
                try:
                    input_format = video_input.get_format(BufferType.VIDEO_CAPTURE)
                except OSError:
                    continue

                resolution = [input_format.width, input_format.height]
                frame_rate = FrameRate(
                    frames=int(video_input.get_fps(BufferType.VIDEO_CAPTURE)),
                    interval="Second",
                )

                capture_profile = CameraCaptureProfile(
                    resolution=resolution,
                    max_frame_rate=frame_rate,
                )

                camera = Camera(
                    id=str(device.device_node.strip("/dev/video")),
                    name=video_input.info.card,
                    capture_profiles=[capture_profile],
                )

                cameras.append(camera)

        if len(cameras) == 0:
            raise V4L2Error("No input devices found")

    except V4L2Error as exc:
        print(f"Error getting camera information: {exc}")
        print(
            "Warning: Please ensure that you have a camera connected to your device when starting the runtime."
        )

    except Exception as exc:
        print(f"Unknown error when getting camera information: {exc}")
        print(f"Please contact {CONSTS.SUPPORT_EMAIL} for assistance.")
        sys.exit(1)

    return cameras


def get_cpu_core_info():
    """Get CPU core information."""
    cpu_model_name = ""
    try:
        with open("/proc/cpuinfo", "r", encoding="utf-8") as f:
            for line in f:
                if "model name" in line:
                    cpu_model_name = line.split(":")[1].strip()
                    break
    except Exception:
        cpu_model_name = "Unknown CPU"

    core_count = psutil.cpu_count(logical=False)

    return CPUCore(name=cpu_model_name, count=core_count)


def get_cpu_memory_info():
    """Get CPU memory information, in bytes."""
    return CPUMemory(bytes=psutil.virtual_memory().total)


def get_disk_space_bytes():
    """Get disk space in bytes."""
    return int(psutil.disk_usage("/").total)


def get_accelerator_info(device_model_name: str) -> List[Accelerator]:
    """Get accelerator information for CUDA devices."""
    try:
        pynvml.nvmlInit()

        driver_version = pynvml.nvmlSystemGetDriverVersion()
        if isinstance(driver_version, bytes):
            driver_version = driver_version.decode("utf-8")

        cuda_version = pynvml.nvmlSystemGetCudaDriverVersion()
        device_count = pynvml.nvmlDeviceGetCount()

        accelerators = []

        for i in range(device_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            device_name = str(pynvml.nvmlDeviceGetName(handle))

            try:
                device_vram_bytes = int(pynvml.nvmlDeviceGetMemoryInfo(handle).total)

            except pynvml.NVMLError as exc:
                if "jetson" in device_model_name.lower():
                    device_vram_bytes = get_cpu_memory_info().bytes
                else:
                    raise exc from exc

            device_compute_capability = pynvml.nvmlDeviceGetCudaComputeCapability(
                handle
            )

            device_uuid = pynvml.nvmlDeviceGetUUID(handle)
            if isinstance(device_uuid, bytes):
                device_uuid = device_uuid.decode("utf-8")

            num_cuda_cores = pynvml.nvmlDeviceGetNumGpuCores(handle)

            accelerator_memory = AcceleratorMemory(
                bytes=device_vram_bytes,
                shared=bool("jetson" in device_model_name.lower()),
            )

            accelerator_performance_metrics = [
                AcceleratorPerformanceMetric(
                    name="CUDA Cores",
                    value=num_cuda_cores,
                ),
                AcceleratorPerformanceMetric(
                    name="Compute Capability",
                    value=".".join(map(str, device_compute_capability)),
                ),
                AcceleratorPerformanceMetric(
                    name="CUDA Version",
                    value=cuda_version,
                ),
                AcceleratorPerformanceMetric(
                    name="Driver Version",
                    value=driver_version,
                ),
            ]

            accelerator = Accelerator(
                manufacturer="NVIDIA",
                name=device_name,
                id=device_uuid.replace("GPU-", ""),
                memory=accelerator_memory,
                performance_metrics=accelerator_performance_metrics,
            )

            accelerators.append(accelerator)

        pynvml.nvmlShutdown()

        return accelerators

    except subprocess.CalledProcessError as exc:
        raise Error(f"Error running nvidia-settings: {exc.stderr}") from exc

    except pynvml.NVMLError:
        print("\nNo CUDA support found, skipping accelerator check.")

    except Error as exc:
        raise Error(f"Error getting CUDA accelerator information: {exc}") from exc

    return []


def get_device_info():
    """Get device information."""
    try:
        with open(
            "/sys/devices/virtual/dmi/id/product_name", "r", encoding="utf-8"
        ) as f:
            device_model_name = f.read().strip()
    except Exception as exc:
        print(f"Error getting device model name: {exc}, using 'Unknown Device'")
        device_model_name = "Unknown Device"

    # Initialize variables with default values
    cpu_core = None
    cpu_memory = None
    disk_space_bytes = 0
    cameras = []
    accelerators = []

    try:
        cpu_core = get_cpu_core_info()
        cpu_memory = get_cpu_memory_info()
        disk_space_bytes = get_disk_space_bytes()
        cameras = get_cameras_info()
        accelerators = get_accelerator_info(device_model_name)

    except Exception as exc:
        print(f"Error getting device information: {exc}")

    # Ensure we have valid values before returning
    if cpu_core is None:
        cpu_core = CPUCore(name="Unknown CPU", count=1)
    if cpu_memory is None:
        cpu_memory = CPUMemory(bytes=0)

    return (
        device_model_name,
        cpu_core,
        cpu_memory,
        disk_space_bytes,
        cameras,
        accelerators,
    )


def get_cameras_in_use():
    """Get cameras in use."""
    in_use_cameras = []

    try:
        context = pyudev.Context()
        for device in context.list_devices(subsystem="video4linux"):
            with Device(device.device_node) as video_input:
                # Try to start streaming (will fail if device is busy)
                try:
                    for _ in video_input:
                        break
                except IOError as io_exc:
                    if "Device or resource busy" in str(io_exc):
                        device_id = str(device.device_node.replace("/dev/video", ""))
                        in_use_cameras.append(device_id)
                except V4L2Error:
                    continue

    except V4L2Error as exc:
        print(f"Error: {exc}")
        sys.exit(1)

    return in_use_cameras


def get_current_device_info():
    """Get current device information."""
    cpu_cores_used = float(
        psutil.cpu_count(logical=True) * psutil.cpu_percent(interval=1) / 100
    )
    cpu_memory_used_bytes = int(psutil.virtual_memory().used)
    disk_space_used_bytes = int(psutil.disk_usage("/").used)
    cameras_in_use = get_cameras_in_use()

    return {
        "cpu_cores_used": cpu_cores_used,
        "cpu_memory_used_bytes": cpu_memory_used_bytes,
        "disk_space_used_bytes": disk_space_used_bytes,
        "cameras_in_use": cameras_in_use,
    }


@start_spinner
def check_system_specs(
    outpost_device_config: OutpostDeviceConfig, message_queue: queue.Queue
) -> None:
    """Check system specifications.

    :param outpost_device_config (OutpostDeviceConfig): Outpost device configuration.
    :param message_queue (queue.Queue): Message queue.
    """
    message_queue.put("Checking system specifications...")
    try:
        outpost_device_config.id = create_device_id()
        (
            device_model_name,
            cpu_core,
            cpu_memory,
            disk_space_bytes,
            cameras,
            accelerators,
        ) = get_device_info()

    except Exception as exc:
        print(f"Error getting device information: {exc}")
        print(
            "Please ensure that you are running this command on a supported Linux machine."
        )
        print(
            f"The list of supported machines can be found at: {CONSTS.DOCS_ENV_SETUP_URL}"
        )
        print(
            "If you wish to run this command on an unsupported machine,"
            f" please contact us at {CONSTS.SUPPORT_EMAIL}."
        )
        sys.exit(1)

    if cpu_memory.bytes < CONSTS.MINIMUM_RAM_BYTES:
        raise ValueError(
            f"Insufficient RAM. You have {cpu_memory.bytes} bytes,"
            f" but you need at least {CONSTS.MINIMUM_RAM_BYTES} bytes"
        )

    if disk_space_bytes < CONSTS.MINIMUM_STORAGE_BYTES:
        raise ValueError(
            f"Insufficient storage space. You have {disk_space_bytes}"
            f" bytes, but you need at least {CONSTS.MINIMUM_STORAGE_BYTES} bytes"
        )

    device_info = DeviceInfo(
        name=device_model_name,
        components=[cpu_core, cpu_memory] + cameras + accelerators,
    )

    outpost_device_config.device_info = device_info
    outpost_device_config.write_to_file()

    return "Success: System requirements verified."
