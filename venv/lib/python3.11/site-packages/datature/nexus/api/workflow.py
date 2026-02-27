#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   workflow.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Datature Workflow API
"""

from typing import Union

from datature.nexus import models
from datature.nexus.api.types import FlowMetadata
from datature.nexus.client_context import RestContext


class Workflow(RestContext):
    """Datature Workflow API Resource."""

    def list(self) -> models.Workflows:
        """Lists all workflows in the project.

        :return:
            A list of msgspec structs containing the workflow metadata with the following structure:

                .. code-block:: python

                    [Workflow(
                        id='flow_64e812a7e47592ef374cbbc2',
                        project_id='proj_cd067221d5a6e4007ccbb4afb5966535',
                        title='Yolov8 Workflow',
                        create_date=1701927649302,
                        update_date=1701927649302
                    )]

        :example:
                .. code-block:: python

                    from datature.nexus import Client

                    project = Client("5aa41e8ba........").get_project("proj_b705a........")
                    project.workflows.list()
        """
        return self.requester.GET(
            f"/projects/{self.project_id}/workflows", response_type=models.Workflows
        )

    def get(self, flow_id: str) -> models.Workflow:
        """Retrieves a specific workflow using the flow ID.

        :param flow_id: The ID of the workflow.
        :return:
            A msgspec struct containing the specific workflow metadata with the following structure:

                .. code-block:: python

                    Workflow(
                        id='flow_64e812a7e47592ef374cbbc2',
                        project_id='proj_cd067221d5a6e4007ccbb4afb5966535',
                        title='Yolov8 Workflow',
                        create_date=1701927649302,
                        update_date=1701927649302
                    )


        :example:
                .. code-block:: python

                        from datature.nexus import Client

                        project = Client("5aa41e8ba........").get_project("proj_b705a........")
                        project.workflows.get("flow_639309be08b4488a914b8802")
        """
        assert isinstance(flow_id, str)

        return self.requester.GET(
            f"/projects/{self.project_id}/workflows/{flow_id}",
            response_type=models.Workflow,
        )

    def update(self, flow_id: str, flow: Union[FlowMetadata, dict]) -> models.Workflow:
        """Updates title of a specific workflow using the flow ID.

        :param flow_id: The ID of the workflow.
        :param flow: The new metadata of the workflow to be updated.
        :return: A msgspec struct containing the updated workflow metadata with the following structure:

                .. code-block:: python

                    Workflow(
                        id='flow_64e812a7e47592ef374cbbc2',
                        project_id='proj_cd067221d5a6e4007ccbb4afb5966535',
                        title='My awesome workflow',
                        create_date=1701927649302,
                        update_date=1701927649302
                    )

        :example:
                .. code-block:: python

                        from datature.nexus import Client, ApiTypes

                        project = Client("5aa41e8ba........").get_project("proj_b705a........")

                        project.workflows.update(
                            "flow_639309be08b4488a914b8802",
                            {"title": "My awesome workflow"}
                        )
                        // or
                        project.workflows.update(
                            "flow_639309be08b4488a914b8802",
                            ApiTypes.FlowMetadata(title="My awesome workflow")
                        )
        """
        assert isinstance(flow_id, str)
        assert isinstance(flow, (FlowMetadata, dict))

        if isinstance(flow, dict):
            flow = FlowMetadata(**flow)

        return self.requester.PATCH(
            f"/projects/{self.project_id}/workflows/{flow_id}",
            request_body=flow.to_json(),
            response_type=models.Workflow,
        )

    def delete(self, flow_id: str) -> models.DeleteResponse:
        """Deletes a specific workflow using the flow ID.

        :param flow_id: The ID of the workflow
        :return: A msgspec struct containing the deleted
            workflow ID and deletion status with the following structure:

            .. code-block:: python

                DeleteResponse(deleted=True, id='flow_656d7912092f3395248c7666')

        :example:
            .. code-block:: python

                from datature.nexus import Client

                project = Client("5aa41e8ba........").get_project("proj_b705a........")
                project.workflows.delete("flow_639309be08b4488a914b8802")
        """
        assert isinstance(flow_id, str)

        return self.requester.DELETE(
            f"/projects/{self.project_id}/workflows/{flow_id}",
            response_type=models.DeleteResponse,
        )
