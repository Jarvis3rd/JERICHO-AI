#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   k8s_config.py
@Author  :   Wei Loon Cheng, Kai Xuan Lee
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Custom runner config functions.
"""

import os
import uuid
from pathlib import Path

from datature.nexus.cli.runner import messages as MESSAGES
from datature.nexus.cli.runner.common import install_pip_package
from datature.nexus.cli.runner.config import RunnerConfig
from datature.nexus.cli.runner.consts import (
    RUNNER_DEPLOYMENT_CONFIG_NAME,
    RUNNER_DEPLOYMENT_NAME,
)
from datature.nexus.error import Error

try:
    from kubernetes import client as k8s_client
except ImportError as exc:
    if not install_pip_package("kubernetes"):
        raise Error(
            MESSAGES.INSTALL_PIP_PACKAGE_ERROR_MESSAGE.format(package_name="kubernetes")
        ) from exc
    from kubernetes import client as k8s_client


def get_resource_config(runner_config: RunnerConfig) -> dict:
    """Get resource configuration for runner.

    :param runner_config (RunnerConfig): Runner configuration.
    :return (dict): Resource configuration.
    """
    accelerators = [
        {
            "kind": "NvidiaGpu",
            "id": gpu.device_uuid,
            "name": gpu.device_name,
            "driverVersion": gpu.device_driver_version,
            "totalVramBytes": gpu.device_vram_bytes,
            "computeCapability": gpu.device_compute_capability,
            **({"cudaCores": 1024} if gpu.device_cuda_cores is not None else {}),
        }
        for gpu in runner_config.gpus
    ]

    return {
        "id": runner_config.id,
        "metadata": {"attributes": {"displayName": runner_config.name}},
        "spec": {
            "suspended": False,
            "workers": [
                {
                    "kind": "KubernetesNode",
                    "id": str(uuid.uuid4()),
                    "resources": {
                        "cpu": runner_config.system_specs.num_cores,
                        "memoryBytes": runner_config.system_specs.ram_total,
                        "accelerators": accelerators,
                    },
                }
            ],
        },
    }


def get_role(namespace: str) -> k8s_client.V1Role:
    """Get role for runner.

    :param namespace (str): Role namespace.
    :return (k8s_client.V1Role): Role.
    """
    return k8s_client.V1Role(
        kind="Role",
        api_version="rbac.authorization.k8s.io/v1",
        metadata=k8s_client.V1ObjectMeta(name="python-job-role", namespace=namespace),
        rules=[
            k8s_client.V1PolicyRule(
                api_groups=["batch", "extensions"],
                resources=["jobs"],
                verbs=[
                    "get",
                    "list",
                    "watch",
                    "create",
                    "update",
                    "patch",
                    "delete",
                ],
            ),
            k8s_client.V1PolicyRule(
                api_groups=[""], resources=["pods"], verbs=["get", "list", "watch"]
            ),
            k8s_client.V1PolicyRule(
                api_groups=[""], resources=["pods/log"], verbs=["get", "list", "watch"]
            ),
        ],
    )


def get_role_binding(namespace: str) -> k8s_client.V1RoleBinding:
    """Get role binding for runner.

    :param namespace (str): Role binding namespace.
    :return (k8s_client.V1RoleBinding): Role binding.
    """
    return k8s_client.V1RoleBinding(
        api_version="rbac.authorization.k8s.io/v1",
        kind="RoleBinding",
        metadata=k8s_client.V1ObjectMeta(
            name="python-job-rolebinding", namespace=namespace
        ),
        subjects=[
            k8s_client.RbacV1Subject(
                kind="ServiceAccount", name="python-job-sa", namespace=namespace
            )
        ],
        role_ref=k8s_client.V1RoleRef(
            kind="Role", name="python-job-role", api_group="rbac.authorization.k8s.io"
        ),
    )


def get_deployment_spec(
    runner_config: RunnerConfig, logs_folder: Path
) -> k8s_client.V1Deployment:
    """Get deployment spec for runner.

    :param namespace (str): Deployment namespace.
    :param logs_folder (Path): Logs folder.
    :return (k8s_client.V1Deployment): Deployment specification.
    """
    return k8s_client.V1DeploymentSpec(
        replicas=1,
        selector=k8s_client.V1LabelSelector(
            match_labels={"app": RUNNER_DEPLOYMENT_NAME}
        ),
        template=k8s_client.V1PodTemplateSpec(
            metadata=k8s_client.V1ObjectMeta(
                name=RUNNER_DEPLOYMENT_NAME,
                namespace=runner_config.kubectl_namespace,
                labels={"app": RUNNER_DEPLOYMENT_NAME},
            ),
            spec=k8s_client.V1PodSpec(
                runtime_class_name="nvidia",
                service_account_name="python-job-sa",
                image_pull_secrets=[
                    k8s_client.V1LocalObjectReference(name="datature-regcred")
                ],
                containers=[
                    k8s_client.V1Container(
                        name=RUNNER_DEPLOYMENT_NAME,
                        image=os.getenv(
                            "DATATURE_RUNNER_DOCKER_REGISTRY",
                            runner_config.runner_metadata.runner_registry,
                        )
                        + f"/{runner_config.runner_metadata.runner_name}"
                        + f":{runner_config.runner_metadata.runner_version}",
                        image_pull_policy="Always",
                        env=[
                            k8s_client.V1EnvVar(
                                name="WORKSPACE_ID",
                                value_from=k8s_client.V1EnvVarSource(
                                    config_map_key_ref=k8s_client.V1ConfigMapKeySelector(
                                        name=RUNNER_DEPLOYMENT_CONFIG_NAME,
                                        key="workspace_id",
                                    )
                                ),
                            ),
                            k8s_client.V1EnvVar(
                                name="SECRET_KEY",
                                value_from=k8s_client.V1EnvVarSource(
                                    config_map_key_ref=k8s_client.V1ConfigMapKeySelector(
                                        name=RUNNER_DEPLOYMENT_CONFIG_NAME,
                                        key="secret_key",
                                    ),
                                ),
                            ),
                            k8s_client.V1EnvVar(
                                name="RUNNER_ID",
                                value_from=k8s_client.V1EnvVarSource(
                                    config_map_key_ref=k8s_client.V1ConfigMapKeySelector(
                                        name=RUNNER_DEPLOYMENT_CONFIG_NAME,
                                        key="runner_id",
                                    ),
                                ),
                            ),
                            k8s_client.V1EnvVar(
                                name="LOGS_DIRECTORY",
                                value_from=k8s_client.V1EnvVarSource(
                                    config_map_key_ref=k8s_client.V1ConfigMapKeySelector(
                                        name=RUNNER_DEPLOYMENT_CONFIG_NAME,
                                        key="logs_directory",
                                    )
                                ),
                            ),
                            k8s_client.V1EnvVar(
                                name="DOCKER_REGISTRY",
                                value_from=k8s_client.V1EnvVarSource(
                                    config_map_key_ref=k8s_client.V1ConfigMapKeySelector(
                                        name=RUNNER_DEPLOYMENT_CONFIG_NAME,
                                        key="docker_registry",
                                    )
                                ),
                            ),
                            k8s_client.V1EnvVar(
                                name="API_URL",
                                value_from=k8s_client.V1EnvVarSource(
                                    config_map_key_ref=k8s_client.V1ConfigMapKeySelector(
                                        name=RUNNER_DEPLOYMENT_CONFIG_NAME,
                                        key="api_url",
                                    )
                                ),
                            ),
                        ],
                        volume_mounts=[
                            k8s_client.V1VolumeMount(
                                name="logs",
                                mount_path="/logs",
                            )
                        ],
                    )
                ],
                volumes=[
                    k8s_client.V1Volume(
                        name="logs",
                        host_path=k8s_client.V1HostPathVolumeSource(
                            path=str(logs_folder)
                        ),
                    )
                ],
            ),
        ),
    )
