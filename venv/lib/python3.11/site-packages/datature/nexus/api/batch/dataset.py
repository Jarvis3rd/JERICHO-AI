#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   dataset.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Datature Dataset API
"""

import base64
import logging
import time
from datetime import datetime, timedelta
from os import path
from typing import Union

import crc32c
from alive_progress import alive_bar

from datature.nexus import config, error, models
from datature.nexus.api.batch import models as batch_models
from datature.nexus.api.batch.types import (
    DatasetMetadata,
    DatasetSourceSpec,
    DatasetSpec,
    DatasetStatusOverview,
)
from datature.nexus.api.types import Pagination
from datature.nexus.client_context import RestContext
from datature.nexus.utils import utils

logger = logging.getLogger("datature-nexus")


class Dataset(RestContext):
    """Datature Dataset API Resource."""

    def create(self, name: str, dataset_path: str) -> batch_models.Dataset:
        """
        Creates a new dataset in the project and uploads
        asset SignedURLs to a GCP bucket.

        :param name: The name of the dataset.
        :param dataset_path: The path to the dataset file.
        :return: A msgspec struct containing the dataset metadata with the following structure:

            .. code-block:: python

                Dataset(
                    id='dataset_652ef566-af5c-4d52-b1e4-ec8ec6dc4b8e',
                    object='dataset',
                    name='rbc',
                    project_id='proj_ca5fe71e7592bbcf7705ea36e4f29ed4',
                    expiry_time=1724561116000,
                    status=DatasetStatus(
                        overview='Uploaded',
                        message='Uploaded Dataset',
                        update_time=1723697121735,
                        source=DatasetSource(
                            kind='UploadedNewlineDelimitedJsonFile',
                            upload_url=DatasetUploadUrl(
                                method='PUT',
                                url='',
                                headers=[
                                    'content-length',
                                    'x-goog-hash',
                                    'x-goog-meta-datature-dataset-link',
                                    'x-goog-if-generation-match',
                                    'content-type'
                                ],
                                expires_at_time=1723740318174
                            )
                        ),
                        item_count=50
                    ),
                    create_date=1723697118174,
                    update_date=1723697121774
                )

        :example:
            .. code-block:: python

                from datature.nexus import Client

                project = Client("5aa41e8ba........").get_project("proj_b705a........")
                project.batch.datasets.create(
                    "my-dataset-08-15",
                    "/path/to/dataset.ndjson"
                )
        """
        assert isinstance(name, str)
        assert isinstance(dataset_path, str)

        if not path.exists(dataset_path):
            raise error.Error("Dataset file not found.")
        if not dataset_path.endswith(".ndjson"):
            raise error.Error(
                "Unsupported dataset file type. Only NDJSON is supported."
            )

        dataset_spec = DatasetSpec(source=self._generate_source_spec(dataset_path))
        dataset_options = DatasetMetadata(name=name, spec=dataset_spec)

        dataset_upload_response = self.requester.POST(
            f"/projects/{self.project_id}/batch/datasets",
            request_body=dataset_options.to_json(),
            response_type=batch_models.Dataset,
        )

        file_path = self._upload_file_through_signed_url(
            dataset_path, dataset_upload_response
        )
        logger.info("Finished Uploading: % s", file_path)
        return dataset_upload_response

    def delete(self, dataset_id: str) -> models.DeleteResponse:
        """Deletes a dataset from the project.

        :param dataset_id: The ID of the dataset to delete.
        :return: A msgspec struct containing the delete response with the following structure:

            .. code-block:: python

                DeleteResponse(
                    id='dataset_652ef566-af5c-4d52-b1e4-ec8ec6dc4b8e',
                    deleted=True
                )

        :example:
            .. code-block:: python

                from datature.nexus import Client

                project = Client("5aa41e8ba........").get_project("proj_b705a........")
                project.batch.datasets.delete("dataset_652ef566-af5c-4d52-b1e4-ec8ec6dc4b8e")
        """
        assert isinstance(dataset_id, str)
        return self.requester.DELETE(
            f"/projects/{self.project_id}/batch/datasets/{dataset_id}",
            response_type=models.DeleteResponse,
        )

    def get(self, dataset_id: str) -> batch_models.Dataset:
        """Retrieves a dataset from the project.

        :param dataset_id: The ID of the dataset to retrieve.
        :return: A msgspec struct containing the dataset metadata with the following structure:

            .. code-block:: python

                Dataset(
                    id='dataset_652ef566-af5c-4d52-b1e4-ec8ec6dc4b8e',
                    object='dataset',
                    name='rbc',
                    project_id='proj_ca5fe71e7592bbcf7705ea36e4f29ed4',
                    expiry_time=1724561116000,
                    status=DatasetStatus(
                        overview='Uploaded',
                        message='Uploaded Dataset',
                        update_time=1723697121735,
                        source=DatasetSource(
                            kind='UploadedNewlineDelimitedJsonFile',
                            upload_url=DatasetUploadUrl(
                                method='PUT',
                                url='',
                                headers=[
                                    'content-length',
                                    'x-goog-hash',
                                    'x-goog-meta-datature-dataset-link',
                                    'x-goog-if-generation-match',
                                    'content-type'
                                ],
                                expires_at_time=1723740318174
                            )
                        ),
                        item_count=50
                    ),
                    create_date=1723697118174,
                    update_date=1723697121774
                )

        :example:
            .. code-block:: python

                from datature.nexus import Client

                project = Client("5aa41e8ba........").get_project("proj_b705a........")
                project.batch.datasets.get("dataset_652ef566-af5c-4d52-b1e4-ec8ec6dc4b8e")
        """
        assert isinstance(dataset_id, str)
        return self.requester.GET(
            f"/projects/{self.project_id}/batch/datasets/{dataset_id}",
            response_type=batch_models.Dataset,
        )

    def list(
        self,
        show_expired: bool = False,
        pagination: Union[Pagination, dict, None] = None,
    ) -> models.PaginationResponse[batch_models.Dataset]:
        """Lists all datasets in the project.

        :param show_expired: Whether to show expired datasets.
        :param pagination: The pagination options.
        :return: A msgspec struct containing the dataset metadata with the following structure:

            .. code-block:: python

                PaginationResponse(
                    next_page=None,
                    previous_page=None,
                    data=[
                        Dataset(
                            id='dataset_652ef566-af5c-4d52-b1e4-ec8ec6dc4b8e',
                            object='dataset',
                            name='rbc',
                            project_id='proj_ca5fe71e7592bbcf7705ea36e4f29ed4',
                            expiry_time=1724561116000,
                            status=DatasetStatus(
                                overview='Uploaded',
                                message='Uploaded Dataset',
                                update_time=1723697121735,
                                source=DatasetSource(
                                    kind='UploadedNewlineDelimitedJsonFile',
                                    upload_url=DatasetUploadUrl(
                                        method='PUT',
                                        url='',
                                        headers=[
                                            'content-length',
                                            'x-goog-hash',
                                            'x-goog-meta-datature-dataset-link',
                                            'x-goog-if-generation-match',
                                            'content-type'
                                        ],
                                        expires_at_time=1723740318174
                                    )
                                ),
                                item_count=50
                            ),
                            create_date=1723697118174,
                            update_date=1723697121774
                        )
                    ]
                )

        :example:
            .. code-block:: python

                from datature.nexus import Client

                project = Client("5aa41e8ba........").get_project("proj_b705a........")
                project.batch.datasets.list()
        """
        assert isinstance(pagination, (Pagination, dict, type(None)))

        if isinstance(pagination, dict):
            pagination = Pagination(**pagination)
        if pagination is None:
            pagination = Pagination()

        datasets = self.requester.GET(
            f"/projects/{self.project_id}/batch/datasets",
            query={**pagination.to_json()},
            response_type=models.PaginationResponse[batch_models.Dataset],
        )

        # filter out expired datasets
        if not show_expired:
            current_time_ms = int(time.time()) * 1000
            datasets.data = [
                dataset
                for dataset in datasets.data
                if dataset.expiry_time > current_time_ms
            ]

        return datasets

    def wait_until_done(
        self,
        dataset_id: str,
        interval: int = 5,
        timeout: int = config.OPERATION_LOOPING_TIMEOUT_SECONDS,
    ) -> batch_models.Dataset:
        """Waits until the dataset is uploaded.

        :param dataset_id: The ID of the dataset to wait for.
        :param interval: The interval to check the dataset status.
        :param timeout: The timeout to wait for the dataset to be uploaded.
        :return: A msgspec struct containing the dataset metadata with the following structure:

            .. code-block:: python

                Dataset(
                    id='dataset_652ef566-af5c-4d52-b1e4-ec8ec6dc4b8e',
                    object='dataset',
                    name='rbc',
                    project_id='proj_ca5fe71e7592bbcf7705ea36e4f29ed4',
                    expiry_time=1724561116000,
                    status=DatasetStatus(
                        overview='Uploaded',
                        message='Uploaded Dataset',
                        update_time=1723697121735,
                        source=DatasetSource(
                            kind='UploadedNewlineDelimitedJsonFile',
                            upload_url=DatasetUploadUrl(
                                method='PUT',
                                url='',
                                headers=[
                                    'content-length',
                                    'x-goog-hash',
                                    'x-goog-meta-datature-dataset-link',
                                    'x-goog-if-generation-match',
                                    'content-type'
                                ],
                                expires_at_time=1723740318174
                            )
                        ),
                        item_count=50
                    ),
                    create_date=1723697118174,
                    update_date=1723697121774
                )

        :example:
            .. code-block:: python

                from datature.nexus import Client

                project = Client("5aa41e8ba........").get_project("proj_b705a........")
                project.batch.datasets.wait_until_done("dataset_652ef566-af5c-4d52-b1e4-ec8ec6dc4b8e")
        """
        assert isinstance(interval, int) and interval > 0
        assert isinstance(timeout, int) and timeout > 0

        elapsed_time = datetime.now() + timedelta(seconds=timeout)
        response = self.get(dataset_id)

        with alive_bar(
            1, title="Uploading Dataset", length=20, force_tty=True, enrich_print=False
        ) as progress_bar:
            while response.status.overview != DatasetStatusOverview.UPLOADED.value:
                if (
                    response.status.overview
                    == DatasetStatusOverview.FAILEDPROCESSING.value
                ):
                    raise error.BadRequestError(
                        f"Error processing Dataset {dataset_id}, "
                        f"run `project.batch.datasets.get({dataset_id})` in Python or "
                        f"`datature batch datasets get {dataset_id}` in your terminal to get more "
                        "detailed status messages, or contact support at support@datature.io",
                    )
                if response.status.overview == DatasetStatusOverview.FAILEDUPLOAD.value:
                    raise error.BadRequestError(
                        f"Error uploading Dataset {dataset_id}, "
                        f"run `project.batch.datasets.get({dataset_id})` in Python or "
                        f"`datature batch datasets get {dataset_id}  in your terminal to get more "
                        "detailed status messages, or contact support at support@datature.io",
                    )

                if elapsed_time < datetime.now():
                    logger.warning(
                        "Operation timeout: please run `project.batch.datasets.get(%s)` in Python "
                        "or `datature batch datasets get %s` in your terminal to get the "
                        "status instead, or contact support at support@datature.io",
                        dataset_id,
                        dataset_id,
                    )
                    return response

                time.sleep(interval)
                response = self.get(dataset_id)
            progress_bar()  # pylint: disable=E1102
            return response

    def _generate_source_spec(self, file_path: str) -> DatasetSourceSpec:
        """Generate the source spec for the dataset.

        :param file_path: The path to the dataset file.
        :return: The source spec for the dataset.
        """
        file_hash = crc32c.CRC32CHash()

        with open(file_path, "rb") as file:
            chunk = file.read(config.FILE_CHUNK_SIZE)
            while chunk:
                file_hash.update(chunk)
                chunk = file.read(config.FILE_CHUNK_SIZE)

        # To fix the wrong crc32c caused by mac M1 clip
        crc32c_str = base64.b64encode(file_hash.digest()).decode("utf-8")
        size = path.getsize(file_path)

        if size and crc32c:
            return DatasetSourceSpec(
                size_bytes=size,
                crc32c=crc32c_str,
            )
        raise error.Error("Failed to read dataset file.")

    def _upload_file_through_signed_url(
        self, file_path, dataset_upload: batch_models.Dataset
    ) -> str:
        """Upload the dataset file to GCP through the signed URL.

        :param file_path: The path to the dataset file.
        :param dataset_upload: The dataset upload response.
        :return: The path to the uploaded dataset file.
        """
        http_session = utils.init_gcs_upload_session()
        http_session.request(
            dataset_upload.status.source.upload_url.method,
            dataset_upload.status.source.upload_url.url,
            headers=dataset_upload.status.source.upload_url.headers,
            data=open(file_path, "rb"),  # pylint: disable=R1732
            timeout=config.REQUEST_TIME_OUT_SECONDS,
        )
        return file_path
