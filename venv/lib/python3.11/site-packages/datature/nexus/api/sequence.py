#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   sequence.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Datature Sequence API
"""

from typing import List, Union

from datature.nexus import models
from datature.nexus.api.operation import Operation
from datature.nexus.api.types import (
    Pagination,
    SequenceBulkUpdateAbortMode,
    SequenceBulkUpdateAction,
    SequenceBulkUpdateActionLink,
    SequenceBulkUpdateActionPatchSequence,
    SequenceBulkUpdateActionRemoveSequence,
    SequenceFilter,
    SequencePatch,
)
from datature.nexus.client_context import ClientContext, RestContext


class Sequence(RestContext):
    """Datature Sequence API Resource."""

    def __init__(self, client_context: ClientContext):
        """Initialize the API Resource."""
        super().__init__(client_context)
        self.operation = Operation(client_context)

    def list(
        self,
        pagination: Union[Pagination, dict, None] = None,
        filters: Union[SequenceFilter, dict, None] = None,
    ) -> models.PaginationResponse[models.Sequence]:
        """Retrieves a list of all sequences in the project.

        :param pagination: A dictionary containing the limit of
                            the number of sequences to be returned in each page (defaults to 100),
                            and the page number (defaults to 1).
        :param filters: A dictionary containing the filters to be applied to the sequences.

        :return: A msgspec struct of pagination response with the following structure:

                .. code-block:: python

                        PaginationResponse(
                            next_page='T2YAGDY1NWFlNDcyMzZkiMDYwMTQ5N2U2',
                            prev_page=None,
                            data=[
                                Sequence(
                                    id="seq_f77a1a3d-2ea2-45fc-a3f5-dc916a56f28c",
                                    name="Patient A",
                                    project_id="proj_cd067221d5a6e4007ccbb4afb5966535",
                                    items=[
                                        SequenceEntryAsset(
                                            asset_id="asset_b5dff11f-6f70-4642-a85b-56f6f6922ac1",
                                            ord=3,
                                            role="Sagittal"
                                        ),
                                        SequenceEntryAsset(
                                            asset_id="asset_fe8ca0ce-654e-4f33-929c-09aa9243850f",
                                            ord=6,
                                            role="Sagittal"
                                        ),
                                    ],
                                    attributes=SequenceAttributes(
                                        bytes_used=20,
                                        bytes_total=1048576,
                                        items={
                                            "report0": "...",
                                            "report1": "...",
                                        }
                                    ),
                                    create_date=1705475663570,
                                    update_date=1705475727051
                                )
                            ]
                        )

        :example:
                .. code-block:: python

                        from datature.nexus import Client

                        project = Client("5aa41e8ba........").get_project("proj_b705a........")

                        project.sequences.list()

                        # or
                        project.sequences.list(
                            nexus.ApiTypes.Pagination(
                                limit= 2,
                                page="ZjYzYmJkM2FjN2UxOTA4ZmU0ZjE0Yjk5Mg"
                            ),
                        )

        """
        assert isinstance(pagination, (Pagination, dict, type(None)))
        assert isinstance(filters, (SequenceFilter, dict, type(None)))

        if isinstance(pagination, dict):
            pagination = Pagination(**pagination)
        if pagination is None:
            pagination = Pagination()

        if isinstance(filters, dict):
            filters = SequenceFilter(**filters)
        if filters is None:
            filters = SequenceFilter()

        return self.requester.GET(
            f"/projects/{self.project_id}/sequences",
            query={**pagination.to_json(), **filters.to_json()},
            response_type=models.PaginationResponse[models.Sequence],
        )

    def get(self, sequence_id: str) -> models.Sequence:
        """Retrieves a sequence by its ID.

        :param sequence_id: The ID of the sequence to retrieve.
        :return: A msgspec struct of sequence with the following structure:

                .. code-block:: python

                        Sequence(
                            id="seq_f77a1a3d-2ea2-45fc-a3f5-dc916a56f28c",
                            name="Patient A",
                            project_id="proj_cd067221d5a6e4007ccbb4afb5966535",
                            items=[
                                SequenceEntryAsset(
                                    asset_id="asset_b5dff11f-6f70-4642-a85b-56f6f6922ac1",
                                    ord=3,
                                    role="Sagittal"
                                ),
                                SequenceEntryAsset(
                                    asset_id="asset_fe8ca0ce-654e-4f33-929c-09aa9243850f",
                                    ord=6,
                                    role="Sagittal"
                                ),
                            ],
                            attributes=SequenceAttributes(
                                bytes_used=20,
                                bytes_total=1048576,
                                items={
                                    "report0": "...",
                                    "report1": "...",
                                }
                            ),
                            create_date=1705475663570,
                            update_date=1705475727051
                        )

        :example:
                .. code-block:: python

                        from datature.nexus import Client

                        project = Client("5aa41e8ba........").get_project("proj_b705a........")
                        sequence = project.sequences.get("seq_f77a1a3d-2ea2-45fc-a3f5-dc916a56f28c")
        """
        assert isinstance(sequence_id, str)
        return self.requester.GET(
            f"/projects/{self.project_id}/sequences/{sequence_id}",
            response_type=models.Sequence,
        )

    def bulk_update(
        self,
        actions: List[Union[SequenceBulkUpdateAction, dict]],
        abort_mode: SequenceBulkUpdateAbortMode = SequenceBulkUpdateAbortMode.NONE,
    ) -> models.SequenceBulkUpdateResults:
        """Update sequences in bulk via a list of actions.

        :param actions: A list of actions to update the sequences.
        :param abort_mode: The abort mode to use when handling update errors.
        :return: A msgspec struct of sequence bulk update results with the following structure:

                .. code-block:: python

                        SequenceBulkUpdateResults(
                            actions=[
                                <SequenceBulkUpdateResult.OK: 'Ok'>,
                                <SequenceBulkUpdateResult.FAILED_LINK_ASSET_NOT_FOUND: 'FailedLinkAssetNotFound'>,
                            ]
                        )

        :example:
                .. code-block:: python

                        from datature.nexus import Client

                        project = Client("5aa41e8ba........").get_project("proj_b705a........")

                        project.sequences.bulk_update(
                            actions=[
                                {
                                    "sequence": {
                                        "name": "Patient A",
                                        "role": "Sagittal",
                                        "ord": 1,
                                    },
                                    "asset_filename": "image_1.jpg",
                                },
                                {
                                    "sequence": {
                                        "name": "Patient A",
                                        "role": "Sagittal",
                                        "ord": 2,
                                    },
                                    "asset_filename": "image_2.jpg",
                                },
                                {
                                    "patch": {
                                        "attributes": {
                                            "age": 20,
                                            "gender": "male",
                                            "height": 180,
                                            "weight": 70,
                                        },
                                    },
                                    "sequence_name": "Patient A",
                                },
                            ]
                        )
        """
        assert isinstance(actions, list)
        assert isinstance(abort_mode, SequenceBulkUpdateAbortMode)

        processed_actions = []

        for action in actions:
            if isinstance(action, dict):
                if action.get("asset_id") or action.get("asset_filename"):
                    action = SequenceBulkUpdateActionLink(**action)
                elif action.get("sequence_id") or action.get("sequence_name"):
                    if action.get("patch"):
                        action = SequenceBulkUpdateActionPatchSequence(**action)
                    else:
                        action = SequenceBulkUpdateActionRemoveSequence(**action)
                else:
                    raise ValueError(f"Invalid action: {action}")

            processed_actions.append(action)

        return self.requester.POST(
            f"/projects/{self.project_id}/sequencesBulkUpdates",
            request_body={
                "actions": [action.to_json() for action in processed_actions],
                "abortMode": abort_mode.value,
            },
            response_type=models.SequenceBulkUpdateResults,
        )

    def patch(
        self, sequence_id: str, patch: Union[SequencePatch, dict]
    ) -> models.Sequence:
        """Updates a sequence by its ID.

        :param sequence_id: The ID of the sequence to update.
        :param patch: A msgspec struct of sequence patch with the following structure:
        :return: A msgspec struct of sequence with the following structure:

                .. code-block:: python

                        Sequence(
                            id="seq_f77a1a3d-2ea2-45fc-a3f5-dc916a56f28c",
                            name="Patient A",
                            project_id="proj_cd067221d5a6e4007ccbb4afb5966535",
                            items=[
                                SequenceEntryAsset(
                                    asset_id="asset_b5dff11f-6f70-4642-a85b-56f6f6922ac1",
                                    ord=3,
                                    role="Sagittal"
                                ),
                                SequenceEntryAsset(
                                    asset_id="asset_fe8ca0ce-654e-4f33-929c-09aa9243850f",
                                    ord=6,
                                    role="Sagittal"
                                ),
                            ],
                            attributes=SequenceAttributes(
                                bytes_used=20,
                                bytes_total=1048576,
                                items={
                                    "report0": "...",
                                    "report1": "...",
                                }
                            ),
                            create_date=1705475663570,
                            update_date=1705475727051
                        )

        :example:
                .. code-block:: python

                        from datature.nexus import Client

                        project = Client("5aa41e8ba........").get_project("proj_b705a........")

                        project.sequences.patch(
                            "seq_f77a1a3d-2ea2-45fc-a3f5-dc916a56f28c",
                            {
                                "name": "Patient A",
                                "attributes": {
                                    "age": 20,
                                    "gender": "male",
                                    "height": 180,
                                    "weight": 70,
                                },
                            }
                        )
        """
        assert isinstance(sequence_id, str)
        assert isinstance(patch, (SequencePatch, dict))

        if isinstance(patch, dict):
            patch = SequencePatch(**patch)

        return self.requester.PATCH(
            f"/projects/{self.project_id}/sequences/{sequence_id}",
            request_body=patch.to_json(),
            response_type=models.Sequence,
        )

    def delete(self, sequence_id: str) -> models.DeleteResponse:
        """Deletes a sequence by its ID.

        :param sequence_id: The ID of the sequence to delete.
        :return: A msgspec struct of delete response with the following structure:

                .. code-block:: python

                        DeleteResponse(deleted=True, id='seq_f77a1a3d-2ea2-45fc-a3f5-dc916a56f28c')

        :example:
                .. code-block:: python

                        from datature.nexus import Client

                        project = Client("5aa41e8ba........").get_project("proj_b705a........")

                        project.sequences.delete("seq_f77a1a3d-2ea2-45fc-a3f5-dc916a56f28c")
        """
        assert isinstance(sequence_id, str)
        return self.requester.DELETE(
            f"/projects/{self.project_id}/sequences/{sequence_id}",
            response_type=models.DeleteResponse,
        )
