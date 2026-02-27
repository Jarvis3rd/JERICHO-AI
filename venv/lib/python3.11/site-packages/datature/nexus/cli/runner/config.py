#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   config.py
@Author  :   Wei Loon Cheng, Kai Xuan Lee
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Custom runner constants.
"""

# pylint: disable=R0902,C0103

from __future__ import annotations

import json
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests

from datature.nexus.cli import messages
from datature.nexus.cli.runner import messages as MESSAGES
from datature.nexus.cli.runner.consts import NEXUS_ENDPOINT, RUNNER_CONFIG_FILE_PATH
from datature.nexus.config import REQUEST_TIME_OUT_SECONDS
from datature.nexus.error import Error


@dataclass
class SystemSpecs:
    """System specifications dataclass."""

    num_cores: int = 0
    ram_total: int = 0
    free_space: int = 0


@dataclass
class GPUInfo:
    """GPU information dataclass."""

    device_id: int
    device_uuid: str
    device_name: str
    device_vram_bytes: int
    device_compute_capability: int
    device_driver_version: str
    device_cuda_version: str
    device_cuda_cores: int


class DateTimeEncoder(json.JSONEncoder):
    """JSON encoder for datetime objects."""

    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return json.JSONEncoder.default(self, o)


@dataclass
class RunnerMetadata:
    """Runner metadata.

    Attributes:
        runner_registry (str): Runner registry.
        runner_name (str): Runner name.
        runner_version (str): Runner version.
    """

    runner_registry: Optional[str] = None
    runner_name: Optional[str] = None
    runner_version: Optional[str] = None

    @classmethod
    def from_dict(cls: RunnerMetadata, data: Dict[str, str]) -> RunnerMetadata:
        """Create Runner metadata from dictionary.

        :param data (Dict[str, str]): Dictionary data.
        :return (RunnerMetadata): Runner metadata.
        """
        snake_case_data = {cls.camel_to_snake(k): v for k, v in data.items()}
        return cls(**snake_case_data)

    @staticmethod
    def camel_to_snake(name: str) -> str:
        """Convert CamelCase to snake_case.

        :param name (str): Name in CamelCase.
        :return (str): Name in snake_case.
        """
        return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


@dataclass
class RunStatus:
    """Run status dataclass."""

    id: Optional[str] = None
    image_name: Optional[str] = None
    status: Optional[str] = None
    started: Optional[datetime] = None
    allocated_memory: Optional[int] = None
    num_gpus: Optional[int] = None


@dataclass
class RunnerStatus:
    """Runner status dataclass."""

    status: Optional[str] = None
    suspended: Optional[bool] = None
    last_updated: Optional[datetime] = None
    valid_secret_key: bool = False
    runs: List[RunStatus] = field(default_factory=list)


@dataclass
class RunnerConfig:
    """Runner configuration dataclass."""

    id: str = ""
    name: str = ""
    secret_key: str = ""
    workspace_id: str = ""
    kubectl_namespace: str = ""
    runner_metadata: RunnerMetadata = field(default_factory=RunnerMetadata)
    system_specs: SystemSpecs = field(default_factory=SystemSpecs)
    gpus: List[GPUInfo] = field(default_factory=list)
    status: RunnerStatus = field(default_factory=RunnerStatus)

    def __post_init__(self):
        if not RUNNER_CONFIG_FILE_PATH.exists():
            runner_configs = []
            with open(
                RUNNER_CONFIG_FILE_PATH,
                "w",
                encoding="utf-8",
            ) as config_file:
                json.dump(runner_configs, config_file, indent=4, cls=DateTimeEncoder)

    def write_to_file(self) -> None:
        """Write Runner configuration to file."""
        try:
            runner_config = asdict(self)

            if (
                RUNNER_CONFIG_FILE_PATH.exists()
                and RUNNER_CONFIG_FILE_PATH.stat().st_size > 0
            ):
                with open(
                    RUNNER_CONFIG_FILE_PATH, "r", encoding="utf-8"
                ) as config_file:
                    runner_configs = json.load(config_file)

                    if len(runner_configs) == 1:
                        if not self.id:
                            runner_configs[0]["name"] = self.name
                        else:
                            runner_configs[0] = runner_config
                    else:
                        runner_configs.append(runner_config)
            else:
                runner_configs = [runner_config]

            with open(RUNNER_CONFIG_FILE_PATH, "w", encoding="utf-8") as config_file:
                json.dump(runner_configs, config_file, indent=4, cls=DateTimeEncoder)
        except (IOError, json.JSONDecodeError) as exc:
            print(f"Error writing Runner config to {RUNNER_CONFIG_FILE_PATH}: {exc}")

    @classmethod
    def read_from_file(cls, runner_name_or_hash: Optional[str] = None) -> RunnerConfig:
        """Read Runner configuration from file.

        :param runner_name_or_hash (str): Runner name or hash.
        :return (RunnerConfig): Runner configuration.
        """
        if not runner_name_or_hash:
            print(
                "Please provide either the name or the hash of your Runner.\n"
                "To get either value, run `datature runner list` to view all available Runners."
            )
            sys.exit(1)

        if not RUNNER_CONFIG_FILE_PATH.exists():
            print(messages.NO_RUNNERS_MESSAGE)
            sys.exit(1)

        try:
            with open(RUNNER_CONFIG_FILE_PATH, "r", encoding="utf-8") as file:
                runner_configs = json.load(file)
                for runner_config in runner_configs:
                    if runner_name_or_hash in (
                        runner_config["name"],
                        runner_config["id"][-6:],
                    ):
                        return cls.from_dict(runner_config)

            print(
                f"Runner '{runner_name_or_hash}' not found. "
                "Please ensure you have entered the correct Runner name or hash.\n"
                "To view all available Runners, run `datature runner list`.\n"
                "If you have not installed a Runner, run `datature runner install` to set up a new Runner."
            )
            sys.exit(1)
        except (IOError, json.JSONDecodeError) as exc:
            print(f"Error reading Runner config from {RUNNER_CONFIG_FILE_PATH}: {exc}")
            sys.exit(1)

    @classmethod
    def read_all_from_file(cls) -> List[RunnerConfig]:
        """Read all Runner configurations from file.

        :return (List[RunnerConfig]): List of Runner configurations.
        """
        try:
            if not RUNNER_CONFIG_FILE_PATH.exists():
                print(messages.NO_RUNNERS_MESSAGE)
                return []

            with open(RUNNER_CONFIG_FILE_PATH, "r", encoding="utf-8") as file:
                runner_configs = json.load(file)
                return [
                    cls.from_dict(runner_config) for runner_config in runner_configs
                ]
        except (IOError, json.JSONDecodeError) as exc:
            print(f"Error reading Runner config from {RUNNER_CONFIG_FILE_PATH}: {exc}")
            sys.exit(1)

    def update(self, force: bool = False) -> None:
        """Update Runner status.

        :param force (bool): True to force update, False otherwise. Default is False.
        """
        if not force and self.is_updated:
            return
        try:
            runner_response = requests.get(
                f"{NEXUS_ENDPOINT}/workspaces/ws_{self.workspace_id}/runners/{self.id}",
                headers={
                    "Secret-Key": self.secret_key,
                    "Content-Type": "application/json",
                },
                timeout=REQUEST_TIME_OUT_SECONDS,
            )
            runner_response.raise_for_status()
        except requests.exceptions.ConnectionError as exc:
            raise Error(
                MESSAGES.UPDATE_RUNNER_CONNECTION_ERROR_MESSAGE.format(
                    self.name, self.id
                )
            ) from exc
        except requests.exceptions.HTTPError as exc:
            if "ForbiddenError" in runner_response.text:
                raise Error(
                    MESSAGES.UPDATE_RUNNER_FORBIDDEN_ERROR_MESSAGE.format(
                        self.name, self.id, self.workspace_id
                    )
                ) from exc
            if runner_response.status_code != 405:
                raise Error(
                    MESSAGES.UPDATE_RUNNER_UNKNOWN_ERROR_MESSAGE.format(
                        self.name, self.id
                    )
                ) from exc
        except requests.exceptions.RequestException as exc:
            raise Error(
                MESSAGES.UPDATE_RUNNER_UNKNOWN_ERROR_MESSAGE.format(self.name, self.id)
            ) from exc
        finally:
            self.status.valid_secret_key = False

        try:
            self.status.status = runner_response.json()["status"]["overview"]
            self.status.suspended = runner_response.json()["suspended"]
            self.status.last_updated = datetime.now()
            self.status.valid_secret_key = True
            self.write_to_file()
        except Exception as exc:
            raise Error(
                MESSAGES.UPDATE_RUNNER_UNKNOWN_ERROR_MESSAGE.format(self.name, self.id)
            ) from exc

    def remove_from_file(self) -> None:
        """Remove Runner configuration from file."""
        try:
            with open(RUNNER_CONFIG_FILE_PATH, "r", encoding="utf-8") as file:
                runner_configs = json.load(file)
                for i, runner in enumerate(runner_configs):
                    if runner["id"] == self.id or runner["name"] == self.name:
                        del runner_configs[i]
                        break
            with open(RUNNER_CONFIG_FILE_PATH, "w", encoding="utf-8") as file:
                json.dump(runner_configs, file, indent=4, cls=DateTimeEncoder)
        except (IOError, json.JSONDecodeError) as exc:
            print(f"Error removing Runner config from {RUNNER_CONFIG_FILE_PATH}: {exc}")

    @classmethod
    def from_dict(cls, data: dict) -> RunnerConfig:
        """Create Runner configuration from dictionary.

        :param data (dict): Dictionary data.
        :return (RunnerConfig): Runner configuration.
        """
        runner_metadata = RunnerMetadata(**data.pop("runner_metadata", {}))
        system_specs = SystemSpecs(**data.pop("system_specs", {}))
        gpus = [GPUInfo(**gpu) for gpu in data.pop("gpus", [])]
        status = data.pop("status", {})
        last_updated_string = status.pop("last_updated", None)
        status_last_updated = (
            None
            if last_updated_string is None
            else datetime.fromisoformat(last_updated_string)
        )
        runs_status = [RunStatus(**run) for run in status.pop("runs", [])]
        runner_status = RunnerStatus(
            runs=runs_status, last_updated=status_last_updated, **status
        )

        return cls(
            runner_metadata=runner_metadata,
            system_specs=system_specs,
            gpus=gpus,
            status=runner_status,
            **data,
        )

    @property
    def is_updated(self) -> bool:
        """Check if Runner status is updated.

        :return (bool): True if updated, False otherwise.
        """
        if self.status.last_updated is None:
            return False
        present = datetime.now()
        return self.status.last_updated + timedelta(seconds=10) > present
