#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   test_artifact.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Datature Artifact API Test Cases
"""

import json
import unittest
from unittest.mock import ANY, MagicMock, patch

import msgspec

from datature.nexus import models
from datature.nexus.api.artifact import Artifact
from datature.nexus.client_context import ClientContext
from tests.unit.fixture.data import artifact_fixture

# pylint: disable=W0212


class TestArtifact(unittest.TestCase):
    """Datature Artifact API Resource Test Cases."""

    def __init__(self, *args, **kwargs):
        """init global variables."""
        unittest.TestCase.__init__(self, *args, **kwargs)

        context = ClientContext("secret_key", endpoint="http://localhost:8080")
        context.project_id = "project_id"
        context.requester._request = MagicMock()

        self.artifact = Artifact(context)

    def test_list(self):
        """Test list all artifacts."""
        self.artifact.list()

        self.artifact._context.requester._request.assert_called_once_with(
            "GET",
            "/projects/project_id/artifacts",
            ANY,
            query={"includeExports": False},
            request_params=None,
        )

    def test_retrieve(self):
        """Test retrieve an artifact."""
        self.artifact.get("artifact_id", include_exports=True)

        self.artifact._context.requester._request.assert_called_once_with(
            "GET",
            "/projects/project_id/artifacts/artifact_id",
            ANY,
            query={"includeExports": True},
            request_params=None,
        )

    def test_list_exported(self):
        """Test artifact exported models."""
        self.artifact.list_exported_models("artifact_id")

        self.artifact._context.requester._request.assert_called_once_with(
            "GET",
            "/projects/project_id/artifacts/artifact_id/exports",
            ANY,
            query=None,
            request_params=None,
        )

    @patch("datature.nexus.api.artifact.config")
    def test_export_model(self, patch_config):
        """Test export a artifact model."""
        patch_config.OPERATION_LOOPING_DELAY_SECONDS = 0
        self.artifact.create_export(
            "artifact_id", {"format": "TensorFlow"}, background=True
        )

        self.artifact._context.requester._request.assert_called_once_with(
            "POST",
            "/projects/project_id/artifacts/artifact_id/exports",
            ANY,
            request_body={"format": "TensorFlow"},
            query=None,
            request_params=None,
        )

    @patch("datature.nexus.api.artifact.utils")
    @patch("datature.nexus.api.artifact.zipfile")
    def test_download_exported_model(self, patch_zipfile, patch_utils):
        """Test download exported model."""
        patch_utils.download_files_to_tempfile = MagicMock()

        patch_zipfile.ZipFile.return_value.__enter__.return_value.namelist.return_value = [
            "datature-yolov8l.onnx",
            "datature-yolov8l.pt",
        ]

        self.artifact.list = MagicMock()

        self.artifact.list.return_value = msgspec.json.decode(
            json.dumps(artifact_fixture.artifacts_includes_exports_response),
            type=models.Artifacts,
        )

        self.artifact.download_exported_model("model_x4qq70769621y5rrv007447q7y5xw279")

    def test_download_exported_model_not_found(self):
        """Test download exported model with wrong model key."""
        self.artifact.list = MagicMock()

        self.artifact.list.return_value = msgspec.json.decode(
            json.dumps(artifact_fixture.artifacts_includes_exports_response),
            type=models.Artifacts,
        )

        try:
            self.artifact.download_exported_model("artifact_id")
        except:
            pass
