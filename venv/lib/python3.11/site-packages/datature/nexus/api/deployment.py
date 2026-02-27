#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   Deploy.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Datature Deploy API
"""

from typing import Union

from datature.nexus import models
from datature.nexus.api.types import DeploymentMetadata
from datature.nexus.client_context import RestContext


class Deployment(RestContext):
    """Datature Deploy API Resource."""

    def list(self) -> models.Deployments:
        """Lists all deployments in a project.

        :return: A list of msgspec structs containing
            deployment metadata with the following structure:

            .. code-block:: python

                [Deployment(
                    id='deploy_1c144673-c757-40b4-8eeb-d400f0b9b2f9',
                    name='My API',
                    project_id='proj_cd067221d5a6e4007ccbb4afb5966535',
                    artifact_id='artifact_65a7678a91afa7d22455c5ba',
                    version_tag='v1.0.0',
                    history_versions=[
                        DeploymentHistoryVersion(
                            version_tag='v1.0.0',
                            artifact_id='artifact_65a7678a91afa7d22455c5ba',
                            update_date=1705475663570
                        )
                    ],
                    resources=DeploymentResources(
                        cpu=4,
                        ram=8192,
                        GPU_T4=None
                    ),
                    scaling=DeploymentScaling(
                        replicas=1,
                        mode='FixedReplicaCount'
                    ),
                    status=DeploymentStatus(
                        overview='Available',
                        message='Created service successfully',
                        update_data=1705475727032
                    ),
                    create_date=1705475663570,
                    update_date=1705475727051,
                    url='https://asia-inference.nip.io/1c144673-c757-40b4-8eeb-d400f0b9b2f9'
                )]

        :example:
                .. code-block:: python

                        from datature.nexus import Client

                        project = Client("5aa41e8ba........").get_project("proj_b705a........")
                        project.deployments.list()
        """
        return self.requester.GET(
            f"/projects/{self.project_id}/deployments", response_type=models.Deployments
        )

    def get(self, deploy_id: str) -> models.Deployment:
        """Retrieves a specific deployment using the deployment ID.

        :param deploy_id: The ID of the deployment as a string.
        :return: A msgspec struct containing the
            specific deployment metadata with the following structure:

            .. code-block:: python

                Deployment(
                    id='deploy_1c144673-c757-40b4-8eeb-d400f0b9b2f9',
                    name='My API',
                    project_id='proj_cd067221d5a6e4007ccbb4afb5966535',
                    artifact_id='artifact_65a7678a91afa7d22455c5ba',
                    version_tag='v1.0.0',
                    history_versions=[
                        DeploymentHistoryVersion(
                            version_tag='v1.0.0',
                            artifact_id='artifact_65a7678a91afa7d22455c5ba',
                            update_date=1705475663570
                        )
                    ],
                    resources=DeploymentResources(
                        cpu=4,
                        ram=8192,
                        GPU_T4=None
                    ),
                    scaling=DeploymentScaling(
                        replicas=1,
                        mode='FixedReplicaCount'
                    ),
                    status=DeploymentStatus(
                        overview='Available',
                        message='Created service successfully',
                        update_data=1705475727032
                    ),
                    create_date=1705475663570,
                    update_date=1705475727051,
                    url='https://asia-inference.nip.io/1c144673-c757-40b4-8eeb-d400f0b9b2f9'
                )

        :example:
            .. code-block:: python

                from datature.nexus import Client

                project = Client("5aa41e8ba........").get_project("proj_b705a........")
                project.deployments.get("deploy_1c144673-c757-40b4-8eeb-d400f0b9b2f9")
        """
        assert isinstance(deploy_id, str)
        return self.requester.GET(
            f"/projects/{self.project_id}/deployments/{deploy_id}",
            response_type=models.Deployment,
        )

    def delete(self, deploy_id: str) -> models.DeleteResponse:
        """Deletes a specific deployment from the project.

        :param deploy_id: The id of the deployment.
        :return: A msgspec struct containing the deleted
            deployment ID and the deletion status with the following structure:

            .. code-block:: python

                DeleteResponse(deleted=True, id="deploy_30922d5e-b2f6-43dc-b7b4-e29e2c30fb45")

        :example:
            .. code-block:: python

                from datature.nexus import Client

                project = Client("5aa41e8ba........").get_project("proj_b705a........")
                project.deployments.delete("deploy_30922d5e-b2f6-43dc-b7b4-e29e2c30fb45")
        """
        assert isinstance(deploy_id, str)
        return self.requester.DELETE(
            f"/projects/{self.project_id}/deployments/{deploy_id}",
            response_type=models.DeleteResponse,
        )

    def create(self, deployment: Union[DeploymentMetadata, dict]) -> models.Deployment:
        """Creates a deployment for a specific model using the model ID.

        :param deployment: The configuration metadata of the deployment.
        :return: A msgspec struct containing the specific
            deployment metadata with the following structure:

            .. code-block:: python

                Deployment(
                    id='deploy_1c144673-c757-40b4-8eeb-d400f0b9b2f9',
                    name='My API',
                    project_id='proj_cd067221d5a6e4007ccbb4afb5966535',
                    artifact_id='artifact_65a7678a91afa7d22455c5ba',
                    version_tag='v1.0.0',
                    history_versions=[
                        DeploymentHistoryVersion(
                            version_tag='v1.0.0',
                            artifact_id='artifact_65a7678a91afa7d22455c5ba',
                            update_date=1705475663570
                        )
                    ],
                    resources=DeploymentResources(
                        cpu=4,
                        ram=8192,
                        GPU_T4=None
                    ),
                    scaling=DeploymentScaling(
                        replicas=1,
                        mode='FixedReplicaCount'
                    ),
                    status=DeploymentStatus(
                        overview='Creating',
                        message='Creating service.',
                        update_data=1705475727032
                    ),
                    create_date=1705475663570,
                    update_date=1705475727051,
                    url=None
                )

        :example:
            .. code-block:: python

                from datature.nexus import Client

                project = Client("5aa41e8ba........").get_project("proj_b705a........")

                project.deployments.create({
                    "name": "My First API",
                    "artifact_id": "artifact_63fd950a64845427a706d57c",
                    "version_tag": "car.staging.v3",
                })
        """
        assert isinstance(deployment, (DeploymentMetadata, dict))

        if isinstance(deployment, dict):
            deployment = DeploymentMetadata(**deployment)

        if deployment.instance_id:
            available_instances = self.requester.GET(
                f"/projects/{self.project_id}/artifacts/{deployment.artifact_id}"
                f"/availableInstances/regions/{deployment.region if deployment.region else '*'}",
                response_type=models.AvailableInstances,
            )
            available_instance_ids = [
                instance.id for instance in available_instances.instances
            ]
            if deployment.instance_id not in available_instance_ids:
                raise ValueError(
                    f"Instance {deployment.instance_id} is not available. Available instances: "
                    f"{available_instance_ids}"
                )

        return self.requester.POST(
            f"/projects/{self.project_id}/deployments",
            request_body=deployment.to_json(),
            response_type=models.Deployment,
        )

    def update(
        self, deploy_id: str, deployment: Union[DeploymentMetadata, dict]
    ) -> models.Deployment:
        """Creates a deployment for a specific model using the model ID.

        :param deploy_id: The ID of the deployment as a string.
        :param deployment: The configuration metadata of the deployment.
        :return: A msgspec struct containing the
            specific deployment metadata with the following structure:

            .. code-block:: python

                Deployment(
                    id='deploy_1c144673-c757-40b4-8eeb-d400f0b9b2f9',
                    name='My First API v2',
                    project_id='proj_cd067221d5a6e4007ccbb4afb5966535',
                    artifact_id='artifact_65a7678a91afa7d22455c5ba',
                    version_tag='v1.0.0',
                    history_versions=[DeploymentHistoryVersion(
                        version_tag='v1.0.0',
                        artifact_id='artifact_65a7678a91afa7d22455c5ba',
                        update_date=1705475663570
                    )],
                    resources=DeploymentResources(
                        cpu=4,
                        ram=8192,
                        GPU_T4=1
                    ),
                    scaling=DeploymentScaling(
                        replicas=1,
                        mode='FixedReplicaCount'
                    ),
                    status=DeploymentStatus(
                        overview='Creating',
                        message='Creating service',
                        update_data=1705475679244
                    ),
                    create_date=1705475663570,
                    update_date=1705477694540,
                    url=None
                )

        :example:

            .. code-block:: python

                from datature.nexus import Client

                project = Client("5aa41e8ba........").get_project("proj_b705a........")

                datature.deployments.update(
                    "deploy_30922d5e-b2f6-43dc-b7b4-e29e2c30fb45",
                    {
                        "name": "My First API v2",
                        "options": {
                            "evaluation_threshold": 0.8
                        }
                        "resources":{
                            "GPU_T4":1
                        }
                })
        """
        assert isinstance(deployment, (DeploymentMetadata, dict))

        if isinstance(deployment, dict):
            deployment = DeploymentMetadata(**deployment)

        return self.requester.PATCH(
            f"/projects/{self.project_id}/deployments/{deploy_id}",
            request_body=deployment.to_json(),
            response_type=models.Deployment,
        )

    def create_version(
        self, deploy_id: str, version_tag: str, artifact_id: str
    ) -> models.Deployment:
        """Updates a deployment version for a specific artifact using the artifact ID.

        :param deploy_id: The ID of the deployment as a string.
        :param version_tag: The new version tag name of the deployment.
        :param artifact_id: The ID of the artifact as a string.
        :return: A msgspec struct containing the specific
            deployment metadata with the following structure:

            .. code-block:: python

                Deployment(
                    id='deploy_1c144673-c757-40b4-8eeb-d400f0b9b2f9',
                    name='My API',
                    project_id='proj_cd067221d5a6e4007ccbb4afb5966535',
                    artifact_id='artifact_65a75d4891afa7d22455c54d',
                    version_tag='v2.0.0',
                    history_versions=[
                        DeploymentHistoryVersion(
                            version_tag='v1.0.0',
                            artifact_id='artifact_65a7678a91afa7d22455c5ba',
                            update_date=1705475663570
                        ),
                        DeploymentHistoryVersion(
                            version_tag='v2.0.0',
                            artifact_id='artifact_65a75d4891afa7d22455c54d',
                            update_date=1705477973476
                        )
                    ],
                    resources=DeploymentResources(
                        cpu=4,
                        ram=8192,
                        GPU_T4=1
                    ),
                    scaling=DeploymentScaling(
                        replicas=1,
                        mode='FixedReplicaCount'
                    ),
                    status=DeploymentStatus(
                        overview='Creating',
                        message='Creating service',
                        update_data=1705475679244
                    ),
                    create_date=1705475663570,
                    update_date=1705477694540,
                    url=None
                )

        :example:
            .. code-block:: python

                from datature.nexus import Client

                project = Client("5aa41e8ba........").get_project("proj_b705a........")

                project.deployments.create_version(
                    "deploy_30922d5e-b2f6-43dc-b7b4-e29e2c30fb45",
                    "v2.0.0",
                    "artifact_63fd950a64845427a706d57d"
                )
        """
        assert isinstance(deploy_id, str)
        assert isinstance(version_tag, str)
        assert isinstance(artifact_id, str)

        return self.requester.POST(
            f"/projects/{self.project_id}/deployments/{deploy_id}/versions",
            request_body={
                "versionTag": version_tag,
                "artifactId": artifact_id,
            },
            response_type=models.Deployment,
        )
