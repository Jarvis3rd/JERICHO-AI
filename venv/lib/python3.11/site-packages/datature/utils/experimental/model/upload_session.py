# !/usr/env/bin python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   upload_session.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Custom model upload session module.
"""
# pylint: disable=R1732

import logging
import os
import shutil
from contextlib import ContextDecorator

from datature.nexus import config, error
from datature.nexus.api.project import Project
from datature.nexus.client_context import RestContext
from datature.nexus.utils import utils

from .custom_model import CustomModel
from .models import UploadSession as UploadSessionModel

logger = logging.getLogger("datature-nexus")


class CustomModelUploadSession(RestContext, ContextDecorator):
    """Datature Asset Upload Session Class.

    :param project: An instance of Project.
    """

    def __init__(self, project: Project):
        super().__init__(project._context)
        self._http_session = utils.init_gcs_upload_session()
        self._custom_models = []
        self._file_name_map = {}
        self._tmp_dir: str = ".datature_custom_models"

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, exc_val, _exc_tb):
        """Context manager exit function. The function will be called
        once the code blocks inside the context manager have finished
        executing, or if an exception inside the context manager is raised."""
        if exc_val is not None:
            logger.warning("Upload session error occurred: %s", exc_val)
            raise error.Error(exc_val)

        if self._custom_models:
            responses = self._upload_models()
            self._clear_model_cache()
            return responses
        return []

    def add_model(self, model_folder_path: str):
        """Add a custom model to the upload session.

        :param model_folder_path: The path to the custom model directory.
        """
        assert os.path.exists(model_folder_path), (
            "The custom model directory does not exist.",
        )
        assert os.path.isdir(model_folder_path), (
            "The custom model path is not a directory. Please provide a directory path "
            "containing the `.pth` model file and `.yaml` config file.",
        )
        custom_model = CustomModel(model_folder_path, self._tmp_dir)
        zip_path, zip_metadata = custom_model.zip()
        self._custom_models.append(zip_metadata)
        self._file_name_map[zip_metadata["filename"]] = zip_path

    def _upload_models(self):
        """Upload the custom models to Nexus.

        :return: The responses from the upload session.
        """
        responses = []

        for custom_model in self._custom_models:
            upload_session_response: UploadSessionModel = self.requester.POST(
                f"/projects/{self.project_id}/modelimportsessions",
                request_body=custom_model,
                response_type=UploadSessionModel,
            )

            file_path = self._file_name_map[upload_session_response.metadata.filename]

            resp = self._http_session.request(
                method=upload_session_response.upload.method,
                url=upload_session_response.upload.url,
                headers=upload_session_response.upload.headers,
                data=open(file_path, "rb"),  # noqa
                timeout=config.REQUEST_TIME_OUT_SECONDS,
            )
            if resp.status_code == 200:
                responses.append(
                    f"Model {custom_model['filename']} uploaded successfully."
                )
            else:
                raise error.Error(
                    f"Failed to upload model {custom_model['filename']}. "
                    f"{resp.status_code} {resp.text}"
                )
        return responses

    def _clear_model_cache(self):
        """Clear the temporary model cache."""
        if os.path.exists(self._tmp_dir):
            shutil.rmtree(self._tmp_dir)
