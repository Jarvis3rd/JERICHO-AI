#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   test_asset.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Datature Asset API Test Cases
"""

import unittest
from unittest.mock import ANY, MagicMock

from datature.nexus.api.asset.asset import Asset
from datature.nexus.api.asset.upload_session import UploadSession
from datature.nexus.client_context import ClientContext

# pylint: disable=W0212


class TestAsset(unittest.TestCase):
    """Datature Asset API Resource Test Cases."""

    def __init__(self, *args, **kwargs):
        """init global variables."""
        unittest.TestCase.__init__(self, *args, **kwargs)

        context = ClientContext("secret_key", endpoint="http://localhost:8080")
        context.project_id = "project_id"
        context.requester._request = MagicMock()

        self.asset = Asset(context)

    def test_list(self):
        """Test retrieve a list of assets."""
        self.asset.list()

        self.asset._context.requester._request.assert_called_once_with(
            "GET",
            "/projects/project_id/assets",
            ANY,
            query={"limit": 100},
            request_params=None,
        )

    def test_list_pagination(self):
        """Test retrieve a list of assets with pagination."""
        self.asset.list({"page": "nextPage", "limit": 5})

        self.asset._context.requester._request.assert_called_once_with(
            "GET",
            "/projects/project_id/assets",
            ANY,
            query={"page": "nextPage", "limit": 5},
            request_params=None,
        )

    def test_list_filters(self):
        """Test retrieve a list of assets with filters."""
        self.asset.list(filters={"status": "None"})

        self.asset._context.requester._request.assert_called_once_with(
            "GET",
            "/projects/project_id/assets",
            ANY,
            query={"limit": 100, "status": "None"},
            request_params=None,
        )

    def test_get(self):
        """Test get an Asset."""
        self.asset.get("asset_id")

        self.asset._context.requester._request.assert_called_once_with(
            "GET",
            "/projects/project_id/assets/asset_id",
            ANY,
            query=None,
            request_params=None,
        )

    def test_update(self):
        """Test update an asset."""
        self.asset.update("asset_id", {"status": "None"})

        self.asset._context.requester._request.assert_called_once_with(
            "PATCH",
            "/projects/project_id/assets/asset_id",
            ANY,
            request_body={"status": "None"},
            query=None,
            request_params=None,
        )

    def test_update_custom_metadata(self):
        """Test update an asset custom metadata."""
        self.asset.update("asset_id", {"custom_metadata": "s"})

        self.asset._context.requester._request.assert_called_once_with(
            "PATCH",
            "/projects/project_id/assets/asset_id",
            ANY,
            request_body={"customMetadata": "s"},
            query=None,
            request_params=None,
        )

    def test_delete(self):
        """Test delete an asset."""
        self.asset.delete("asset_id")

        self.asset._context.requester._request.assert_called_once_with(
            "DELETE", "/projects/project_id/assets/asset_id", ANY
        )

    def test_upload_session(self):
        """Test create Asset."""
        upload_session = self.asset.create_upload_session()

        assert isinstance(upload_session, UploadSession)

    def test_groups(self):
        """Test retrieve assets statistic."""
        self.asset.list_groups()

        self.asset._context.requester._request.assert_called_once_with(
            "GET",
            "/projects/project_id/assetgroups",
            ANY,
            query={"group": None},
            request_params=None,
        )
