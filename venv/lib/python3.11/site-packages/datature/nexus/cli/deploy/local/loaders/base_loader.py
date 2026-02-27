#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   base_loader.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Base class for model loaders.
"""

# pylint: disable=R0902,W0718

import logging
import os
import queue
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Tuple

import requests

from datature.nexus.cli.deploy.local.consts import DEFAULT_MODEL_DIR
from datature.nexus.cli.deploy.local.utils.common import start_spinner
from datature.nexus.cli.deploy.local.utils.inference import ModelExtension
from datature.nexus.cli.deploy.local.utils.management_api import ManagementAPIClient
from datature.nexus.cli.deploy.local.utils.model import Model
from datature.nexus.error import Error
from datature.nexus.models import LocalArtifact

logger = logging.getLogger("datature-nexus")


class BaseLoader(ABC):
    """Base class for model loaders."""

    _artifact_id: str
    _model_format: str
    _execution_provider: str
    _management_api_client: ManagementAPIClient
    _model_dir: Path
    _model_path: str
    _label_map_path: str
    _model: Model

    def __init__(
        self,
        artifact_id: str,
        execution_provider: str,
        model_format: str,
        management_api_client: ManagementAPIClient,
    ) -> None:
        """Initialize loader."""
        self._artifact_id = artifact_id
        self._execution_provider = execution_provider
        self._model_format = model_format
        self._management_api_client = management_api_client

        self._model_dir = DEFAULT_MODEL_DIR / self._artifact_id
        self._model_path = ""
        self._label_map_path = ""

        self._get_model()

    @abstractmethod
    def load(self, message_queue: queue.Queue = queue.Queue()):
        """Load format-specific model.

        Raises:
            ValueError: Abstract function needs to be implemented.
        """
        raise ValueError("Abstract function needs to be implemented")

    def _get_model(self) -> None:
        """Fetch model from Datature Nexus or local directory.

        Raises:
            InvalidModelException: Error loading model.
        """
        if not os.path.isdir(self._model_dir):
            self._get_model_from_api()

        else:
            try:
                self._get_model_from_local()
            except Exception as exc:
                print(f"Error fetching {self.model_format} model locally: {exc}")
                print(
                    f"Attempting to fetch {self.model_format} model from Datature Nexus..."
                )
                self._get_model_from_api()

    def _get_model_from_api(self) -> None:
        """Fetch model from Datature Nexus."""
        try:
            exported_model = self._export_model()

            local_model = self._download_model(exported_model)

            self._model_path = os.path.join(
                local_model.download_path, local_model.model_filename
            )

            if not os.path.exists(self._model_path):
                raise FileNotFoundError

        except FileNotFoundError as exc:
            raise Error(f"Model file path not found: {self._model_path}!") from exc

        except Exception as exc:
            raise Error(f"Error fetching {self.model_format} model: {exc}") from exc

        try:
            self._label_map_path = os.path.join(
                local_model.download_path, local_model.label_filename
            )

            if not os.path.exists(self._label_map_path):
                raise FileNotFoundError

        except FileNotFoundError as exc:
            raise Error(
                f"Label map file path not found: {self._label_map_path}!"
            ) from exc

        except OSError as exc:
            raise Error("Error getting label map file path") from exc

    def _get_model_from_local(self) -> None:
        """Fetch model from local directory."""
        model_filename = next(
            (
                f
                for f in os.listdir(self._model_dir)
                if any(f.endswith(ext.value) for ext in ModelExtension)
            ),
            None,
        )

        if model_filename is None:
            raise FileNotFoundError(
                f"Model file could not be detected in {self._model_dir}"
            )

        try:
            self._model_path = os.path.join(self._model_dir, model_filename)

            if not os.path.exists(self._model_path):
                raise FileNotFoundError(
                    f"Model file path not found: {self._model_path}"
                )

        except FileNotFoundError as exc:
            raise Error(f"Model file path not found: {self._model_path}") from exc

        except OSError as exc:
            raise Error("Error getting model file path") from exc

        except Exception as exc:
            raise Error(f"Error fetching {self.model_format} model: {exc}") from exc

        try:
            label_map_filename = next(
                (
                    file_name
                    for file_name in os.listdir(self._model_dir)
                    if (file_name.endswith(".pbtxt") or file_name.endswith(".txt"))
                    and "label" in file_name
                ),
                None,
            )

            if label_map_filename is None:
                raise FileNotFoundError

            self._label_map_path = os.path.join(self._model_dir, label_map_filename)

            if not os.path.exists(self._label_map_path):
                raise FileNotFoundError

        except FileNotFoundError as exc:
            raise Error(
                f"Label map file path not found: {self._label_map_path}"
            ) from exc

        except OSError as exc:
            raise Error("Error getting label map file path") from exc

    @start_spinner
    def _export_model(self, message_queue: queue.Queue = queue.Queue()):
        """Export model from Datature Nexus."""
        message_queue.put("Exporting model...")

        while True:
            try:
                exports = (
                    self._management_api_client.project.artifacts.list_exported_models(
                        self._artifact_id
                    )
                )

            except requests.exceptions.HTTPError as exc:
                raise Error(
                    f"Error finding model artifact {self._artifact_id}: {exc.response.text}"
                ) from exc

            exported_model = next(
                (model for model in exports if model.format == self._model_format),
                None,
            )

            if exported_model and exported_model.status == "Error":
                raise Error(
                    "Error exporting model. Please try again later or contact"
                    "support at support@datature.io."
                )

            if not exported_model or exported_model.status != "Finished":
                try:
                    exported_model = (
                        self._management_api_client.project.artifacts.create_export(
                            self._artifact_id,
                            export_options={"format": self._model_format},
                        )
                    )

                except requests.exceptions.HTTPError as exc:
                    # Wait and retry if the model export is already in progress
                    if exc.response.status_code == 409:
                        time.sleep(5)
                        continue

                    raise Error(f"Error exporting model: {exc.response.text}") from exc

            break

        return exported_model, "Model exported successfully"

    @start_spinner
    def _download_model(
        self, exported_model, message_queue: queue.Queue = queue.Queue()
    ) -> Tuple[LocalArtifact, str]:
        """Download model from Datature Nexus."""
        message_queue.put("Downloading model...")

        try:
            downloaded_model = (
                self._management_api_client.project.artifacts.download_exported_model(
                    exported_model["id"], self._model_dir
                )
            )

        except requests.exceptions.HTTPError as exc:
            raise Error(
                f"Server error when downloading model: {exc.response.text}"
            ) from exc

        except Exception as exc:
            raise Error(f"Error downloading model: {exc}") from exc

        return downloaded_model, "Model downloaded successfully"

    @property
    def model_format(self) -> str:
        """Get model format."""
        return self._model_format

    @model_format.setter
    def model_format(self, model_format) -> None:
        """Set model format."""
        self._model_format = model_format

    @property
    def model(self) -> Model:
        """Get loaded model."""
        return self._model

    @model.setter
    def model(self, model) -> None:
        """Set loaded model."""
        self._model = model
