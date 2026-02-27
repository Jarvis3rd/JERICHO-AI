#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   asset.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Datature Asset API
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import quote, unquote

from datature.nexus import models
from datature.nexus.api.asset.downloader import AssetDownloader
from datature.nexus.api.asset.results import AssetDownloadResult
from datature.nexus.api.asset.upload_session import UploadSession
from datature.nexus.api.operation import Operation
from datature.nexus.api.types import (
    AssetCustomMetadata,
    AssetCustomMetadataBatch,
    AssetFilenameFrameParent,
    AssetFilenameParent,
    AssetFilter,
    AssetFrameParent,
    AssetMetadata,
    AssetParent,
    Pagination,
)
from datature.nexus.client_context import ClientContext, RestContext
from datature.nexus.config import (
    ASSET_DEFAULT_SAVE_DIR,
    ASSET_DOWNLOAD_DEFAULT_BATCH_SIZE,
)


class Asset(RestContext):
    """Datature Annotation API Resource."""

    def __init__(self, client_context: ClientContext):
        """Initialize the API Resource."""
        super().__init__(client_context)
        self.operation = Operation(client_context)

    def list(
        self,
        pagination: Union[Pagination, dict, None] = None,
        filters: Union[AssetFilter, dict, None] = None,
    ) -> models.PaginationResponse[models.Asset]:
        """Retrieves a list of all assets in the project.

        :param pagination: A dictionary containing the limit of
                            the number of assets to be returned in each page (defaults to 100),
                            and the page cursor for page selection (defaults to the first page).
        :param filters: A dictionary containing the filters of
                            the assets to be returned.
        :return: A msgspec struct of pagination response with the following structure:

                .. code-block:: python

                    PaginationResponse(
                        next_page='T2YAGDY1NWFlNDcyMzZkiMDYwMTQ5N2U2',
                        prev_page=None,
                        data=[
                            Asset(
                                id='asset_8208740a-2d9c-46e8-abb9-5777371bdcd3',
                                filename='boat180.png',
                                project='proj_cd067221d5a6e4007ccbb4afb5966535',
                                status='None',
                                create_date=1701927649302,
                                url='',
                                metadata=AssetMetadata(
                                    file_size=186497,
                                    mime_type='image/png',
                                    height=243,
                                    width=400,
                                    groups=['main'],
                                    custom_metadata={'captureAt': '2021-03-10T09:00:00Z'}
                                ),
                                statistic=AssetAnnotationsStatistic(
                                    tags_count=[],
                                    total_annotations=0
                                )
                            )
                        ]
                    )

        :example:
                .. code-block:: python

                        from datature.nexus import Client

                        project = Client("5aa41e8ba........").get_project("proj_b705a........")

                        project.assets.list({
                            "limit": 2,
                            "page": "ZjYzYmJkM2FjN2UxOTA4ZmU0ZjE0Yjk5Mg"
                        }, filters={
                            "status": "Annotated",
                            "groups": ["main"],
                        })

                        # or
                        project.assets.list(
                            nexus.ApiTypes.Pagination(
                                limit= 2,
                                page="ZjYzYmJkM2FjN2UxOTA4ZmU0ZjE0Yjk5Mg"
                            ),
                            filters=nexus.ApiTypes.AssetFilter(status="Annotated", groups=["main"])
                        )

        """
        assert isinstance(pagination, (Pagination, dict, type(None)))
        assert isinstance(filters, (AssetFilter, dict, type(None)))

        if isinstance(pagination, dict):
            pagination = Pagination(**pagination)
        if pagination is None:
            pagination = Pagination()

        if isinstance(filters, dict):
            filters = AssetFilter(**filters)
        if filters is None:
            filters = AssetFilter()

        return self.requester.GET(
            f"/projects/{self.project_id}/assets",
            query={**pagination.to_json(), **filters.to_json()},
            response_type=models.PaginationResponse[models.Asset],
        )

    def get(self, asset_id_or_name: str) -> models.Asset:
        """Retrieves a specific asset using the asset ID or file name.

        :param asset_id_or_name: The ID or file name of the asset as a string.
        :return: A msgspec struct containing the metadata of one asset with the following structure:

                .. code-block:: python

                        Asset(
                            id='asset_8208740a-2d9c-46e8-abb9-5777371bdcd3',
                            filename='boat180.png',
                            project='proj_cd067221d5a6e4007ccbb4afb5966535',
                            status='None',
                            create_date=1701927649302,
                            url='',
                            metadata=AssetMetadata(
                                file_size=186497,
                                mime_type='image/png',
                                height=243,
                                width=400,
                                groups=['main'],
                                custom_metadata={'captureAt': '2021-03-10T09:00:00Z'}
                            ),
                            statistic=AssetAnnotationsStatistic(
                                tags_count=[],
                                total_annotations=0
                            )
                        )

        :example:
                .. code-block:: python

                        from datature.nexus import Client

                        project = Client("5aa41e8ba........").get_project("proj_b705a........")
                        project.assets.get("asset_6aea3395-9a72-4bb5-9ee0-19248c903c56")
        """
        assert isinstance(asset_id_or_name, str)
        return self.requester.GET(
            f"/projects/{self.project_id}/assets/{asset_id_or_name}",
            response_type=models.Asset,
        )

    def update(
        self, asset_id_or_name: str, asset_meta: Union[AssetMetadata, dict]
    ) -> models.Asset:
        """Updates the metadata of a specific asset.

        :param asset_id_or_name: The ID or file name of the asset as a string.
        :param asset_meta: The new metadata of the asset to be updated.
        :return: A msgspec struct containing the metadata of one asset with the following structure:

                .. code-block:: python

                        Asset(
                            id='asset_f4dcb429-0332-4dd6-a1b4-fee794031ba6',
                            project_id='proj_cd067221d5a6e4007ccbb4afb5966535',
                            filename='boat194.png',
                            status='None',
                            create_date=1701927649302,
                            url='',
                            metadata=AssetMetadata(
                                file_size=172676,
                                mime_type='image/png',
                                height=384,
                                width=422,
                                groups=['main'],
                                custom_metadata={'captureAt': '2021-03-10T09:00:00Z'}
                            ),
                            statistic=AssetAnnotationsStatistic(
                                tags_count=[],
                                total_annotations=0
                            )
                        )

        :example:
                .. code-block:: python

                        from datature.nexus import Client

                        project = Client("5aa41e8ba........").get_project("proj_b705a........")

                        project.assets.update(
                            "asset_6aea3395-9a72-4bb5-9ee0-19248c903c56",
                            {
                                "status": "Annotated"
                            }
                        )
        """
        assert isinstance(asset_id_or_name, str)
        assert isinstance(asset_meta, (AssetMetadata, dict))

        if isinstance(asset_meta, dict):
            asset_meta = AssetMetadata(**asset_meta)

        return self.requester.PATCH(
            f"/projects/{self.project_id}/assets/{asset_id_or_name}",
            request_body=asset_meta.to_json(),
            response_type=models.Asset,
        )

    def delete(self, asset_id_or_name: str) -> models.DeleteResponse:
        """Deletes a specific asset from the project.

        :param asset_id_or_name: The ID or file name of the asset as a string.
        :return: A msgspec struct containing the
            deleted asset ID and the deletion status with the following structure.

                .. code-block:: python

                    DeleteResponse(deleted=True, id='asset_8208740a-2d9c-46e8-abb9-5777371bdcd3')

        :example:

                .. code-block:: python

                        from datature.nexus import Client

                        project = Client("5aa41e8ba........").get_project("proj_b705a........")

                        project.assets.delete(
                            "asset_6aea3395-9a72-4bb5-9ee0-19248c903c56",
                        )
        """
        assert isinstance(asset_id_or_name, str)
        return self.requester.DELETE(
            f"/projects/{self.project_id}/assets/{asset_id_or_name}",
            response_type=models.DeleteResponse,
        )

    def create_upload_session(
        self,
        groups: Optional[List[str]] = None,
        background: bool = False,
        show_progress: bool = True,
    ) -> UploadSession:
        """
        Creates a new upload session with specified
        groups and an option to run in the background.

        This method initializes and returns an UploadSession object,
        which can be used to manage file uploads within the system.

        :param groups: A list of group names to categorize the upload. Default is None.
        :param background: A flag indicating whether
                            the upload should run in the background. Default is False.
        :param show_progress: Whether to display an alive-progress bar during upload.
                            Default is False. Set to False when CLI implements its own progress.
        :return: UploadSession: An instance of the UploadSession class.
        :example:

                .. code-block:: python

                    from datature.nexus import Client

                    project = Client("5aa41e8ba........").get_project("proj_b705a........")

                    upload_session = project.assets.create_upload_session(
                                                groups=["main"],
                                                background=True
                                            )

                    with upload_session as session:
                        # add assets path to upload session
                        upload_session.add_path(
                            "folder/path/to/files",
                            custom_metadata={"key": "value"}
                        )

                        upload_session.add_bytes(
                            b"bytes/of/file",
                            "filename",
                            custom_metadata={"key": "value"}
                        )
        """
        assert isinstance(groups, (list, type(None)))
        assert isinstance(background, bool)
        assert isinstance(show_progress, bool)

        return UploadSession(self._context, groups, background, show_progress)

    def list_groups(self, groups: Union[List[str], None] = None) -> models.AssetGroups:
        """Retrieve asset statistics categorized by asset group and asset status.

        :param groups: A string array of name(s) of asset group(s).
        :return: A list of msgspec struct of
            the categorized asset statistics with the following structure:

                .. code-block:: python

                        [
                            AssetGroup(
                                group='1',
                                statistic=AssetGroupStatistic(
                                    total_assets=1,
                                    annotated_assets=0,
                                    reviewed_assets=0,
                                    to_fixed_assets=0,
                                    completed_assets=0
                                )
                            ),
                            AssetGroup(
                                group='main',
                                statistic=AssetGroupStatistic(
                                    total_assets=503,
                                    annotated_assets=0,
                                    reviewed_assets=0,
                                    to_fixed_assets=0,
                                    completed_assets=0
                                )
                            )
                        ]

        :example:

                .. code-block:: python

                    from datature.nexus import Client

                    project = Client("5aa41e8ba........").get_project("proj_b705a........")
                    project.assets.list_groups()
        """
        assert isinstance(groups, (list, type(None)))

        return self.requester.GET(
            f"/projects/{self.project_id}/assetgroups",
            query={"group": groups},
            response_type=models.AssetGroups,
        )

    def download(
        self,
        save_dir: str = ASSET_DEFAULT_SAVE_DIR,
        overwrite: bool = False,
        show_progress: bool = True,
    ) -> AssetDownloadResult:
        """Download all assets from the project to local storage.

        Downloads all asset files (images, videos, documents) from the project to
        a local directory. The download process is optimized with batching and
        parallel downloads for efficiency. Files are organized in a structured
        directory layout.

        Args:
            save_dir: Base directory where assets will be saved. Assets are saved in a
                subdirectory structure: save_dir/project_id/filename.ext.
                Defaults to "~/.datature/nexus/assets/".
            overwrite: Whether to overwrite existing files. If False, existing files
                are skipped. If True, files are re-downloaded. Defaults to False.
            show_progress: Whether to display download progress bar with file counts
                and transfer speeds. Set to False for non-interactive environments.
                Defaults to True.

        Returns:
            AssetDownloadResult wrapper containing download information and helper
            methods for inspecting downloaded assets. Use `.summary()` to see
            download statistics or `.info()` for detailed information.

        Raises:
            FileNotFoundError: If the save directory cannot be created.
            PermissionError: If unable to write to save_dir.
            OSError: If insufficient disk space for download.

        Example:
            ```python
            # Download all assets with default settings
            result = project.assets.download()
            print(f"Downloaded {result.count} assets to {result.save_dir}")

            # Download to custom directory
            result = project.assets.download(save_dir="./my_assets", overwrite=True)
            # Files will be saved in: ./my_assets/{project_id}/
            ```

        """
        # Validate and create save directory with project_id subdirectory
        save_path = (Path(save_dir) / self.project_id).resolve()
        try:
            save_path.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            raise OSError(f"Cannot create save directory '{save_dir}': {e}") from e
        downloader = AssetDownloader(overwrite=overwrite, show_progress=show_progress)

        # Get total asset count from project statistics
        from datature.nexus.api.project import Project  # pylint: disable=C0415

        total_asset_count = Project(self._context).get_info().statistic.total_assets
        total_batch_count = total_asset_count // ASSET_DOWNLOAD_DEFAULT_BATCH_SIZE + 1

        downloader.download(
            url_batches=downloader.generate_download_url_batches(
                self, ASSET_DOWNLOAD_DEFAULT_BATCH_SIZE
            ),
            save_dir=save_path,
            total_assets=total_asset_count,
            total_batches=total_batch_count,
        )

        return AssetDownloadResult(
            project_id=self.project_id,
            count=total_asset_count,
            save_dir=str(save_path),
        )

    def get_custom_metadata(self, asset_id_or_name: str) -> models.AssetCustomMetadatas:
        """Retrieve custom metadata for a specific asset.

        This method fetches all custom metadata associated with a given asset,
        including metadata for specific frames if the asset is a video.

        :param asset_id_or_name: The ID or file name of the asset as a string.
        :return: A msgspec struct containing the custom metadata of the asset with the following structure:

                .. code-block:: python

                        AssetCustomMetadatas(
                            custom_metadatas=[
                                AssetCustomMetadata(
                                    custom_metadata={"captureAt": "2021-03-10T09:00:00Z"}
                                )
                            ]
                        )

        :example:
                .. code-block:: python

                        from datature.nexus import Client

                        project = Client("5aa41e8ba........").get_project("proj_b705a........")
                        project.assets.get_custom_metadata("asset_6aea3395-9a72-4bb5-9ee0-19248c903c56")
        """
        assert isinstance(asset_id_or_name, str)

        return self.requester.GET(
            f"/projects/{self.project_id}/assets/{asset_id_or_name}/customMetadatas",
            response_type=models.AssetCustomMetadatas,
        )

    def add_custom_metadata(
        self,
        asset_id_or_name: str,
        custom_metadata: Dict[str, Union[str, int, float, bool]],
        frame: Optional[int] = None,
    ) -> models.AssetCustomMetadata:
        """Add custom metadata to a specific asset.

        This method allows you to add custom metadata to an asset. For video assets,
        you can must specify the frame number.

        :param asset_id_or_name: The ID or file name of the asset as a string.
        :param custom_metadata: A dictionary of custom metadata to add to the asset.
                               Supported value types are string, int, float, and bool.
        :param frame: Required frame number for video assets. Optional for image assets.
        :return: A msgspec struct containing the added custom metadata with the following structure:

                .. code-block:: python

                        AssetCustomMetadata(
                            custom_metadata={"captureAt": "2021-03-10T09:00:00Z"}
                        )

        :example:
                .. code-block:: python

                        from datature.nexus import Client

                        project = Client("5aa41e8ba........").get_project("proj_b705a........")

                        # Add metadata to asset level
                        project.assets.add_custom_metadata(
                            "asset_6aea3395-9a72-4bb5-9ee0-19248c903c56",
                            {"captureAt": "2021-03-10T09:00:00Z"}
                        )

                        # Add metadata to specific frame (for video assets)
                        project.assets.add_custom_metadata(
                            "asset_6aea3395-9a72-4bb5-9ee0-19248c903c56",
                            {"event": "motion_detected"},
                            frame=15
                        )
        """
        assert isinstance(asset_id_or_name, str)
        assert isinstance(custom_metadata, dict)

        if not all(
            isinstance(key, str) and isinstance(value, (str, int, float, bool))
            for key, value in custom_metadata.items()
        ):
            raise ValueError(
                "custom_metadata must be a dictionary with keys of string, and values of string, int, float, or bool"
            )

        if frame:
            parent = AssetFrameParent(frame=frame)
        else:
            parent = AssetParent()

        custom_meta = AssetCustomMetadata(
            parent=parent, custom_metadata=custom_metadata
        )

        return self.requester.PUT(
            f"/projects/{self.project_id}/assets/{asset_id_or_name}/customMetadatas",
            request_body=custom_meta.to_json(),
            response_type=models.AssetCustomMetadata,
        )

    def delete_custom_metadata(
        self, asset_id_or_name: str, custom_metadata_id: str
    ) -> models.DeleteResponse:
        """Delete custom metadata from a specific asset.

        This method removes a specific custom metadata entry from an asset.
        The custom_metadata_id can be obtained from the get_custom_metadata method.

        :param asset_id_or_name: The ID or file name of the asset as a string.
        :param custom_metadata_id: The ID of the custom metadata to delete.
        :return: A msgspec struct containing the deletion status with the following structure:

                .. code-block:: python

                        DeleteResponse(
                            deleted=True,
                            id='custommeta_customMetadata#assetParent:59d4e65e05e7360235526f75698ef3e0:97a83640-f56d-440c-9095-362de2d12681'
                        )

        :example:
                .. code-block:: python

                        from datature.nexus import Client

                        project = Client("5aa41e8ba........").get_project("proj_b705a........")
                        project.assets.delete_custom_metadata(
                            "asset_6aea3395-9a72-4bb5-9ee0-19248c903c56",
                            "custommeta_customMetadata#assetParent:59d4e65e05e7360235526f75698ef3e0:97a83640-f56d-440c-9095-362de2d12681",
                        )
        """
        assert isinstance(asset_id_or_name, str)
        assert isinstance(custom_metadata_id, str)

        # Ensures proper encoding no matter the encoding state
        encoded_custom_metadata_id = quote(unquote(custom_metadata_id))

        return self.requester.DELETE(
            f"/projects/{self.project_id}/assets/{asset_id_or_name}"
            f"/customMetadatas/{encoded_custom_metadata_id}",
            response_type=models.DeleteResponse,
        )

    def add_custom_metadata_batch(
        self,
        custom_metadata_batch: List[Dict[str, Dict[str, Any]]],
    ) -> models.AssetCustomMetadata:
        """Add custom metadata to multiple assets in a single operation.

        This method allows you to add custom metadata to multiple assets or frames
        in a single batch operation, which is more efficient than individual calls.
        Each item in the batch should specify the target asset (by ID or filename)
        and a frame number for video assets.

        :param custom_metadata_batch: A list of dictionaries, where each dictionary contains:
                                     - "parent": A dictionary with either "asset_id" or "filename",
                                       and "frame" for video assets
                                     - "custom_metadata": A dictionary of metadata key-value pairs
        :return: A msgspec struct containing the batch operation response.
        :raises ValueError: If the parent specification is invalid (missing asset_id or filename).

        :example:
                .. code-block:: python

                        from datature.nexus import Client

                        project = Client("5aa41e8ba........").get_project("proj_b705a........")

                        # Batch add metadata to multiple assets
                        batch_data = [
                            {
                                "parent": {"asset_id": "asset_123", "frame": 5},
                                "custom_metadata": {"event": "motion", "confidence": 0.95}
                            },
                            {
                                "parent": {"filename": "image.jpg"},
                                "custom_metadata": {"location": "camera_1", "timestamp": "2021-03-10T09:00:00Z"}
                            }
                        ]

                        project.assets.add_custom_metadata_batch(batch_data)
        """

        assert isinstance(custom_metadata_batch, list)

        custom_metas = AssetCustomMetadataBatch(custom_metadata_batch=[])

        for item in custom_metadata_batch:
            parent = item.get("parent", {})

            asset_id = parent.get("asset_id")
            filename = parent.get("filename")
            frame = parent.get("frame")

            if not all(
                isinstance(key, str) and isinstance(value, (str, int, float, bool))
                for key, value in item.get("custom_metadata", {}).items()
            ):
                raise ValueError(
                    "custom_metadata must be a dictionary with keys of string, and values of string, int, float, or bool"
                )

            if asset_id and frame:
                custom_metas.custom_metadata_batch.append(
                    AssetCustomMetadata(
                        parent=AssetFrameParent(asset_id=asset_id, frame=frame),
                        custom_metadata=item.get("custom_metadata", {}),
                    )
                )

            elif asset_id and not frame:
                custom_metas.custom_metadata_batch.append(
                    AssetCustomMetadata(
                        parent=AssetParent(asset_id=asset_id),
                        custom_metadata=item.get("custom_metadata", {}),
                    )
                )

            elif filename and frame:
                custom_metas.custom_metadata_batch.append(
                    AssetCustomMetadata(
                        parent=AssetFilenameFrameParent(filename=filename, frame=frame),
                        custom_metadata=item.get("custom_metadata", {}),
                    )
                )

            elif filename and not frame:
                custom_metas.custom_metadata_batch.append(
                    AssetCustomMetadata(
                        parent=AssetFilenameParent(filename=filename),
                        custom_metadata=item.get("custom_metadata", {}),
                    )
                )

            else:
                raise ValueError(
                    "Invalid parent. Parent must contain either asset_id or filename."
                )

        return self.requester.POST(
            f"/projects/{self.project_id}/customMetadataBulkUpdates",
            request_body=custom_metas.to_json(),
            response_type=models.AssetCustomMetadataBatch,
        )

    def delete_custom_metadata_batch(
        self,
        custom_metadata_ids: List[str],
    ) -> models.DeleteCustomMetadataBatchResponse:
        """Delete custom metadata from multiple assets in a single operation.

        This method allows you to delete multiple custom metadata entries across
        different assets in a single batch operation. The custom_metadata_ids can
        be obtained from the get_custom_metadata method for each asset.

        :param custom_metadata_ids: A list of custom metadata IDs to delete.
        :return: A msgspec struct containing the batch deletion response.
                 If the list is empty, returns an empty response.

        :example:
                .. code-block:: python

                        from datature.nexus import Client

                        project = Client("5aa41e8ba........").get_project("proj_b705a........")

                        # Delete multiple custom metadata entries
                        metadata_ids = [
                            "custommeta_customMetadata#assetParent:59d4e65e05e7360235526f75698ef3e0:97a83640-f56d-440c-9095-362de2d12681",
                            "custommeta_customMetadata#assetParent:59d4e65e05e7360235526f75698ef3e0:a0d7813c-47c5-4da0-a6e7-4b73f5539cf5",
                        ]
                        project.assets.delete_custom_metadata_batch(metadata_ids)
        """

        assert isinstance(custom_metadata_ids, list)

        if len(custom_metadata_ids) == 0:
            return models.DeleteCustomMetadataBatchResponse()

        return self.requester.POST(
            f"/projects/{self.project_id}/customMetadataBulkUpdates/delete",
            request_body={"ids": custom_metadata_ids},
            response_type=models.DeleteCustomMetadataBatchResponse,
        )
