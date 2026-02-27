#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   upload_session.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Datature Asset Upload Session
"""
# pylint: disable=E1102,R0914,R0912,R0902,R1732

import base64
import concurrent.futures
import logging
import threading
import time
from contextlib import ContextDecorator
from datetime import datetime, timedelta
from os import path

import crc32c

from datature.nexus import config, error, models
from datature.nexus.api.types import OperationStatusOverview
from datature.nexus.client_context import ClientContext, RestContext
from datature.nexus.utils import utils

logger = logging.getLogger("datature-nexus")


class ImportSession(RestContext, ContextDecorator):
    """
    Datature Annotation Import Session Class.

    :param background: A flag indicating whether
        the import should run in the background. Default is False.
    """

    def __init__(self, client_context: ClientContext, background=False):
        """Initialize the API Resource."""
        super().__init__(client_context)
        self.max_files_per_session = config.ANNOTATION_IMPORT_SESSION_MAX_SIZE
        self.max_files_per_batch = config.ANNOTATION_IMPORT_SESSION_BATCH_SIZE
        self.max_bytes_per_batch = config.ANNOTATION_IMPORT_SESSION_BATCH_BYTES

        self._local = threading.local()

        import_session = self.requester.POST(
            f"/projects/{self.project_id}/annotationimportsessions",
            response_type=models.ImportSession,
        )

        self.import_session_id = import_session.id
        self.background = background

        self.current_batch = []
        self.annotations_contents_map = {}
        self.current_batch_bytes_size = 0
        self.filenames = set()

    def _init_http_session(self):
        """Init gcs upload session."""
        self._local.http_session = utils.init_gcs_upload_session()

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, exc_val, _exc_tb):
        """
        Exit function.
        The function will be called if an exception is raised inside the context manager
        """
        if exc_val is not None:
            # Error handling, patch import session status
            self._patch_status(
                {
                    "condition": "FilesProcessed",
                    "status": "FailedReach",
                }
            )
            logger.warning(
                "Import session error existed, no file will be updated: %s", exc_val
            )
            return True

        # Patch import session status
        self._patch_status(
            {
                "condition": "FilesInserted",
                "status": "Reached",
            }
        )

        if self.background:
            return True

        # Looping check import session status
        return self.wait_until_done()

    def __len__(self):
        """Overwrite len function."""
        return len(self.filenames)

    def _calculate_file_hash(self, file_contents):
        """Calculate and return the CRC32C hash of the given file contents."""
        file_hash = crc32c.CRC32CHash()
        file_hash.update(file_contents)
        return base64.b64encode(file_hash.digest()).decode("utf-8")

    def add_bytes(self, file_bytes: bytes, filename: str):
        """
        Attach file in bytes to import session

        :param file_bytes: The file bytes.
        :param filename: The file name.
        :returns: None
        """
        if len(self.filenames) + 1 > self.max_files_per_session:
            raise error.Error(
                f"One import session allow max {self.max_files_per_session} files."
            )
        if filename in self.filenames:
            raise error.Error(
                f"Filename {filename} already exists in this import session."
            )

        # Push the file to the current batch
        self.filenames.add(filename)
        self.current_batch_bytes_size += len(file_bytes)

        self.annotations_contents_map[filename] = {
            "file_type": "bytes",
            "contents": file_bytes,
        }

        self.current_batch.append(
            {
                "filename": filename,
                "size": len(file_bytes),
                "crc32c": self._calculate_file_hash(file_bytes),
            }
        )

        self._upload_current_batch()

    def add_path(self, file_path: str):
        """
        Attach file path or folders to import session

        :param file_path: The file or folder path.
        :returns: None
        """
        if path.isdir(file_path):
            file_path_list = utils.find_all_annotations_files(file_path)
        else:
            file_path_list = [file_path]

        if len(self.filenames) + len(file_path_list) > self.max_files_per_session:
            raise error.Error(
                f"One import session allow max {self.max_files_per_session} files."
            )

        for _file_path in file_path_list:
            filename = path.basename(_file_path)

            if filename in self.filenames:
                raise error.Error(
                    f"Filename {filename} already exists in this import session."
                )

            self.filenames.add(filename)
            file_size = path.getsize(_file_path)

            file_hash = crc32c.CRC32CHash()

            with open(_file_path, "rb") as file:
                chunk = file.read(config.FILE_CHUNK_SIZE)
                while chunk:
                    file_hash.update(chunk)
                    chunk = file.read(config.FILE_CHUNK_SIZE)

            self.annotations_contents_map[filename] = {
                "file_type": "path",
                "contents": _file_path,
            }

            self.current_batch.append(
                {
                    "filename": filename,
                    "size": file_size,
                    "crc32c": base64.b64encode(file_hash.digest()).decode("utf-8"),
                }
            )

        self._upload_current_batch()

    def wait_until_done(self):
        """
        Wait for all operations to be done.
            This function only works when background is set to False.
        """
        elapsed_time = datetime.now() + timedelta(
            seconds=config.OPERATION_LOOPING_TIMEOUT_SECONDS
        )

        while True:
            import_session = self.requester.GET(
                f"/projects/{self.project_id}/annotationimportsessions/{self.import_session_id}",
                response_type=models.ImportSession,
            )

            logger.debug("Looping import sessions status: %s", import_session)

            if import_session.status.overview == OperationStatusOverview.ERRORED.value:
                raise error.BadRequestError(
                    f"Error: Please run 'project.annotations.get_import_session_logs"
                    f'("{self.import_session_id}")\' in your Python shell to check the error details.'
                )

            if import_session.status.overview == OperationStatusOverview.FINISHED.value:
                return True

            # if the operation has not finished when the timeouts
            if elapsed_time < datetime.now():
                logger.warning(
                    "Operation timeout: Please run "
                    "'project.annotations.get_import_session_logs(\"%s\")'"
                    " in your Python shell to check the error details.",
                    self.import_session_id,
                )
                return False

            time.sleep(config.OPERATION_LOOPING_DELAY_SECONDS)

    def _upload_file(self, filename, signed_url):
        """Upload file to GCS."""
        file_info = self.annotations_contents_map[filename]
        file_type = file_info["file_type"]
        file_contents = file_info["contents"]

        self._local.http_session.request(
            signed_url.get("method"),
            signed_url.get("url"),
            headers=signed_url.get("headers"),
            data=file_contents if file_type == "bytes" else open(file_contents, "rb"),
            timeout=config.REQUEST_TIME_OUT_SECONDS,
        )

        return filename

    def _upload_current_batch(self):
        batch_segments = [
            self.current_batch[i : i + self.max_files_per_batch]
            for i in range(0, len(self.current_batch), self.max_files_per_batch)
        ]

        for segment in batch_segments:
            # Add files to import session
            logger.debug("Start uploading files to import session: %s", segment)

            files_res = self.requester.POST(
                f"""/projects/{self.project_id}/annotationimportsessions/{
                    self.import_session_id}/files""",
                request_body={"files": segment},
                response_type=models.InsertImportSessionFiles,
            )

            logger.debug("Start uploading files to import session: %s", files_res)

            with concurrent.futures.ThreadPoolExecutor(
                initializer=self._init_http_session
            ) as executor:
                futures = [
                    executor.submit(
                        self._upload_file, upload_file.filename, upload_file.upload
                    )
                    for upload_file in files_res.files
                ]

                for future in concurrent.futures.as_completed(futures):
                    filename = future.result()

                    logger.debug("Finished Uploading: % s", filename)

            logger.debug("All files uploaded")

        # Reset current batch
        self.current_batch = []
        self.annotations_contents_map = {}
        self.current_batch_bytes_size = 0

    def _patch_status(self, status_condition: dict) -> models.ImportSession:
        """Patch import session status"""
        import_session = self.requester.PATCH(
            f"/projects/{self.project_id}/annotationimportsessions/{self.import_session_id}",
            request_body={"status": {"conditions": [status_condition]}},
            response_type=models.ImportSession,
        )

        return import_session

    def get_logs(self) -> models.ImportSessionLog:
        """
        Retrieves import session logs from the project.

        :param import_session_id: The ID of the import session.

        :return: A msgspec struct containing the import session logs with the following structure:

            .. code-block:: python

                ImportSessionLog(
                    id='annotsess_1e433826-ab9c-402e-8b9a-a95d82f358f1',
                    project_id='proj_cd067221d5a6e4007ccbb4afb5966535',
                    logs=[]
                )

        :example:

            .. code-block:: python

                from datature.nexus import Client

                project = Client("5aa41e8ba........").get_project("proj_b705a........")

                project.annotations.retrieve_import_session_logs()
        """
        return self.requester.GET(
            f"/projects/{self.project_id}/annotationimportsessions/{self.import_session_id}/logs",
            response_type=models.ImportSessionLog,
        )
