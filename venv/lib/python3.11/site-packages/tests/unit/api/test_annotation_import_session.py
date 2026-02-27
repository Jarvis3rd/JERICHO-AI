#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   test_annotation_import_session.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Datature Asset Upload Session API Test Cases
"""
# pylint: disable=W0703,R0913,W0613,W0212

import json
import unittest
from unittest.mock import ANY, MagicMock, patch

import msgspec

from datature.nexus import models
from datature.nexus.api.annotation.import_session import ImportSession
from datature.nexus.client_context import ClientContext
from datature.nexus.error import Error
from tests.unit.fixture.data import operation_fixture


class TestAnnotationImportSession(unittest.TestCase):
    """Datature Annotation Import Session API Resource Test Cases."""

    def __init__(self, *args, **kwargs):
        """init global variables."""
        unittest.TestCase.__init__(self, *args, **kwargs)

        context = ClientContext("secret_key", endpoint="http://localhost:8080")
        context.project_id = "project_id"
        context.requester._request = MagicMock()
        self.context = context

    def test_add_with_file_not_exist(self):
        """Test not existed annotation to import session."""
        import_session = ImportSession(self.context)

        try:
            import_session.add_path("assetPath")
        except Exception as exception:
            assert isinstance(exception, FileNotFoundError)

    def test_get_logs(self):
        """Test get_logs ."""
        import_session = ImportSession(self.context)

        import_session.import_session_id = "import_session_id"

        import_session.get_logs()

        import_session._context.requester._request.assert_called_with(
            "GET",
            "/projects/project_id/annotationimportsessions/import_session_id/logs",
            ANY,
            query=None,
            request_params=None,
        )

    def test_patch_status(self):
        """Test patch_status function."""
        import_session = ImportSession(self.context)

        import_session.import_session_id = "import_session_id"

        import_session._patch_status(
            {
                "condition": "FilesProcessed",
                "status": "FailedReach",
            }
        )

        import_session._context.requester._request.assert_called_with(
            "PATCH",
            "/projects/project_id/annotationimportsessions/import_session_id",
            ANY,
            query=None,
            request_params=None,
            request_body={
                "status": {
                    "conditions": [
                        {
                            "condition": "FilesProcessed",
                            "status": "FailedReach",
                        }
                    ]
                }
            },
        )

    def test_import_session_length(self):
        """Test len(import_session) function."""
        import_session = ImportSession(self.context)

        import_session.filenames = {"file1", "file2"}

        assert len(import_session) == 2

    @patch("datature.nexus.api.annotation.import_session.open")
    @patch("datature.nexus.api.annotation.import_session.path")
    @patch("datature.nexus.api.annotation.import_session.utils")
    def test_add_path_to_import_session(
        self, patched_utils, patched_path, patched_open
    ):
        """Test import session."""
        import_session = ImportSession(self.context)

        patched_open.__enter__.return_value.__len__.return_value = 100
        patched_path.isdir.return_value = True
        patched_path.basename.side_effect = ["file1", "file2"]
        patched_utils.find_all_annotations_files.return_value = ["file1", "file2"]

        import_session._calculate_file_hash = MagicMock()
        import_session._calculate_file_hash.return_value = 1234

        import_session.add_path("assetPath")

    @patch("datature.nexus.api.annotation.import_session.open")
    @patch("datature.nexus.api.annotation.import_session.path")
    @patch("datature.nexus.api.annotation.import_session.utils")
    def test_duplicate_path_to_import_session(
        self, patched_utils, patched_path, patched_open
    ):
        """Test import session."""
        import_session = ImportSession(self.context)

        patched_open.__enter__.return_value.__len__.return_value = 100
        patched_path.isdir.return_value = True
        patched_path.basename.side_effect = ["file1", "file1"]
        patched_utils.find_all_annotations_files.return_value = ["file1", "file2"]

        import_session._calculate_file_hash = MagicMock()
        import_session._calculate_file_hash.return_value = 1234

        try:
            import_session.add_path("assetPath")
        except Exception as exception:
            assert isinstance(exception, Error)

    @patch("datature.nexus.api.annotation.import_session.open")
    @patch("datature.nexus.api.annotation.import_session.path")
    @patch("datature.nexus.api.annotation.import_session.utils")
    def test_max_file_path_to_import_session(
        self, patched_utils, patched_path, patched_open
    ):
        """Test import session."""
        import_session = ImportSession(self.context)
        import_session.filenames = {"filename1", "filename2"}
        import_session.max_files_per_session = 1

        patched_path.isdir.return_value = True
        patched_utils.find_all_annotations_files.return_value = ["file1", "file2"]

        try:
            import_session.add_path("assetPath")
        except Exception as exception:
            assert isinstance(exception, Error)

    @patch("datature.nexus.api.annotation.import_session.open")
    @patch("datature.nexus.api.annotation.import_session.path")
    @patch("datature.nexus.api.annotation.import_session.utils")
    def test_background_path_to_import_session(
        self, patched_utils, patched_path, patched_open
    ):
        """Test import session."""
        import_session = ImportSession(self.context)
        import_session._upload_current_batch = MagicMock()

        patched_open.__enter__.return_value.__len__.return_value = 100
        import_session.max_files_per_batch = 1
        patched_path.isdir.return_value = True
        patched_path.basename.side_effect = ["file1", "file2"]
        patched_utils.find_all_annotations_files.return_value = ["file1", "file2"]

        import_session._calculate_file_hash = MagicMock()
        import_session._calculate_file_hash.return_value = 1234

        import_session.add_path("assetPath")
        import_session._upload_current_batch.assert_called()

    def test_add_bytes_max_files_per_session(self):
        """Test import session add bytes."""
        import_session = ImportSession(self.context)
        import_session._upload_current_batch = MagicMock()
        import_session.filenames = {"filename1"}

        import_session._calculate_file_hash = MagicMock()
        import_session._calculate_file_hash.return_value = 1234

        import_session.max_files_per_session = 1
        try:
            import_session.add_bytes(b"assetPath", "file1")
        except Exception as exception:
            assert isinstance(exception, Error)

    def test_add_bytes_duplicate_file(self):
        """Test import session add duplicate file bytes."""
        import_session = ImportSession(self.context)
        import_session._upload_current_batch = MagicMock()
        import_session.filenames = {"filename1"}

        import_session._calculate_file_hash = MagicMock()
        import_session._calculate_file_hash.return_value = 1234

        try:
            import_session.add_bytes(b"assetPath", "filename1")
        except Exception as exception:
            assert isinstance(exception, Error)

    def test_add_bytes(self):
        """Test import session add file bytes."""
        import_session = ImportSession(self.context)
        import_session._upload_current_batch = MagicMock()

        import_session._calculate_file_hash = MagicMock()
        import_session._calculate_file_hash.return_value = 1234

        import_session.add_bytes(b"assetPath", "filename1")

    def test_add_bytes_with_upload_current_batch(self):
        """Test import session add file bytes."""
        import_session = ImportSession(self.context)
        import_session._upload_current_batch = MagicMock()
        import_session.max_files_per_batch = 1
        import_session.max_bytes_per_batch = 1

        import_session._calculate_file_hash = MagicMock()
        import_session._calculate_file_hash.return_value = 1234

        import_session.add_bytes(b"assetPath", "filename1")
        import_session._upload_current_batch.assert_called()

    def test_calculate_file_hash(self):
        """Test calculate file hash."""
        import_session = ImportSession(self.context)

        c2c32 = import_session._calculate_file_hash(b"assetPath")

        assert c2c32 == "EUvjmg=="

    def test_wait_until_done(self):
        """Test wait until done."""
        import_session = ImportSession(self.context)
        import_session.import_session_id = "import_session_id"

        import_session._context.requester._request.return_value = msgspec.json.decode(
            json.dumps(operation_fixture.annotation_import_finished_response),
            type=models.ImportSession,
        )

        import_session.wait_until_done()

    @patch("datature.nexus.api.annotation.import_session.config")
    def test_wait_until_done_with_timeout(self, patched_config):
        """Test wait until done."""
        import_session = ImportSession(self.context)
        import_session.import_session_id = "import_session_id"

        patched_config.OPERATION_LOOPING_DELAY_SECONDS = 0
        patched_config.OPERATION_LOOPING_TIMEOUT_SECONDS = 2

        import_session._context.requester._request.return_value = msgspec.json.decode(
            json.dumps(operation_fixture.annotation_import_running_response),
            type=models.ImportSession,
        )

        res = import_session.wait_until_done()
        assert res is False

    def test_wait_until_done_with_error(self):
        """Test wait until done."""
        import_session = ImportSession(self.context)
        import_session.import_session_id = "import_session_id"

        import_session._context.requester._request.return_value = msgspec.json.decode(
            json.dumps(operation_fixture.annotation_import_errored_response),
            type=models.ImportSession,
        )
        try:
            import_session.wait_until_done()
        except Exception as exception:
            assert isinstance(exception, Error)
