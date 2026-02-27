#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   prediction.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Datature Prediction API
"""

from typing import Union

from datature.nexus import models
from datature.nexus.api.types import Pagination, PredictionFilter
from datature.nexus.client_context import RestContext


class Prediction(RestContext):
    """Datature Prediction API Resource."""

    def list(
        self,
        pagination: Union[Pagination, dict, None] = None,
        filters: Union[PredictionFilter, dict, None] = None,
    ) -> models.PaginationResponse[models.Prediction]:
        """Lists predictions in the project.

        :param pagination: Pagination object.
        :param filters: PredictionFilter object.

        :return: PaginationResponse containing a list of predictions with the following structure:

                .. code-block:: python

                    PaginationResponse(
                        next_page='NjVhYTE0ZDY3YzQ5MThlMTJjYTUy',
                        prev_page=None,
                        data=[
                            Prediction(
                                predictions=[
                                    PredictionObject(
                                        id='prediction_1d5f2062-0638-41d4-8317-b46f226b7ee9:241',
                                        object='prediction',
                                        prediction_slice=PredictionSlice(
                                            project='proj_ca5fe71e7592bbcf7705ea36e4f29ed4',
                                            asset_id='asset_facf5eee-89a8-41f4-a958-95d54708e590',
                                            filename='29.jpg',
                                            slice=[],
                                            snapshot_id='snapshot_1d5f2062-0638-41d4-8317-b46f226b7ee9',
                                            run_id='run_4eecc30d-ac18-4821-96c5-239e97e96d6c',
                                            artifact_id='artifact_67a9a6fe9841727bfcc9c847',
                                            id='predictionslice_adc613a5-aa32-4c0f-86a1-5d5637c3bd26',
                                            prediction_metadata=PredictionSliceMetadata(
                                                average_confidence=0.79,
                                                average_confidence_for_tag=[
                                                'RBC',
                                                'WBC',
                                                'Platelets'
                                                ],
                                                prediction_count=26,
                                                prediction_count_for_tag=[
                                                'Background',
                                                'RBC',
                                                'Platelets',
                                                'WBC'
                                                ]
                                            )
                                        ),
                                        metadata=PredictionMetadata(
                                            average_confidence=0.25
                                        ),
                                        tag=Tag(
                                            index=1,
                                            name='RBC',
                                            color='#38b6ff',
                                            description=None
                                        ),
                                        bound=[
                                            'boundType',
                                            'rectangle'
                                        ],
                                    )
                                ],
                            )
                        ]

        :example:
                .. code-block:: python

                        from datature.nexus import Client

                        project = Client("5aa41e8ba........").get_project("proj_b705a........")

                        project.predictions.list(
                            filters={
                                "prediction_filter": '''
                                {
                                    "and": [
                                        {
                                        "=": [
                                            {
                                            "var": "run"
                                            },
                                            "run_4eecc30d-ac18-4821-96c5-239e97e96d6c"
                                        ]
                                        }
                                    ]
                                }
                                '''
                            }
                        )
        """
        assert isinstance(pagination, (Pagination, dict, type(None)))
        assert isinstance(filters, (PredictionFilter, dict, type(None)))

        if isinstance(pagination, dict):
            pagination = Pagination(**pagination)
        if pagination is None:
            pagination = Pagination()

        if isinstance(filters, dict):
            filters = PredictionFilter(**filters)
        if filters is None:
            filters = PredictionFilter()

        return self.requester.GET(
            f"/projects/{self.project_id}/predictions",
            query={**pagination.to_json(), **filters.to_json()},
            response_type=models.PaginationResponse[models.Prediction],
        )
