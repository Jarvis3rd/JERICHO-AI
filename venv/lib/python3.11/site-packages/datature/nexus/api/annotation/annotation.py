#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   annotation.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Datature Annotation API
"""

import json
import zipfile
from pathlib import Path
from typing import Union

import msgspec

from datature.nexus import error, models
from datature.nexus.api.annotation.import_session import ImportSession
from datature.nexus.api.operation import Operation
from datature.nexus.api.types import (
    AnnotationExportMetadata,
    AnnotationFilter,
    AnnotationMetadata,
    Pagination,
)
from datature.nexus.client_context import ClientContext, RestContext
from datature.nexus.utils import utils


class Annotation(RestContext):
    """Datature Annotation API Resource."""

    def __init__(self, client_context: ClientContext):
        """Initialize the API Resource."""
        super().__init__(client_context)
        self.operation = Operation(client_context)

    def list(
        self,
        pagination: Union[Pagination, dict, None] = None,
        filters: Union[AnnotationFilter, dict, None] = None,
        include_attributes: bool = False,
    ) -> models.PaginationResponse[models.Annotation]:
        """Lists all annotations of a specific asset.

        :param pagination: The pagination options.
        :param filters: The filter options.
        :param include_attributes: A flag indicating whether to include the annotation attributes.
        :return: A list of msgspec struct containing
            annotation metadata with the following structure:

            .. code-block:: python

                PaginationResponse(
                    next_page='NjVhYTE0ZDY3YzQ5MThlMTJjYTUyOGRk',
                    prev_page=None,
                    data=[
                        Annotation(
                            id='annot_e5028bdc-122e-4837-b354-d82b95320b69',
                            project_id='proj_cd067221d5a6e4007ccbb4afb5966535',
                            asset_id='asset_6647b58e-86af-460c-9a85-efead830aee8',
                            tag='dog',
                            bound_type='Polygon',
                            bound=[
                                [0.42918, 0.45322666666666667],
                                [0.43677999999999995, 0.4579466666666666],
                                [0.43677999999999995, 0.46941333333333335],
                                [0.44236000000000003, 0.4788800000000001],
                                [0.45146, 0.4829333333333333],
                                [0.45754, 0.48696000000000006],
                                [0.48234, 0.4842666666666666],
                                [0.4869, 0.43432000000000004],
                                [0.50514, 0.4302666666666667]
                            ],
                            create_date=None,
                            ontology_id='ontology_843e486c-58d7-45a7-b722-f4948e204a56',
                            attributes=[
                                OntologyAttributeValue(
                                    id='attri_d0877827-63d6-4794-b520-ef3e0c57ef71',
                                    name='Tag Group',
                                    value=['person']
                                )
                            ]
                        )
                    ]
                )

        :example:
            .. code-block:: python

                from datature.nexus import Client

                project = Client("5aa41e8ba........").get_project("proj_b705a........")
                project.annotations.list(
                    pagination = {
                        "limit": 500,
                        "page": "NjVhYTE0ZDY3YzQ5MThlMTJjYTUyOGRk"
                    },
                    filters = {
                        "asset_ids": ["asset_6647b58e-86af-460c-9a85-efead830aee8"]
                    }
                )
        """
        assert isinstance(pagination, (Pagination, dict, type(None)))
        assert isinstance(filters, (AnnotationFilter, dict, type(None)))

        if isinstance(pagination, dict):
            pagination = Pagination(**pagination)
        if pagination is None:
            pagination = Pagination()

        if isinstance(filters, dict):
            filters = AnnotationFilter(**filters)
        if filters is None:
            filters = AnnotationFilter()

        return self.requester.GET(
            f"/projects/{self.project_id}/annotations",
            query={
                **pagination.to_json(),
                **filters.to_json(),
                "includeAttributes": include_attributes,
            },
            response_type=models.PaginationResponse[models.Annotation],
        )

    def create(self, annotation: Union[AnnotationMetadata, dict]) -> models.Annotation:
        """Creates an annotation.

        :param annotation: The metadata of the annotation.
        :return: A msgspec struct containing the annotation metadata with the following structure:

            .. code-block:: python

                Annotation(
                    id='annot_ffcd02f1-bac2-4cd4-b959-a04e0c67b44e',
                    project_id='proj_cd067221d5a6e4007ccbb4afb5966535',
                    asset_id='asset_dd0c72a4-a8c4-479e-a130-432e699351fc',
                    tag='boat',
                    bound_type='Rectangle',
                    bound=[
                        [0.425, 0.49382716049382713],
                        [0.425, 0.6419753086419753],
                        [0.6, 0.6419753086419753],
                        [0.6, 0.49382716049382713]
                    ],
                    create_date=1701927649302,
                )

        :example:
            .. code-block:: python

                from datature.nexus import Client

                project = Client("5aa41e8ba........").get_project("proj_b705a........")

                project.annotations.create({
                    "bound_type": "Rectangle",
                    "bound": [[0.425, 0.49382716049382713], [0.425, 0.6419753086419753],
                            [0.6, 0.6419753086419753], [0.6, 0.49382716049382713]],
                    "asset_id":
                        "asset_6aea3395-9a72-4bb5-9ee0-19248c903c56",
                    "tag":
                        "tagName1"
                })
        """
        assert isinstance(annotation, (AnnotationMetadata, dict))

        if isinstance(annotation, dict):
            annotation = AnnotationMetadata(**annotation)

        return self.requester.POST(
            f"/projects/{self.project_id}/annotations",
            request_body=annotation.to_json(),
            response_type=models.Annotation,
        )

    def get(
        self, annotation_id: str, include_attributes: bool = False
    ) -> models.Annotation:
        """Retrieves a specific annotation using the annotation ID.

        :param annotation_id: The ID of the annotation.
        :param include_attributes: A flag indicating whether to include the annotation attributes.
        :return: A msgspec struct containing
            the specific annotation metadata with the following structure:

            .. code-block:: python

                    Annotation(
                        id='annot_a9ff9b21-c0e2-49ff-8a69-773aaf00a6f8',
                        project_id='proj_cd067221d5a6e4007ccbb4afb5966535',
                        asset_id='asset_f4dcb429-0332-4dd6-a1b4-fee794031ba6',
                        tag='boat',
                        bound_type='Rectangle',
                        create_date=1701927649302,
                        bound=[
                            [0.2772511848341232, 0.34635416666666663],
                            [0.2772511848341232, 0.46875],
                            [0.54739336492891, 0.46875],
                            [0.54739336492891, 0.34635416666666663]
                        ],
                        ontology_id='ontology_843e486c-58d7-45a7-b722-f4948e204a56',
                        attributes=[
                            OntologyAttributeValue(
                                id='attri_d0877827-63d6-4794-b520-ef3e0c57ef71',
                                name='Tag Group',
                                value=['person']
                            )
                        ]
                    )

        :example:
            .. code-block:: python

                    from datature.nexus import Client

                    project = Client("5aa41e8ba........").get_project("proj_b705a........")
                    project.annotations.get(
                        "asset_6aea3395-9a72-4bb5-9ee0-19248c903c56",
                        include_attributes=True
                    )
        """
        assert isinstance(annotation_id, str)
        return self.requester.GET(
            f"/projects/{self.project_id}/annotations/{annotation_id}",
            query={"includeAttributes": include_attributes},
            response_type=models.Annotation,
        )

    def delete(self, annotation_id: str) -> models.DeleteResponse:
        """Deletes a specific annotation from the project.

        :param annotation_id: The ID of the annotation.
        :return: A msgspec struct containing
            the deleted annotation ID and the deletion status with the following structure:

            .. code-block:: python

                DeleteResponse(deleted=True, id='annot_8188782f-a86b-4961-9e2a-697509085460')

        :example:
            .. code-block:: python

                from datature.nexus import Client

                project = Client("5aa41e8ba........").get_project("proj_b705a........")
                project.annotations.delete("asset_6aea3395-9a72-4bb5-9ee0-19248c903c56")
        """
        assert isinstance(annotation_id, str)
        return self.requester.DELETE(
            f"/projects/{self.project_id}/annotations/{annotation_id}",
            response_type=models.DeleteResponse,
        )

    def create_export(
        self,
        export_metadata: Union[AnnotationExportMetadata, dict],
        background: bool = False,
    ) -> models.Operation:
        """Exports all annotations from the project in a specific annotation format.

        :param export_metadata: A dict containing other export options.
        :param background: Signal to complete the annotation export
                            process in the background. Defaults to False.
        :return: A msgspec struct containing the operation metadata of the annotation export
            with the following structure:

            .. code-block:: python

                Operation(
                    id='op_ea10c06e-0e2a-4087-b2cf-1a1c9c42d83d',
                    kind='nexus.annotations.export',
                    status=OperationStatus(
                        overview='Finished',
                        message='Operation finished',
                        progress=OperationProgress(
                            unit='whole operation',
                            with_status=OperationProgressWithStatus(
                                Queued=0,
                                Running=0,
                                Finished=1,
                                Cancelled=0,
                                Errored=0
                            )
                        )
                    ),
                    create_date=1701927649302,
                    update_date=1701927649302
                )

        :example:
            .. code-block:: python

                from datature.nexus import Client

                project = Client("5aa41e8ba........").get_project("proj_b705a........")

                project.annotations.create_export({
                    "format": "csv_fourcorner",
                    "options": {
                        "split_ratio": 0.5,
                        "seed": 1337,
                        "normalized": True
                    }
                })
        """
        assert isinstance(export_metadata, (AnnotationExportMetadata, dict))
        assert isinstance(background, bool)

        if isinstance(export_metadata, dict):
            export_metadata = AnnotationExportMetadata(**export_metadata)

        num_annotated_assets = self.requester.GET(
            f"/projects/{self.project_id}", response_type=models.Project
        ).statistic.annotated_assets

        if num_annotated_assets == 0:
            raise error.BadRequestError(
                "There are no annotations in the project. Please annotate some assets first."
            )
        if num_annotated_assets == 1:
            export_metadata.options.split_ratio = 0.0

        operation = self.requester.POST(
            f"/projects/{self.project_id}/annotationexports",
            request_body=export_metadata.to_json(),
            response_type=models.Operation,
        )

        if background:
            return operation

        return self.operation.wait_until_done(operation.id)

    def download_exported_file(
        self, op_id: str, path: Union[str, Path, None] = None
    ) -> models.LocalAnnotations:
        """Retrieves the download link of the exported annotations.

        :param op_id: The operation ID of the annotation export.
        :param path: The download path for the annotation, default current path.
        :return: A msgspec struct with the download metadata of
            the annotation export with the following structure:

            .. code-block:: python

                LocalAnnotations(
                    download_path='local',
                    file_names=[
                        'cd067221d5a6e4007ccbb4afb5966535/train.csv',
                        'cd067221d5a6e4007ccbb4afb5966535/validate.csv'
                    ]
                )

        :example:
            .. code-block:: python

                from datature.nexus import Client

                project = Client("5aa41e8ba........").get_project("proj_b705a........")

                project.annotations.download_exported_file(
                    "op_cf8c538a-bcb5-49a9-82cf-fb0d13b49bb1"
                )
        """
        assert isinstance(op_id, str)
        assert isinstance(path, (str, Path, type(None)))

        exported_files = self.requester.GET(
            f"/projects/{self.project_id}/annotationexports/{op_id}",
            response_type=models.ExportedAnnotations,
        )

        download_path = utils.get_download_path(path)

        if exported_files.status == "Finished" and exported_files.download is not None:
            download_tmpfile = utils.download_files_to_tempfile(exported_files.download)

            with zipfile.ZipFile(download_tmpfile, "r") as zip_ref:
                zip_ref.extractall(download_path)

                file_names = [
                    info.filename for info in zip_ref.infolist() if not info.is_dir()
                ]

            return msgspec.json.decode(
                json.dumps(
                    {"download_path": str(download_path), "file_names": file_names}
                ),
                type=models.LocalAnnotations,
            )

        # If didn't find the model key in the artifacts, raise an 404 error
        raise error.NotFoundError(
            f"Export with id {op_id} not found, please export first."
        )

    def create_import_session(self, background: bool = False):
        """
        Creates an import session to import or update annotations.
            For bulk annotation import, we allow the user to add up to 1000
            files in one single import session.
            To add file into the import session, simply include its file path as an argument
            when calling the add function. Once all files have been added,
            it will initiate the upload process automatically.

        :param background: A flag indicating whether the upload should run in the background.
            Default is False.
        :return: ImportSession class
        :example:

            .. code-block:: python

                from datature.nexus import Client

                project = Client("5aa41e8ba........").get_project("proj_b705a........")

                # Import session context manager
                # If background is set to True,
                # the import session will be processed in the background

                import_session = project.annotations.create_import_session(background=True)

                with import_session as session:
                    # Function 1: add file path
                    session.add_path("path/to/annotation1.json")

                    # Function 2: add folder path
                    session.add_path("folder/path/to/files")

                    # Function 3: or even you can add bytes data
                    session.add_bytes(b"bytes/of/file", "filename")

                # Retrieve import session logs
                import_session.get_logs()

        """
        return ImportSession(self._context, background)

    def list_import_sessions(self) -> models.ImportSessions:
        """Lists the import sessions from the project.

        :return: A list of msgspec struct containing import sessions with the following structure:

            .. code-block:: python

                [ImportSession(
                    id='annotsess_58bb96a6-9dd5-4c78-89e7-57366060318e',
                    project_id='proj_cd067221d5a6e4007ccbb4afb5966535',
                    status=ImportSessionStatus(
                        overview='Finished',
                        message='Annotation Imported successfully.',
                        update_date=1701677312962,
                        annotations=ImportSessionStatusAnnotations(
                            with_status=ImportSessionAnnotationStatus(
                                Processed=1548,
                                Committed=1548
                            )
                        ),
                        files=ImportSessionStatusFiles(
                            total_size_bytes=63368,
                            page_count=1,
                            with_status=ImportSessionFilesStatus(
                                Processing=0,
                                Processed=1,
                                FailedProcess=0
                            )
                        )
                    ),
                    expiry_date=1701927649302,
                    create_date=1701927649302,
                    update_date=1701927649302
                )]

        :example:

            .. code-block:: python

                from datature.nexus import Client

                project = Client("5aa41e8ba........").get_project("proj_b705a........")

                project.annotations.list_import_sessions()
        """
        return self.requester.GET(
            f"/projects/{self.project_id}/annotationimportsessions",
            response_type=models.ImportSessions,
        )

    def get_import_session(self, import_session_id: str) -> models.ImportSession:
        """Retrieves a specific import session from the project.

        :param import_session_id: The ID of the import session.

        :return: A msgspec struct containing the import session with the following structure:

            .. code-block:: python

                ImportSession(
                    id='annotsess_58bb96a6-9dd5-4c78-89e7-57366060318e',
                    project_id='proj_cd067221d5a6e4007ccbb4afb5966535',
                    status=ImportSessionStatus(
                        overview='Finished',
                        message='Annotation Imported successfully.',
                        update_date=1701677312962,
                        annotations=ImportSessionStatusAnnotations(
                            with_status=ImportSessionAnnotationStatus(
                                Processed=1548,
                                Committed=1548
                            )
                        ),
                        files=ImportSessionStatusFiles(
                            total_size_bytes=63368,
                            page_count=1,
                            with_status=ImportSessionFilesStatus(
                                Processing=0,
                                Processed=1,
                                FailedProcess=0
                            )
                        )
                    ),
                    expiry_date=1701927649302,
                    create_date=1701927649302,
                    update_date=1701927649302
                )

        :example:

            .. code-block:: python

                from datature.nexus import Client

                project = Client("5aa41e8ba........").get_project("proj_b705a........")

                project.annotations.get_import_session(
                    "annotsess_75879caf-184d-4d82-912b-180609a72ace"
                )
        """
        assert isinstance(import_session_id, str)

        return self.requester.GET(
            f"/projects/{self.project_id}/annotationimportsessions/{import_session_id}",
            response_type=models.ImportSession,
        )

    def get_import_session_logs(
        self, import_session_id: str
    ) -> models.ImportSessionLog:
        """Retrieves import session logs from the project.

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

                project.annotations.get_import_session_logs(
                    "annotsess_75879caf-184d-4d82-912b-180609a72ace"
                )
        """
        assert isinstance(import_session_id, str)
        return self.requester.GET(
            f"/projects/{self.project_id}/annotationimportsessions/{import_session_id}/logs",
            response_type=models.ImportSessionLog,
        )
