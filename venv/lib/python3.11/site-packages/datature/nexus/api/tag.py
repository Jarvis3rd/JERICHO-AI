#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   tag.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Datature Tag API
"""

from typing import Union

from datature.nexus import models
from datature.nexus.api.types import TagMetadata
from datature.nexus.client_context import RestContext


class Tag(RestContext):
    """Datature Tag API Resource."""

    def list(self) -> models.Tags:
        """Lists all tags in the project.

        :return: A msgspec struct containing tag metadata with the following structure:

            .. code-block:: python

                [Tag(
                    index=0,
                    name='Platelets',
                    color=None,
                    description=None
                )]

        :example:
                .. code-block:: python

                        from datature.nexus import Client

                        project = Client("5aa41e8ba........").get_project("proj_b705a........")
                        project.tags.list()
        """
        return self.requester.GET(
            f"/projects/{self.project_id}/tags", response_type=models.Tags
        )

    def create(self, metadata: Union[TagMetadata, dict]) -> models.Tags:
        """Creates a new tag.
            The indices of new tags created will begin from the last existing tag index.

        :param metadata: The metadata of the new tag.
        :return: An updated msgspec struct containing tag metadata with the following structure:

            .. code-block:: python

                [
                    Tag(
                        index=0,
                        name='boat',
                        color='#7ed957',
                        description='boat'
                    ),
                    Tag(
                        index=1,
                        name='boat2',
                        color='#ff3131',
                        description=None
                    )
                ]


        :example:
            .. code-block:: python

                from datature.nexus import Client, ApiTypes

                project = Client("5aa41e8ba........").get_project("proj_b705a........")

                project.tags.create({"name": "boat2", "color": "#ff3131"}

                # or
                project.tags.create(ApiTypes.TagMetadata(
                                        name="boat2",
                                        color="#ff3131",
                                        description="This is a boat"
                                    ))
        """
        assert isinstance(metadata, (TagMetadata, dict))

        if isinstance(metadata, dict):
            metadata = TagMetadata(**metadata)

        return self.requester.POST(
            f"/projects/{self.project_id}/tags",
            request_body=metadata.to_json(),
            response_type=models.Tags,
        )

    def update(self, index: int, metadata: Union[TagMetadata, dict]) -> models.Tags:
        """Updates the name of a specific tag using the tag index.

        :param index: The index of the tag to update.
        :param metadata: The new metadata of the tag.
        :return: An updated msgspec struct containing tag metadata with the following structure:

            .. code-block:: python

                [
                    Tag(
                        index=0,
                        name='boat',
                        color='#7ed957',
                        description='boat'
                    ),
                    Tag(
                        index=1,
                        name='tagName',
                        color='#ff3131',
                        description=None
                    )
                ]

        :example:
                .. code-block:: python

                        from datature.nexus import Client

                        project = Client("5aa41e8ba........").get_project("proj_b705a........")

                        project.tags.update(1, "tagName")
        """
        assert isinstance(index, int)
        assert isinstance(metadata, (TagMetadata, dict))

        if isinstance(metadata, dict):
            metadata = TagMetadata(**metadata)

        return self.requester.PATCH(
            f"/projects/{self.project_id}/tags/{index}",
            request_body=metadata.to_json(),
            response_type=models.Tags,
        )

    def delete(self, index: int) -> models.DeleteResponse:
        """Deletes a specific tag using the tag index.
            The tag indices of other tags will be left unchanged.
            The indices of new tags created will begin from the last existing tag index.

        :param index: The index of the tag.
        :return: A msgspec struct containing the deletion
            status of the tag with the following structure:

                .. code-block:: python

                    DeleteResponse(deleted=True, id=None)

        :example:
            .. code-block:: python

                from datature.nexus import Client

                project = Client("5aa41e8ba........").get_project("proj_b705a........")

                project.tags.delete(1)
        """
        assert isinstance(index, int)
        return self.requester.DELETE(
            f"/projects/{self.project_id}/tags/{index}",
            response_type=models.DeleteResponse,
        )

    def merge(self, index: int, target_index: int) -> models.Tags:
        """Merges a tag into another tag. .

        :param index: The index of the tag to merge.
        :param target_index: The index of the tag to merge into.
        :return: An updated msgspec struct containing tag
            metadata with the following structure:

            .. code-block:: python

                [Tag(
                    index=0,
                    name='boat',
                    color='#7ed957',
                    description='boat'
                )]

        :example:
            .. code-block:: python

                from datature.nexus import Client

                project = Client("5aa41e8ba........").get_project("proj_b705a........")
                project.tags.merge(1, 0)
        """
        assert isinstance(index, int)
        assert isinstance(target_index, int)

        return self.requester.POST(
            f"/projects/{self.project_id}/tags/{index}-{target_index}:merge",
            response_type=models.Tags,
        )
