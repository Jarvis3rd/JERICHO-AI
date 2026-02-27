#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   test_annotation.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Datature Annotation API Test Cases
"""

import json
import unittest
from unittest.mock import ANY, MagicMock, patch

import msgspec

from datature.nexus import models
from datature.nexus.api.annotation.annotation import Annotation
from datature.nexus.api.annotation.import_session import ImportSession
from datature.nexus.client_context import ClientContext
from tests.unit.fixture.data import operation_fixture
from tests.unit.fixture.mock import MockResponse

# pylint: disable=W0212,W0702


class TestAnnotation(unittest.TestCase):
    """Datature Annotation API Resource Test Cases."""

    def __init__(self, *args, **kwargs):
        """init global variables."""
        unittest.TestCase.__init__(self, *args, **kwargs)

        context = ClientContext("secret_key", endpoint="http://localhost:8080")
        context.project_id = "project_id"
        context.requester._request = MagicMock()

        self.annotation = Annotation(context)
        # Mock operation
        self.annotation.operation.wait_until_done = MagicMock()

    def test_list(self):
        """Test retrieve a list of annotations."""
        self.annotation.list()

        self.annotation._context.requester._request.assert_called_once_with(
            "GET",
            "/projects/project_id/annotations",
            ANY,
            query={"limit": 100, "includeAttributes": False},
            request_params=None,
        )

    def test_create(self):
        """Test create an annotation."""
        self.annotation.create(
            {
                "asset_id": "asset_id",
                "tag": "tagName",
                "bound_type": "Rectangle",
                "bound": [
                    [0.425, 0.49382716049382713],
                    [0.425, 0.6419753086419753],
                    [0.6, 0.6419753086419753],
                    [0.6, 0.49382716049382713],
                ],
            }
        )

        self.annotation._context.requester._request.assert_called_once_with(
            "POST",
            "/projects/project_id/annotations",
            ANY,
            request_body={
                "assetId": "asset_id",
                "tag": "tagName",
                "boundType": "Rectangle",
                "bound": [
                    [0.425, 0.49382716049382713],
                    [0.425, 0.6419753086419753],
                    [0.6, 0.6419753086419753],
                    [0.6, 0.49382716049382713],
                ],
            },
            query=None,
            request_params=None,
        )

    def test_get(self):
        """Test retrieve an annotation."""
        self.annotation.get("annotation_id")

        self.annotation._context.requester._request.assert_called_once_with(
            "GET",
            "/projects/project_id/annotations/annotation_id",
            ANY,
            query={"includeAttributes": False},
            request_params=None,
        )

    def test_delete(self):
        """Test delete an annotation."""
        self.annotation.delete("annotation_id")

        self.annotation._context.requester._request.assert_called_once_with(
            "DELETE",
            "/projects/project_id/annotations/annotation_id",
            ANY,
        )

    def test_export_with_background(self):
        """Test export annotations."""
        self.annotation.create_export(
            {
                "format": "csv_fourcorner",
                "options": {"split_ratio": 0.4, "seed": 1337, "normalized": True},
            },
            background=True,
        )

        self.annotation._context.requester._request.assert_called_once_with(
            "POST",
            "/projects/project_id/annotationexports",
            ANY,
            query=None,
            request_body={
                "format": "csv_fourcorner",
                "options": {
                    "splitRatio": 0.4,
                    "seed": 1337,
                    "normalized": True,
                },
            },
            request_params=None,
        )

    def test_export(self):
        """Test export annotations."""
        self.annotation.create_export(
            {
                "format": "csv_fourcorner",
                "options": {
                    "split_ratio": 0.4,
                    "seed": 1337,
                },
            }
        )
        self.annotation._context.requester._request.side_effect = MockResponse(
            operation_fixture.pending_operation_response, 200
        )

        self.annotation.operation.wait_until_done.assert_called()

    @patch("datature.nexus.api.annotation.annotation.utils")
    @patch("datature.nexus.api.annotation.annotation.zipfile")
    def test_download_exported_file(self, patch_utils, patch_zipfile):
        """Test get export annotations."""
        patch_utils.download_files_to_tempfile = MagicMock()
        patch_zipfile.ZipFile = MagicMock()

        self.annotation._context.requester._request.return_value = msgspec.json.decode(
            json.dumps(operation_fixture.annotation_operation_response),
            type=models.ExportedAnnotations,
        )

        self.annotation.download_exported_file("op_id")

    def test_download_exported_file_error(self):
        """Test get export annotations."""
        self.annotation._context.requester._request.return_value = msgspec.json.decode(
            json.dumps(operation_fixture.annotation_export_error_response),
            type=models.ExportedAnnotations,
        )
        try:
            self.annotation.download_exported_file("op_id")
        except:
            pass

    def test_create_import_session(self):
        """Test export annotations."""
        import_session = self.annotation.create_import_session()

        assert isinstance(import_session, ImportSession)

    def test_list_import_sessions(self):
        """Test export annotations."""
        self.annotation.list_import_sessions()

        self.annotation._context.requester._request.assert_called_once_with(
            "GET",
            "/projects/project_id/annotationimportsessions",
            ANY,
            query=None,
            request_params=None,
        )

    def test_get_import_session(self):
        """Test export annotations."""
        self.annotation.get_import_session("import_session_id")

        self.annotation._context.requester._request.assert_called_once_with(
            "GET",
            "/projects/project_id/annotationimportsessions/import_session_id",
            ANY,
            query=None,
            request_params=None,
        )

    def test_get_import_session_logs(self):
        """Test export annotations."""
        self.annotation.get_import_session_logs("import_session_id")

        self.annotation._context.requester._request.assert_called_once_with(
            "GET",
            "/projects/project_id/annotationimportsessions/import_session_id/logs",
            ANY,
            query=None,
            request_params=None,
        )
