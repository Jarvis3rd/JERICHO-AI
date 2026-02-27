#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   manager.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Outpost installation manager module.
"""

# pylint: disable=W0718,E1120

import queue
import sys
import time
import traceback

from InquirerPy import inquirer

from datature.nexus.cli.outpost import consts as CONSTS
from datature.nexus.cli.outpost import utils
from datature.nexus.cli.outpost.types import (
    DeviceStatusMessage,
    OutpostDeviceConfig,
    RegistrationStatus,
)
from datature.nexus.error import Error

ACTION_TIMEOUT_SECONDS = 300


class OutpostManager:
    """Outpost Manager class."""

    def __init__(self):
        CONSTS.OUTPOST_CONFIG_ROOT_DIR.mkdir(parents=True, exist_ok=True)
        self._outpost_device_config = OutpostDeviceConfig.read_from_file()

    def create_configuration(self):
        """Create Outpost configuration."""
        try:
            utils.create_configuration(self._outpost_device_config)
            self._outpost_device_config.write_to_file()
        except KeyboardInterrupt:
            sys.exit(1)
        except Error:
            sys.exit(1)
        except Exception:
            traceback.print_exc()
            sys.exit(1)

    def install(self):
        """Install Outpost on device."""
        try:
            utils.prompt_for_configuration_version(self._outpost_device_config)
            utils.prompt_for_runtime_config(self._outpost_device_config)
            utils.prompt_for_python_version(self._outpost_device_config)
            print()

            utils.register_device(self._outpost_device_config)
            utils.setup_outpost_credentials(self._outpost_device_config)
            utils.get_outpost_device_config_files(self._outpost_device_config)
            utils.get_outpost_runtime_files(self._outpost_device_config)

            self._outpost_device_config.write_to_file()

            print("Installing Outpost runtime... This may take a few minutes.")
            utils.install_runtime(self._outpost_device_config)

        except KeyboardInterrupt:
            sys.exit(1)

        except Error as exc:
            print(exc)
            sys.exit(1)

        except Exception:
            traceback.print_exc()
            sys.exit(1)

    def uninstall(self):
        """Uninstall Outpost from device."""
        try:
            self.pause()
            utils.deregister_device(self._outpost_device_config)

        except Error:
            print(
                "Warning: error occurred while deregistering device. "
                "It may have already been deregistered."
            )

        try:
            cleanup = inquirer.confirm(
                message=(
                    "Do you also want to remove all Outpost runtime files from your device?"
                ),
            ).execute()

            if cleanup:
                utils.uninstall_runtime(self._outpost_device_config)

            self._outpost_device_config.remove_from_file()

        except Error as exc:
            print(exc)
            sys.exit(1)

        except Exception:
            traceback.print_exc()
            sys.exit(1)

    @utils.start_spinner(raise_on_error=True)
    def pause(self, message_queue: queue.Queue):
        """Pause Outpost runtime."""
        message_queue.put("Pausing Outpost runtime...")

        runtime_status = utils.get_runtime_status_message(self._outpost_device_config)

        if runtime_status in [DeviceStatusMessage.OFFLINE.value]:
            return (
                "Outpost runtime is offline. "
                "It may have already been paused, or the device is unreachable."
            )

        if runtime_status in [
            DeviceStatusMessage.PAUSED.value,
            DeviceStatusMessage.PAUSED_ROLLING_OUT.value,
        ]:
            return "Outpost runtime is already paused."

        status_data = {"spec": {"registrationStatus": RegistrationStatus.PAUSED.value}}

        utils.patch_device(self._outpost_device_config, status_data)

        start_time = time.time()
        while utils.get_runtime_status_message(self._outpost_device_config) not in [
            DeviceStatusMessage.PAUSED_ROLLING_OUT.value,
            DeviceStatusMessage.PAUSED.value,
        ]:
            if time.time() - start_time > ACTION_TIMEOUT_SECONDS:
                raise TimeoutError("Pausing Outpost runtime timed out.")

            time.sleep(1)

        if (
            utils.get_runtime_status_message(self._outpost_device_config)
            == DeviceStatusMessage.PAUSED_ROLLING_OUT.value
        ):
            return (
                "Outpost runtime initiating pause. "
                "Run `datature outpost status` to check the status."
            )

        return "Outpost runtime paused successfully."

    @utils.start_spinner
    def resume(self, message_queue: queue.Queue):
        """Resume Outpost runtime."""
        message_queue.put("Resuming Outpost runtime...")

        runtime_status = utils.get_runtime_status_message(self._outpost_device_config)

        if runtime_status in [
            DeviceStatusMessage.READY.value,
            DeviceStatusMessage.READY_ROLLING_OUT.value,
        ]:
            return "Outpost runtime is already resumed."

        status_data = {
            "spec": {"registrationStatus": RegistrationStatus.REGISTERED.value}
        }

        utils.patch_device(self._outpost_device_config, status_data)

        start_time = time.time()
        while utils.get_runtime_status_message(self._outpost_device_config) not in [
            DeviceStatusMessage.READY_ROLLING_OUT.value,
            DeviceStatusMessage.READY.value,
        ]:
            if time.time() - start_time > ACTION_TIMEOUT_SECONDS:
                raise TimeoutError("Resuming Outpost runtime timed out.")

            time.sleep(1)

        if (
            utils.get_runtime_status_message(self._outpost_device_config)
            == DeviceStatusMessage.READY_ROLLING_OUT.value
        ):
            return (
                "Outpost runtime initiating resume. "
                "Run `datature outpost status` to check the status."
            )

        return "Outpost runtime resumed successfully."

    def status(self, user: str = "datature") -> None:
        """Get Outpost runtime status."""
        utils.validate_certificate(self._outpost_device_config)
        utils.get_outpost_runtime_status(self._outpost_device_config, user)
        current_device_info = utils.get_current_device_info()

        utils.format_outpost_runtime_status(
            self._outpost_device_config, current_device_info
        )
