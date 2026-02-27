#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   client.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   SDK Client module
"""
# pylint: disable=C0103

import copy
import os
from abc import ABC
from typing import List, Optional, Union

from datature.nexus import models
from datature.nexus.api.project import Project
from datature.nexus.api.types import ArtifactFilters
from datature.nexus.client_context import ClientContext


class Client(ABC):
    """Initialize the Datature client with a secret key and an API endpoint.

    Parameters:
        secret_key (str): The secret key used for authentication with the Datature API.
        endpoint (str): The base URL for the Datature API.
            Defaults to the value of the DATATURE_API_BASE_URL environment variable,
            or "https://api.datature.io" if the environment variable is not set.
    """

    _context: ClientContext

    def __init__(
        self,
        secret_key: Optional[str] = None,
        mtls_certificate_file_path: Optional[str] = None,
        mtls_private_key_file_path: Optional[str] = None,
        endpoint: str = os.getenv("DATATURE_API_BASE_URL", "https://api.datature.io"),
    ):
        """Initialize"""
        self._context = ClientContext(
            secret_key, mtls_certificate_file_path, mtls_private_key_file_path, endpoint
        )

    def get_info(self) -> models.Workspace:
        """Retrieve this workspace.

        :return: A msgspec struct containing the workspace information with the following structure:

            .. code-block:: python

                Workspace(
                    id='ws_1c8aab980f174b0296c7e35e88665b13',
                    name="Raighne's Workspace",
                    owner='user_6323fea23e292439f31c58cd',
                    tier='Developer',
                    create_date=1701927649302
                )

        :example:

            .. code-block:: python

                from datature.nexus import Client

                client = Client("5aa41e8ba........")
                client.get_info()
        """
        return self._context.requester.GET("/workspace", response_type=models.Workspace)

    def list_projects(self) -> List[Project]:
        """List all projects under this workspace.

        :return: A List of project class instances.
        :example:

            .. code-block:: python

                from datature.nexus import Client

                projects = Client("5aa41e8ba........").list_projects()

                for project in projects:
                    print(project.get_info())
        """
        projects = self._context.requester.GET(
            "/workspace/projects", response_type=models.Projects
        )

        projects_res = []
        for project in projects:
            project_context = copy.deepcopy(self._context)
            project_context.project_id = project.id
            projects_res.append(Project(project_context))

        return projects_res

    def get_project(self, project_id: str) -> Project:
        """Return a project object with a separate context.

        :param project_id: The project ID.
        :return: A class instance of the project.
        :example:

            .. code-block:: python

                from datature.nexus import Client

                project = Client("5aa41e8ba........").get_project("proj_b705a........")
        """
        assert isinstance(project_id, str)

        if not project_id.startswith("proj_"):
            project_id = f"proj_{project_id}"

        project_context = copy.deepcopy(self._context)
        project_context.project_id = project_id

        return Project(project_context)

    def list_artifacts(
        self,
        filters: Union[ArtifactFilters, dict] = None,
    ) -> models.Artifacts:
        """Lists all artifacts in the workspace.

        :return: A list of msgspec structs containing
            the artifact metadata with the following structure:

            .. code-block:: python

                [Artifact(
                    id='artifact_65ae274540259e2a07533532',
                    project_id='proj_ecfb4589d153999ba9ce01f54568fa72',
                    run_id='run_4a5d406d-464d-470c-bd7d-e92456621ad3',
                    flow_title='Test workflow',
                    artifact_name='ckpt-20',
                    create_date=1705912133684,
                    is_training=False,
                    step=5000,
                    is_deployed=False,
                    metric=ArtifactMetric(
                        total_loss=0.32356,
                        classification_loss=0.012036,
                        localization_loss=0.010706,
                        regularization_loss=0.0
                    ),
                    model_name='fasterrcnn-inceptionv2-1024x1024',
                    export_options=[
                        ArtifactExportOptions(
                            format='ONNX',
                            optimizations=ArtifactExportOptimizations(
                                quantization=['float32', 'float16']
                            ),
                            default_optimizations=ArtifactExportOptimizations(
                                quantization='float32'
                            )
                        ),
                        ArtifactExportOptions(
                            format='TensorFlow',
                            optimizations=ArtifactExportOptimizations(
                                quantization=['float32']
                            ),
                            default_optimizations=ArtifactExportOptimizations(
                                quantization='float32'
                            )
                        ),
                    ],
                    exports=None
                )]

        :example:
            .. code-block:: python

                from datature.nexus import Client

                workspace_artifacts = Client("5aa41e8ba........").list_artifacts()
        """
        assert isinstance(filters, (ArtifactFilters, dict, type(None)))

        if isinstance(filters, dict):
            filters = ArtifactFilters(**filters)
        if filters is None:
            filters = ArtifactFilters()

        workspace_id = self.get_info().id

        return self._context.requester.GET(
            f"/workspaces/{workspace_id}/artifacts",
            query={**filters.to_json()},
            response_type=models.Artifacts,
        )
