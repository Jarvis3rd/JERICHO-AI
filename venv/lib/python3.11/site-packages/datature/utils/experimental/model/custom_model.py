# !/usr/env/bin python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   custom_model.py
@Author  :   Denzel Lee
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Custom model module.
"""

import base64
import os
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile

import crc32c

from datature.nexus import config

from .utils import verify_graph_module, verify_yaml_config


class CustomModel:
    """Custom model class."""

    def __init__(self, model_folder_path: str, tmp_dir: str) -> None:
        """Initialize the custom model.

        :param model_folder_path: Path to the model folder.
        :param tmp_dir: Path to the temporary directory.
        """
        self._model_folder_path = model_folder_path
        self._yaml_path = None
        self._graph_module_path = None
        self._tmp_dir = tmp_dir
        self._zip_path = os.path.join(self._tmp_dir, f"{str(uuid4())}.zip")

        self._verify_contents()

    def zip(self):
        """Zip the contents of the model folder.

        :return: Path to the zipped file and metadata.
        """
        os.makedirs(self._tmp_dir, exist_ok=True)

        with ZipFile(self._zip_path, "w", ZIP_DEFLATED) as zipf:
            zipf.write(
                self._yaml_path,
                os.path.relpath(self._yaml_path, self._model_folder_path),
            )
            zipf.write(
                self._graph_module_path,
                os.path.relpath(self._graph_module_path, self._model_folder_path),
            )

        return self._generate_metadata()

    def _calculate_file_hash(self, file_name: str):
        """Calculate and return the CRC32C hash of the given file contents.

        :param file_name: Path to the file.

        :return: CRC32C hash of the file contents.
        """
        file_hash = crc32c.CRC32CHash()

        with open(file_name, "rb") as file:
            chunk = file.read(config.FILE_CHUNK_SIZE)
            while chunk:
                file_hash.update(chunk)
                chunk = file.read(config.FILE_CHUNK_SIZE)

        return base64.b64encode(file_hash.digest()).decode("utf-8")

    def _verify_contents(self):
        """Verify the contents of the model folder.

        :raises FileNotFoundError:
            If the YAML configuration file or the PyTorch GraphModule file is missing.
        """
        all_files = os.listdir(self._model_folder_path)
        yaml_filename = next((f for f in all_files if f.endswith(".yaml")), None)
        if not yaml_filename:
            raise FileNotFoundError("no yaml file")
        graph_module_filename = next((f for f in all_files if f.endswith(".pth")), None)
        if not graph_module_filename:
            raise FileNotFoundError("no graph module file")

        self._yaml_path = os.path.join(self._model_folder_path, yaml_filename)
        self._graph_module_path = os.path.join(
            self._model_folder_path, graph_module_filename
        )

        verify_yaml_config(self._yaml_path)
        verify_graph_module(self._graph_module_path)

    def _generate_metadata(self):
        """Generate metadata for the custom model.

        :return: Path to the zipped file and metadata.
        """

        zip_metadata = {
            "filename": os.path.basename(self._zip_path),
            "size": os.path.getsize(self._zip_path),
            "crc32c": self._calculate_file_hash(self._zip_path),
        }
        return self._zip_path, zip_metadata
