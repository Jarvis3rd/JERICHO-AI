#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   test_requester.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Datature HTTP Resource Test Cases
"""
# pylint: disable=W0703,W0012,W0212

import json
import unittest

import msgspec
from requests import Session

from datature.nexus import models
from datature.nexus.utils import utils


class TestUtils(unittest.TestCase):
    """Datature Utils Test Cases."""

    def test_find_all_annotations_files(self):
        """Test find_all_annotations_files."""

        # test find all annotations files
        files = utils.find_all_annotations_files("tests/fixture/data")
        assert len(files) == 0

    def test_get_exportable_annotations_formats(self):
        """Test get_exportable_annotations_formats."""

        # test get exportable annotations formats
        formats = utils.get_exportable_annotations_formats("Classification")
        assert len(formats) == 2

        formats = utils.get_exportable_annotations_formats("Keypoint")
        assert len(formats) == 1

        formats = utils.get_exportable_annotations_formats("")
        assert len(formats) == 10

    def test_init_gcs_upload_session(self):
        """Test init_gcs_upload_session."""

        # test init gcs upload session
        session = utils.init_gcs_upload_session()

        assert isinstance(session, Session)

    def test_get_download_path(self):
        """Test get_download_path."""

        # test get download path
        path = utils.get_download_path("../test")
        assert "test" in str(path)

        path = utils.get_download_path()
        assert "datature" in str(path)

    def test_download_files_to_tempfile(self):
        """Test download_files_to_tempfile."""

        # test get download path
        utils.download_files_to_tempfile(
            msgspec.json.decode(
                json.dumps(
                    {
                        "method": "GET",
                        "url": "https://cdn.jsdelivr.net/npm/bootstrap@3.3.7/dist/js/bootstrap.min.js",
                        "expiryDate": 1701755214003,
                    }
                ),
                type=models.DownloadSignedUrl,
            )
        )
