#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   ontology.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Datature Ontology API
"""
# pylint: disable=R0903

from typing import List, Union

from datature.nexus import models
from datature.nexus.api.types import OntologyAttribute, OntologyMetadata
from datature.nexus.client_context import RestContext


class Ontology(RestContext):
    """Datature ontology API Resource."""

    def list_schemas(self) -> models.Ontologies:
        """Lists all training runs regardless of status.

        :return: A msgspec struct containing
            the ontology metadata with the following structure:

            .. code-block:: json

                [Ontology(
                    id='ontology_843e486c-58d7-45a7-b722-f4948e204a56',
                    project_id='proj_cd067221d5a6e4007ccbb4afb5966535',
                    index=1,
                    name='car',
                    color='#c1ff72',
                    description='Cars',
                    attributes=[OntologyAttribute(
                      id='attri_d0877827-63d6-4794-b520-ef3e0c57ef71',
                      name='brand',
                      description='Brand of the car',
                      type='Categorical',
                      options=OntologyAttributeOptions(
                        categories=['Toyota', 'Ford']
                      ),
                      default='Toyota'
                    )]
                )]

        :example:
            .. code-block:: python

            from datature.nexus import Client

            project = Client("5aa41e8ba........").get_project("proj_b705a........")

            ontologies = project.ontologies.list_schemas()
        """
        return self.requester.GET(
            f"/projects/{self.project_id}/ontologies", response_type=models.Ontologies
        )

    def create_schema(
        self, tag_index: int, attributes: List[Union[OntologyAttribute, dict]]
    ) -> models.Ontology:
        """Create an ontology schema. This function will throw an error if a schema
        already exists for the given tag index. Note that valid attribute names should not
        contain preceding or trailing spaces, dots (.), or dollar signs ($).

        :param tag_index: The tag index to create a new schema.
        :param attributes: The ontology attributes to set for this tag.
        :return: A msgspec struct containing the ontology metadata with the following structure:

            .. code-block:: json

                Ontology(
                    id='ontology_843e486c-58d7-45a7-b722-f4948e204a56',
                    project_id='proj_cd067221d5a6e4007ccbb4afb5966535',
                    index=1,
                    name='car',
                    color='#c1ff72',
                    description='Cars',
                    attributes=[OntologyAttribute(
                      id='attri_d0877827-63d6-4794-b520-ef3e0c57ef71',
                      name='brand',
                      description='Brand of the car',
                      type='Categorical',
                      options=OntologyAttributeOptions(
                        categories=['Toyota', 'Ford']
                      ),
                      default='Toyota'
                    )]
                )

        :example:
            .. code-block:: python

                from datature.nexus import Client

                project = Client("5aa41e8ba........").get_project("proj_b705a........")

                project.ontologies.create_schema(1, [{
                    "name": "brand",
                    "description": "Brand of the car",
                    "type": "Categorical",
                    "options": {
                        "categories": ["Toyota", "Ford"]
                    },
                    "default": "Toyota"
                }])
        """

        metadata = OntologyMetadata(attributes=attributes)

        return self.requester.PUT(
            f"/projects/{self.project_id}/ontologies/{tag_index}",
            request_body=metadata.to_json(),
            response_type=models.Ontology,
        )
