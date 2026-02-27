#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   project.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Datature Project API
"""
# pylint: disable=R0902

from abc import ABC
from collections import ChainMap
from inspect import isclass
from typing import Union

from datature.nexus import models
from datature.nexus.api.annotation.annotation import Annotation
from datature.nexus.api.artifact import Artifact
from datature.nexus.api.asset.asset import Asset
from datature.nexus.api.batch.batch import Batch
from datature.nexus.api.deployment import Deployment
from datature.nexus.api.object import Object
from datature.nexus.api.ontology import Ontology
from datature.nexus.api.operation import Operation
from datature.nexus.api.prediction import Prediction
from datature.nexus.api.run import Run
from datature.nexus.api.sequence import Sequence
from datature.nexus.api.tag import Tag
from datature.nexus.api.types import ProjectMetadata
from datature.nexus.api.workflow import Workflow
from datature.nexus.client_context import ClientContext, RestContext


class Project(ABC):
    """Datature Project API Resource."""

    _context: ClientContext
    operations: Operation
    assets: Asset
    annotations: Annotation
    objects: Object
    predictions: Prediction
    tags: Tag
    workflows: Workflow
    artifacts: Artifact
    runs: Run
    deployments: Deployment
    ontologies: Ontology
    batch: Batch
    sequences: Sequence

    def __init__(self, client_context: ClientContext):
        """Initialize the Project API Resource."""
        self.requester = client_context.requester
        self.project_id = client_context.project_id
        self._context = client_context

        # Init sub resources
        self._auto_init_resources()

    def _get_all_annotations(self):
        """Get annotations for this class and all superclasses."""
        # This expression correctly handles cases where multiple superclasses
        # provide different annotations for the same attribute name.
        # See https://stackoverflow.com/a/72037059.
        return ChainMap(
            *(
                c.__annotations__
                for c in self.__class__.__mro__
                if "__annotations__" in c.__dict__
            )
        )

    def _auto_init_resources(self):
        for name, type_annot in self._get_all_annotations().items():
            # Don't overwrite existing fields
            if hasattr(self, name):
                continue

            # Only initialize if the type is a class and a subclass of RestContext
            if not isclass(type_annot) or not issubclass(type_annot, RestContext):
                continue

            setattr(self, name, type_annot(self._context))

    def get_info(self) -> models.Project:
        """Retrieves project information.

        :return: A msgspec struct containing the projects with the following structure:

            .. code-block:: python

                Project(
                    id='proj_9004a21df7b040ace4674c4879603fe8',
                    name='keypoints',
                    workspace_id='ws_1c8aab980f174b0296c7e35e88665b13',
                    type='ObjectDetection',
                    create_date=1701927649302,
                    localization='MULTI',
                    tags=['cat faces'],
                    groups=['main', 'cats'],
                    statistic=Statistic(
                        tags_count=[TagsCountItem(name='cat faces', count=0)],
                        total_assets=28,
                        annotated_assets=0,
                        total_annotations=0
                    )
                )


        :example:
            .. code-block:: python

                from datature.nexus import Client

                project = Client("5aa41e8ba........").get_project("proj_b705a........")
                project.get_info()
        """
        project = self._context.requester.GET(
            f"/projects/{self.project_id}", response_type=models.Project
        )

        return project

    def update(self, project: Union[ProjectMetadata, dict]) -> models.Project:
        """Updates the project with project meta fields.

        :param project: The new metadata of the project to be updated.
        :return: A msgspec struct containing the projects with the following structure:

            .. code-block:: python

                Project(
                    id='proj_9004a21df7b040ace4674c4879603fe8',
                    name='My Cool Project',
                    workspace_id='ws_1c8aab980f174b0296c7e35e88665b13',
                    type='ObjectDetection',
                    create_date=1701927649302,
                    localization='MULTI',
                    tags=['cat faces'],
                    groups=['main', 'cats'],
                    statistic=Statistic(
                        tags_count=[TagsCountItem(name='cat faces', count=0)],
                        total_assets=28,
                        annotated_assets=0,
                        total_annotations=0
                    )
                )

        :example:
            .. code-block:: python

                from datature.nexus import Client, ApiTypes

                project = Client("5aa41e8ba........").get_project("proj_b705a........")

                project.update({"name":"My Cool Project"})
                // Or
                project.update(ApiTypes.ProjectMetadata(name="My Cool Project"))
        """
        assert isinstance(project, (ProjectMetadata, dict))

        if isinstance(project, dict):
            project = ProjectMetadata(**project)

        return self.requester.PATCH(
            f"/projects/{self.project_id}",
            request_body=project.to_json(),
            response_type=models.Project,
        )

    def list_insights(self) -> models.ProjectInsights:
        """Retrieves project insight and metrics of the completed training runs.

        :return: A msgspec struct containing
            the project insights metadata with the following structure:

            .. code-block:: python

                [ProjectInsight(
                    flow_title='Test workflow',
                    run_id='run_4a5d406d-464d-470c-bd7d-e92456621ad3',
                    dataset=InsightDataset(
                        data_type='Rectangle',
                        num_classes=1,
                        average_annotations=5.19,
                        total_assets=500,
                        settings=DatasetSettings(
                            split_ratio=0.3,
                            shuffle=True,
                            seed=0,
                            using_sliding_window=False
                        )
                    ),
                    model=InsightModel(
                        name='fasterrcnn-inceptionv2-1024x1024',
                        batch_size=2,
                        training_steps=5000,
                        max_detection_per_class=100,
                        solver='momentum',
                        learning_rate=0.04,
                        momentum=0.9
                    ),
                    checkpoint=RunCheckpoint(
                        strategy='STRAT_ALWAYS_SAVE_LATEST',
                        evaluation_interval=250,
                        metric=None
                    ),
                    artifact=InsightArtifact(
                        id='artifact_65ae274540259e2a07533532',
                        is_training=False,
                        step=5000,
                        metric=ArtifactMetric(
                            total_loss=0.32356,
                            classification_loss=0.012036,
                            localization_loss=0.010706,
                            regularization_loss=0.0
                        )
                    ),
                    create_date=1705912133684
                )]

        :example:
            .. code-block:: python

                from datature.nexus import Client

                project = Client("5aa41e8ba........").get_project("proj_b705a........")
                project.list_insights()
        """
        return self.requester.GET(
            f"/projects/{self.project_id}/insights",
            response_type=models.ProjectInsights,
        )

    def list_users(self) -> models.ProjectUsers:
        """Retrieves all users in the project.
            This includes Project Owners, Collaborators and Datature Experts.

        :return: A list of msgspec struct containing
            the project user metadata with the following structure:

            .. code-block:: python

                [ProjectUser(
                    id='user_6323fea23e292439f31c58cd',
                    access_type='Owner',
                    email='raighne@datature.io',
                    nickname='raighne',
                    picture='https://s.gravatar.com/avatar/avatars%2Fra.png'
                )]

        :example:
            .. code-block:: python

                from datature.nexus import Client

                project = Client("5aa41e8ba........").get_project("proj_b705a........")
                project.list_users()
        """
        return self.requester.GET(
            f"/projects/{self.project_id}/users", response_type=models.ProjectUsers
        )
