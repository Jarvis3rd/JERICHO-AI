#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   test_asset_upload_session.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Datature Asset Upload Session API Test Cases
"""
# pylint: disable=W0703,R0913,W0613,W0212

import json
import unittest
from unittest.mock import MagicMock, patch

import msgspec

from datature.nexus import models
from datature.nexus.api.asset.upload_session import UploadSession
from datature.nexus.client_context import ClientContext
from datature.nexus.error import Error
from tests.unit.fixture.data import projects_fixture, upload_session_fixture


class TestAssetUploadSession(unittest.TestCase):
    """Datature Asset Upload Session API Resource Test Cases."""

    def __init__(self, *args, **kwargs):
        """init global variables."""
        unittest.TestCase.__init__(self, *args, **kwargs)

        context = ClientContext("secret_key", endpoint="http://localhost:8080")
        context.project_id = "project_id"
        context.requester._request = MagicMock()
        self.context = context

    def test_add_with_file_not_exist(self):
        """Test add asset to upload with ."""
        upload_session = UploadSession(self.context)

        try:
            upload_session.add_path("assetPath")
        except Exception as exception:
            assert isinstance(exception, Error)

    @patch("datature.nexus.api.asset.upload_session.config")
    @patch("datature.nexus.api.asset.upload_session.filetype")
    @patch("datature.nexus.api.asset.upload_session.struct")
    @patch("datature.nexus.api.asset.upload_session.crc32c")
    @patch("datature.nexus.api.asset.upload_session.path")
    @patch("datature.nexus.api.asset.upload_session.open")
    def test_add_with_duplicated_file(
        self, patch_open, patch_path, crc32c, struct, filetype, patch_config
    ):
        """Test add asset to upload with duplicated file."""
        patch_config.ASSET_UPLOAD_SESSION_BATCH_SIZE = 100

        upload_session = UploadSession(self.context)
        upload_session.file_name_map = {"assetName": {"path": "file_path"}}

        struct.unpack.return_value = [-384617082]
        patch_path.basename.return_value = "assetName"
        patch_path.getsize.return_value = 5613

        mock_guess = MagicMock()
        mock_guess.mime = "image/jpeg"
        filetype.guess.return_value = mock_guess

        try:
            with upload_session as upload_session:
                upload_session.add_path("assetPath")
        except Exception as exception:
            assert isinstance(exception, Error)

    @patch("datature.nexus.api.asset.upload_session.config")
    @patch("datature.nexus.api.asset.upload_session.filetype")
    @patch("datature.nexus.api.asset.upload_session.path")
    @patch("datature.nexus.api.asset.upload_session.struct")
    @patch("datature.nexus.api.asset.upload_session.crc32c")
    @patch("datature.nexus.api.asset.upload_session.open")
    def test_add_with_file_not_supported(
        self, patch_open, crc32c, struct, path, filetype, patch_config
    ):
        """Test add asset to upload with file not supported."""
        patch_config.ASSET_UPLOAD_SESSION_BATCH_SIZE = 100

        upload_session = UploadSession(self.context)

        struct.unpack.return_value = [-384617082]
        path.basename.return_value = "assetName"
        path.getsize.return_value = 5613

        mock_guess = MagicMock()
        mock_guess.mime = ""
        filetype.guess.return_value = mock_guess

        try:
            with upload_session as upload_session:
                upload_session.add_path("assetPath")
        except Exception as exception:
            assert isinstance(exception, Error)

    @patch("datature.nexus.api.asset.upload_session.config")
    @patch("datature.nexus.api.asset.upload_session.filetype")
    @patch("datature.nexus.api.asset.upload_session.path")
    @patch("datature.nexus.api.asset.upload_session.struct")
    @patch("datature.nexus.api.asset.upload_session.crc32c")
    @patch("datature.nexus.api.asset.upload_session.open")
    def test_add_with_file(
        self, patch_open, crc32c, struct, path, filetype, patch_config
    ):
        """Test add asset to upload with file."""
        patch_config.ASSET_UPLOAD_SESSION_BATCH_SIZE = 100
        upload_session = UploadSession(self.context)

        struct.unpack.return_value = [-384617082]
        path.basename.return_value = "assetName"
        path.getsize.return_value = 5613

        mock_guess = MagicMock()
        mock_guess.mime = "image/jpeg"
        filetype.guess.return_value = mock_guess

        upload_session.add_path("assetPath")

    def test_start_with_empty_assets(self):
        """Test upload with empty assets ."""
        upload_session = UploadSession(self.context, ["main"])
        try:
            with upload_session as upload_session:
                upload_session.add_path("assetPath")
        except Exception as exception:
            assert isinstance(exception, Error)

    @patch("datature.nexus.api.asset.upload_session.config")
    @patch("datature.nexus.api.asset.upload_session.open")
    def test_start(self, patch_open, patch_config):
        """Test start upload with empty assets ."""
        patch_config.ASSET_UPLOAD_SESSION_BATCH_SIZE = 100

        upload_session = UploadSession(self.context, ["main"], background=True)
        upload_session._upload_assets = MagicMock()

        upload_session.assets = [
            {
                "filename": "test.jpeg",
                "mime": "image/jpeg",
                "size": 5613,
                "crc32c": -384617082,
            }
        ]
        upload_session.file_name_map = {"test.jpeg": {"path": "file_path"}}

        upload_session._context.requester._request.return_value = msgspec.json.decode(
            json.dumps(upload_session_fixture.upload_assets_response),
            type=models.UploadSession,
        )

        upload_session.assets = [
            {
                "filename": "test.jpeg",
                "mime": "image/jpeg",
                "size": 5613,
                "crc32c": -384617082,
            }
        ]

        with upload_session as upload_session:
            pass

    @patch("datature.nexus.api.asset.upload_session.open")
    def test_start_with_background(self, patch_open):
        """Test start upload with wait server process."""
        upload_session = UploadSession(self.context, ["main"])

        upload_session.operation.wait_until_done = MagicMock()
        upload_session._upload_assets = MagicMock()

        upload_session.assets = [
            {
                "filename": "test.jpeg",
                "mime": "image/jpeg",
                "size": 5613,
                "crc32c": -384617082,
            }
        ]
        upload_session.file_name_map = {"test.jpeg": {"path": "file_path"}}

        upload_session._context.requester._request.return_value = msgspec.json.decode(
            json.dumps(upload_session_fixture.upload_assets_response),
            type=models.UploadSession,
        )

        upload_session.assets = [
            {
                "filename": "test.jpeg",
                "mime": "image/jpeg",
                "size": 5613,
                "crc32c": -384617082,
            }
        ]

        with upload_session as upload_session:
            pass

        upload_session.operation.wait_until_done.assert_called()

    def test_get_operation_ids(self):
        """Test get_operation_ids function."""
        upload_session = UploadSession(self.context, ["main"])
        upload_session.operation_ids = ["id1", "id2"]

        operation_ids = upload_session.get_operation_ids()

        assert operation_ids == ["id1", "id2"]

    def test_import_session_length(self):
        """Test len(upload_session) function."""
        upload_session = UploadSession(self.context, ["main"])
        upload_session.file_name_map = {
            "filename": {
                "path": "path",
            }
        }

        assert len(upload_session) == 1
