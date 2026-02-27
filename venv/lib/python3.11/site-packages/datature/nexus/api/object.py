#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   object.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Datature Object API
"""

from typing import Union

from datature.nexus import models
from datature.nexus.api.types import ObjectFilter, Pagination
from datature.nexus.client_context import RestContext


class Object(RestContext):
    """Datature Object API Resource."""

    def list(
        self,
        pagination: Union[Pagination, dict, None] = None,
        filters: Union[ObjectFilter, dict, None] = None,
        include_attributes: bool = False,
    ) -> models.PaginationResponse[models.Object]:
        """Lists objects in the project.

        :param pagination: Pagination object.
        :param filters: ObjectFilter object.
        :param include_attributes: Include attributes in the response.

        :return: PaginationResponse of an Object containing a list of
            assets and a list of annotations with the following structure:

                .. code-block:: python

                    PaginationResponse(
                        next_page='NjVhYTE0ZDY3YzQ5MThlMTJjYTUyOGRk',
                        prev_page=None,
                        data=Object(
                            annotations=[
                                [
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
                                    ],
                                ],
                                assets=[
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
                                ],
                            ],
                        )
                    )

        :example:
                .. code-block:: python

                        from datature.nexus import Client

                        project = Client("5aa41e8ba........").get_project("proj_b705a........")

                        project.objects.list({
                            "limit": 2,
                                "page": "ZjYzYmJkM2FjN2UxOTA4ZmU0ZjE0Yjk5Mg"
                            }
                        )

        """
        assert isinstance(pagination, (Pagination, dict, type(None)))
        assert isinstance(filters, (ObjectFilter, dict, type(None)))

        if isinstance(pagination, dict):
            pagination = Pagination(**pagination)
        if pagination is None:
            pagination = Pagination()

        if isinstance(filters, dict):
            filters = ObjectFilter(**filters)
        if filters is None:
            filters = ObjectFilter()

        return self.requester.GET(
            f"/projects/{self.project_id}/objects",
            query={
                **pagination.to_json(),
                **filters.to_json(),
                "include_attributes": include_attributes,
            },
            response_type=models.PaginationResponse[models.Object],
        )
