#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   utils.py
@Author  :   Wei Loon Cheng, Kai Xuan Lee
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Custom runner utility functions.
"""

# pylint: disable=W0719,E1102

import base64
import hashlib
import json
import os
import queue
import shlex
import shutil
import subprocess
import sys
import threading
import time
from functools import wraps
from pathlib import Path
from typing import List
from uuid import UUID

import requests
from alive_progress import alive_bar
from colorama import Fore
from halo import Halo
from wcwidth import wcswidth

from datature.nexus.cli.runner import commands as COMMANDS
from datature.nexus.cli.runner import consts as CONSTS
from datature.nexus.cli.runner import k8s_config as K8S_CONFIG
from datature.nexus.cli.runner import messages as MESSAGES
from datature.nexus.cli.runner.common import install_pip_package
from datature.nexus.cli.runner.config import (
    GPUInfo,
    RunnerConfig,
    RunnerMetadata,
    SystemSpecs,
)
from datature.nexus.config import REQUEST_TIME_OUT_SECONDS
from datature.nexus.error import Error

try:
    import kubernetes as k8s
except ImportError as exc:
    if not install_pip_package("kubernetes"):
        raise Error(
            MESSAGES.INSTALL_PIP_PACKAGE_ERROR_MESSAGE.format(package_name="kubernetes")
        ) from exc
    import kubernetes as k8s

try:
    import pynvml
except ImportError as exc:
    if not install_pip_package("nvidia-ml-py"):
        raise Error(
            MESSAGES.INSTALL_PIP_PACKAGE_ERROR_MESSAGE.format(
                package_name="nvidia-ml-py"
            )
        ) from exc
    import pynvml


def start_spinner(func: callable = None) -> callable:
    """Start spinner for the function."""

    def decorator(func: callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            wait_spinner = Halo(spinner="dots")
            message_queue = queue.Queue()
            stop_thread = threading.Event()

            def update_spinner():
                while not stop_thread.is_set():
                    try:
                        new_message = message_queue.get(timeout=0.1)
                        if not kwargs.get("quiet", False) and new_message is not None:
                            wait_spinner.text = new_message
                    except queue.Empty:
                        continue

            thread = threading.Thread(target=update_spinner)
            wait_spinner.start()
            thread.start()

            try:
                result = func(*args, **kwargs, message_queue=message_queue)
                if not kwargs.get("quiet", False):
                    wait_spinner.succeed(result)
                return result
            except Error as exc:
                error_symbol = f"{Fore.CYAN}●{Fore.RESET}"
                wait_spinner.stop_and_persist(error_symbol, exc.message)
                sys.exit(1)
            except Exception as exc:
                error_symbol = f"{Fore.CYAN}●{Fore.RESET}"
                wait_spinner.stop_and_persist(error_symbol, str(exc))
                raise Exception(exc) from exc
            finally:
                stop_thread.set()
                thread.join()
                wait_spinner.stop()

        return wrapper

    if func is None:
        return decorator
    return decorator(func)


@start_spinner
def check_system_specs(runner_config: RunnerConfig, message_queue: queue.Queue) -> None:
    """Check system specifications.

    :param runner_config (RunnerConfig): Runner configuration.
    :param message_queue (queue.Queue): Message queue.
    """
    try:
        num_cores = int(
            subprocess.check_output(["nproc", "--all"], stderr=subprocess.STDOUT)
            .strip()
            .decode()
        )
        ram_total = int(
            subprocess.check_output(["free", "-b"], stderr=subprocess.STDOUT)
            .split()[7]
            .decode()
        )
        if ram_total < CONSTS.MINIMUM_RAM_BYTES:
            raise Error(
                MESSAGES.INSUFFICIENT_RAM_ERROR_MESSAGE.format(
                    ram_total // 1e9, CONSTS.MINIMUM_RAM_BYTES
                )
            )
        free_space = shutil.disk_usage(Path("/")).free
        if free_space < CONSTS.MINIMUM_STORAGE_BYTES:
            raise Error(
                MESSAGES.INSUFFICIENT_STORAGE_ERROR_MESSAGE.format(
                    free_space // 1e6, CONSTS.MINIMUM_STORAGE_BYTES
                )
            )
        runner_config.system_specs = SystemSpecs(
            num_cores=num_cores, ram_total=ram_total, free_space=free_space
        )
    except subprocess.CalledProcessError as exc:
        raise Error(
            MESSAGES.CHECK_SYSTEM_SPECS_ERROR_MESSAGE.format(exc.stderr)
        ) from exc

    try:
        check_nvidia_drivers(runner_config, message_queue)
    except Error as exc:
        raise exc from exc

    return MESSAGES.CHECK_SYSTEM_SPECS_SUCCESS_MESSAGE


def check_nvidia_drivers(
    runner_config: RunnerConfig, message_queue: queue.Queue
) -> None:
    """Check NVIDIA drivers.

    :param runner_config (RunnerConfig): Runner configuration.
    :param message_queue (queue.Queue): Message queue.
    """
    try:
        message_queue.put(MESSAGES.CHECK_DRIVERS_MESSAGE)
        pynvml.nvmlInit()
        driver_version = pynvml.nvmlSystemGetDriverVersion()
        if isinstance(driver_version, bytes):
            driver_version = driver_version.decode("utf-8")
        driver_version_major = int(driver_version.split(".")[0])
        if driver_version_major < CONSTS.MIN_NVIDIA_DRIVER_VERSION:
            raise Error(
                MESSAGES.DRIVER_VERSION_TOO_OLD_ERROR_MESSAGE.format(
                    driver_version, CONSTS.MIN_NVIDIA_DRIVER_VERSION
                )
            )
        if driver_version_major > CONSTS.MAX_NVIDIA_DRIVER_VERSION:
            raise Error(
                MESSAGES.DRIVER_VERSION_TOO_NEW_ERROR_MESSAGE.format(
                    driver_version, CONSTS.MAX_NVIDIA_DRIVER_VERSION
                )
            )
        cuda_version = pynvml.nvmlSystemGetCudaDriverVersion()

        message_queue.put(MESSAGES.FETCH_GPU_INFO_MESSAGE)
        device_count = pynvml.nvmlDeviceGetCount()
        if device_count == 0:
            raise Error(MESSAGES.NO_GPU_FOUND_ERROR_MESSAGE)

        if len(runner_config.gpus) == 0:
            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                device_name = str(pynvml.nvmlDeviceGetName(handle))
                device_vram_bytes = int(pynvml.nvmlDeviceGetMemoryInfo(handle).total)
                device_compute_capability = pynvml.nvmlDeviceGetCudaComputeCapability(
                    handle
                )
                device_uuid = pynvml.nvmlDeviceGetUUID(handle)
                if isinstance(device_uuid, bytes):
                    device_uuid = device_uuid.decode("utf-8")
                num_cuda_cores = pynvml.nvmlDeviceGetNumGpuCores(handle)
                runner_config.gpus.append(
                    GPUInfo(
                        device_id=i,
                        device_name=device_name,
                        device_vram_bytes=device_vram_bytes,
                        device_compute_capability=int(
                            "".join(map(str, device_compute_capability))
                        ),
                        device_driver_version=driver_version,
                        device_cuda_version=cuda_version,
                        device_uuid=device_uuid.replace("GPU-", ""),
                        device_cuda_cores=num_cuda_cores,
                    )
                )
        pynvml.nvmlShutdown()
    except subprocess.CalledProcessError as exc:
        raise Error(f"Error running nvidia-settings: {exc.stderr}") from exc
    except pynvml.NVMLError as exc:
        raise Error(MESSAGES.NVML_ERROR_MESSAGE.format(str(exc))) from exc
    except Error as exc:
        raise exc from exc


@start_spinner
def configure_microk8s(message_queue: queue.Queue) -> None:
    """Configure MicroK8s.

    :param message_queue (queue.Queue): Message queue.
    """
    try:
        message_queue.put(MESSAGES.CHECK_MICROK8S_STATUS_MESSAGE)
        subprocess.check_output(
            shlex.split(COMMANDS.MICROK8S_STATUS_COMMAND), stderr=subprocess.STDOUT
        )
    except FileNotFoundError as exc:
        raise Error(MESSAGES.MICROK8S_NOT_FOUND_ERROR_MESSAGE) from exc
    except subprocess.CalledProcessError as exc:
        raise Error(MESSAGES.CHECK_MICROK8S_STATUS_ERROR_MESSAGE) from exc
    return MESSAGES.CHECK_MICROK8S_STATUS_SUCCESS_MESSAGE


def ping_server(runner_config: RunnerConfig) -> None:
    """Ping Datature server.

    :param runner_config (RunnerConfig): Runner configuration
    """
    runner_config.status.valid_secret_key = False
    try:
        # Dummy ping to Datature server to check for internet connection.
        response = requests.get(
            f"{CONSTS.NEXUS_ENDPOINT}/workspaces/ws_{runner_config.workspace_id}/runners",
            headers={
                "Secret-Key": runner_config.secret_key,
                "Content-Type": "application/json",
            },
            timeout=REQUEST_TIME_OUT_SECONDS,
        )
        response.raise_for_status()
    except requests.exceptions.ConnectionError as exc:
        raise Error(MESSAGES.PING_SERVER_CONNECTION_ERROR_MESSAGE) from exc
    except requests.exceptions.HTTPError as exc:
        if response.status_code == 402:
            print(MESSAGES.FEATURE_NOT_AVAILABLE_ERROR_MESSAGE)
            sys.exit(1)
        if response.status_code == 403:
            raise Error(
                MESSAGES.PING_SERVER_FORBIDDEN_ERROR_MESSAGE.format(
                    runner_config.workspace_id
                )
            ) from exc
        if response.status_code != 405:
            raise Error(
                MESSAGES.PING_SERVER_UNKNOWN_ERROR_MESSAGE.format(response.text)
            ) from exc
    runner_config.status.valid_secret_key = True


def create_runner_id(runner_config: RunnerConfig) -> str:
    """Create runner UUID based on machine UUID and GPU UUIDs.

    :param runner_config (RunnerConfig): Runner configuration.
    :return (str): Runner UUID.
    """
    with open("/etc/machine-id", "r", encoding="utf-8") as machine_id_file:
        machine_id = str(machine_id_file.read().strip())
    runner_id_string = machine_id + runner_config.workspace_id
    for gpu in runner_config.gpus:
        runner_id_string += gpu.device_uuid

    sha256_hash = hashlib.sha256(runner_id_string.encode()).hexdigest()
    hex_uuid = (
        sha256_hash[:8]
        + "-"
        + sha256_hash[8:12]
        + "-"
        + "4"
        + sha256_hash[13:16]
        + "-"
        + sha256_hash[16:20]
        + "-"
        + sha256_hash[20:32]
    )
    return f"runner_{str(UUID(hex_uuid))}"


@start_spinner
def register_runner(runner_config: RunnerConfig, message_queue: queue.Queue) -> None:
    """Register runner with Datature server.

    :param runner_config (RunnerConfig): Runner configuration.
    :param message_queue (queue.Queue): Message queue.
    """
    message_queue.put(MESSAGES.REGISTER_RUNNER_MESSAGE.format(runner_config.name))
    try:
        response = requests.post(
            f"{CONSTS.NEXUS_ENDPOINT}/workspaces/ws_{runner_config.workspace_id}/runners",
            headers={
                "Secret-Key": runner_config.secret_key,
                "Content-Type": "application/json",
            },
            data=json.dumps(K8S_CONFIG.get_resource_config(runner_config)),
            timeout=REQUEST_TIME_OUT_SECONDS,
        )
        response.raise_for_status()
    except requests.exceptions.ConnectionError as exc:
        raise Error(
            MESSAGES.REGISTER_RUNNER_CONNECTION_ERROR_MESSAGE.format(runner_config.name)
        ) from exc
    except requests.exceptions.HTTPError as exc:
        if "No access rights" in response.text:
            raise Error(
                MESSAGES.REGISTER_RUNNER_FORBIDDEN_ERROR_MESSAGE.format(
                    runner_config.name, runner_config.workspace_id
                )
            ) from exc
        if "Conflict" in response.text:
            raise Error(
                MESSAGES.REGISTER_RUNNER_CONFLICT_ERROR_MESSAGE.format(
                    runner_config.name
                )
            ) from exc
        raise Error(
            MESSAGES.REGISTER_RUNNER_UNKNOWN_ERROR_MESSAGE.format(
                response.text, runner_config.name
            )
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise Error(
            MESSAGES.REGISTER_RUNNER_UNKNOWN_ERROR_MESSAGE.format(
                response.text, runner_config.name
            )
        ) from exc

    runner_config.kubectl_namespace = "datature-" + runner_config.id.replace(
        "runner_", "runner-"
    )

    return MESSAGES.REGISTER_RUNNER_SUCCESS_MESSAGE.format(
        runner_config.name, runner_config.id[-6:]
    )


@start_spinner
def create_runner_namespace(
    runner_config: RunnerConfig,
    k8s_core_api_instance: k8s.client.CoreV1Api,
    message_queue: queue.Queue,
) -> None:
    """Create runner namespace in Kubernetes.

    :param runner_config (RunnerConfig): Runner configuration.
    :param k8s_core_api_instance (k8s.client.CoreV1Api): Kubernetes Core API instance.
    :param message_queue (queue.Queue): Message queue.
    """
    message_queue.put(
        MESSAGES.CREATE_RUNNER_NAMESPACE_MESSAGE.format(runner_config.kubectl_namespace)
    )

    try:
        runner_namespace = k8s.client.V1Namespace(
            api_version="v1",
            kind="Namespace",
            metadata={"name": runner_config.kubectl_namespace},
        )
        k8s_core_api_instance.create_namespace(body=runner_namespace)
    except k8s.client.rest.ApiException as exc:
        if (
            exc.status != 409
            and json.loads(exc.body).get("reason", "") != "AlreadyExists"
        ):
            raise Error(
                MESSAGES.CREATE_RUNNER_NAMESPACE_ERROR_MESSAGE.format(
                    exc.body, runner_config.kubectl_namespace
                )
            ) from exc
    return MESSAGES.CREATE_RUNNER_NAMESPACE_SUCCESS_MESSAGE.format(
        runner_config.kubectl_namespace
    )


def get_runner_metadata(runner_config: RunnerConfig) -> None:
    """Get runner metadata.

    :param runner_config (RunnerConfig): Runner configuration.
    """
    try:
        response = requests.get(
            f"{CONSTS.NEXUS_ENDPOINT}/workspaces/ws_{runner_config.workspace_id}/metadata/runner",
            headers={
                "Secret-Key": runner_config.secret_key,
                "Content-Type": "application/json",
            },
            timeout=REQUEST_TIME_OUT_SECONDS,
        )
        runner_config.runner_metadata = RunnerMetadata.from_dict(response.json())
    except requests.exceptions.ConnectionError as exc:
        raise Error(MESSAGES.PING_SERVER_CONNECTION_ERROR_MESSAGE) from exc
    except requests.exceptions.HTTPError as exc:
        if response.status_code == 402:
            print(MESSAGES.FEATURE_NOT_AVAILABLE_ERROR_MESSAGE)
            sys.exit(1)
        if response.status_code == 403:
            raise Error(
                MESSAGES.PING_SERVER_FORBIDDEN_ERROR_MESSAGE.format(
                    runner_config.workspace_id
                )
            ) from exc
        if response.status_code != 405:
            raise Error(
                MESSAGES.PING_SERVER_UNKNOWN_ERROR_MESSAGE.format(response.text)
            ) from exc


@start_spinner
def apply_config_map(
    runner_config: RunnerConfig,
    k8s_core_api_instance: k8s.client.CoreV1Api,
    message_queue: queue.Queue,
) -> None:
    """Apply configuration map for runner in Kubernetes.

    :param runner_config (RunnerConfig): Runner configuration.
    :param k8s_core_api_instance (k8s.client.CoreV1Api): Kubernetes Core API instance.
    :param message_queue (queue.Queue): Message queue.
    """
    message_queue.put(MESSAGES.APPLY_CONFIG_MAP_MESSAGE)

    is_existing_config_map = False
    try:
        k8s_core_api_instance.read_namespaced_config_map(
            name=CONSTS.RUNNER_DEPLOYMENT_CONFIG_NAME,
            namespace=runner_config.kubectl_namespace,
        )
        is_existing_config_map = True
    except k8s.client.rest.ApiException as exc:
        if exc.status != 404 and json.loads(exc.body).get("reason", "") != "NotFound":
            pass

    try:
        config_map = k8s.client.V1ConfigMap(
            api_version="v1",
            kind="ConfigMap",
            metadata={
                "name": CONSTS.RUNNER_DEPLOYMENT_CONFIG_NAME,
                "namespace": runner_config.kubectl_namespace,
            },
            data={
                "secret_key": runner_config.secret_key,
                "workspace_id": runner_config.workspace_id,
                "runner_id": runner_config.id,
                "runner_name": runner_config.name,
                "logs_directory": str(CONSTS.RUNNER_LOG_DIR),
                "docker_registry": os.getenv(
                    "DATATURE_RUNNER_DOCKER_REGISTRY",
                    runner_config.runner_metadata.runner_registry,
                ),
                "api_url": os.getenv(
                    "DATATURE_API_BASE_URL", "https://api.datature.io"
                ),
            },
        )

        if is_existing_config_map:
            k8s_core_api_instance.patch_namespaced_config_map(
                name=CONSTS.RUNNER_DEPLOYMENT_CONFIG_NAME,
                namespace=runner_config.kubectl_namespace,
                body=config_map,
            )
        else:
            k8s_core_api_instance.create_namespaced_config_map(
                namespace=runner_config.kubectl_namespace, body=config_map
            )
    except k8s.client.rest.ApiException as exc:
        if (
            exc.status != 409
            and json.loads(exc.body).get("reason", "") != "AlreadyExists"
        ):
            raise Error(
                MESSAGES.APPLY_CONFIG_MAP_ERROR_MESSAGE.format(
                    exc.body, runner_config.kubectl_namespace
                )
            ) from exc
    return MESSAGES.APPLY_CONFIG_MAP_SUCCESS_MESSAGE


@start_spinner
def apply_service_account(
    runner_config: RunnerConfig,
    k8s_core_api_instance: k8s.client.CoreV1Api,
    k8s_rbac_api_instance: k8s.client.RbacAuthorizationV1Api,
    message_queue: queue.Queue,
) -> None:
    """Apply service account for runner in Kubernetes.

    :param runner_config (RunnerConfig): Runner configuration.
    :param k8s_core_api_instance (k8s.client.CoreV1Api): Kubernetes Core API instance.
    :param k8s_rbac_api_instance (k8s.client.RbacAuthorizationV1Api): Kubernetes RBAC API instance.
    :param message_queue (queue.Queue): Message queue.
    """
    message_queue.put(MESSAGES.APPLY_SERVICE_ACCOUNT_MESSAGE)

    try:
        service_account = k8s.client.V1ServiceAccount(
            api_version="v1",
            kind="ServiceAccount",
            metadata={
                "name": "python-job-sa",
                "namespace": runner_config.kubectl_namespace,
            },
        )

        k8s_core_api_instance.create_namespaced_service_account(
            namespace=runner_config.kubectl_namespace, body=service_account
        )
        k8s_rbac_api_instance.create_namespaced_role(
            namespace=runner_config.kubectl_namespace,
            body=K8S_CONFIG.get_role(runner_config.kubectl_namespace),
        )
        k8s_rbac_api_instance.create_namespaced_role_binding(
            namespace=runner_config.kubectl_namespace,
            body=K8S_CONFIG.get_role_binding(runner_config.kubectl_namespace),
        )
    except k8s.client.rest.ApiException as exc:
        if (
            exc.status != 409
            and json.loads(exc.body).get("reason", "") != "AlreadyExists"
        ):
            raise Error(
                MESSAGES.APPLY_SERVICE_ACCOUNT_ERROR_MESSAGE.format(
                    exc.body, runner_config.kubectl_namespace
                )
            ) from exc
    return MESSAGES.APPLY_SERVICE_ACCOUNT_SUCCESS_MESSAGE


@start_spinner
def setup_docker_registry_credentials(
    runner_config: RunnerConfig,
    k8s_core_api_instance: k8s.client.CoreV1Api,
    message_queue: queue.Queue,
) -> None:
    """Setup Docker registry credentials for runner in Kubernetes.

    :param runner_config (RunnerConfig): Runner configuration.
    :param k8s_core_api_instance (k8s.client.CoreV1Api): Kubernetes Core API instance.
    :param message_queue (queue.Queue): Message queue.
    """
    message_queue.put(
        MESSAGES.DELETE_DOCKER_REGCRED_MESSAGE.format(CONSTS.DOCKER_REGISTRY_SECRET)
    )
    try:
        # Delete existing secret datature-regcred if it exists
        body = k8s.client.V1DeleteOptions()
        k8s_core_api_instance.delete_namespaced_secret(
            name=CONSTS.DOCKER_REGISTRY_SECRET,
            namespace=runner_config.kubectl_namespace,
            body=body,
            grace_period_seconds=0,
        )
    except k8s.client.rest.ApiException as exc:
        if exc.status != 404 and json.loads(exc.body).get("reason", "") != "NotFound":
            raise Error(
                MESSAGES.DELETE_DOCKER_REGCRED_ERROR_MESSAGE.format(
                    CONSTS.DOCKER_REGISTRY_SECRET
                )
            ) from exc

    # Create new docker-registry secret datature-regcred
    message_queue.put(
        MESSAGES.CREATE_DOCKER_REGCRED_MESSAGE.format(CONSTS.DOCKER_REGISTRY_SECRET)
    )

    try:
        docker_config_dict = {
            "auths": {
                os.getenv(
                    "DATATURE_RUNNER_DOCKER_REGISTRY",
                    runner_config.runner_metadata.runner_registry,
                ): {
                    "username": "secret-key",
                    "password": runner_config.secret_key,
                }
            }
        }
        docker_config = base64.b64encode(
            json.dumps(docker_config_dict).encode()
        ).decode()
        body = k8s.client.V1Secret(
            api_version="v1",
            kind="Secret",
            type="kubernetes.io/dockerconfigjson",
            data={".dockerconfigjson": docker_config},
            metadata={
                "name": CONSTS.DOCKER_REGISTRY_SECRET,
                "namespace": runner_config.kubectl_namespace,
            },
        )
        k8s_core_api_instance.create_namespaced_secret(
            namespace=runner_config.kubectl_namespace, body=body
        )
    except k8s.client.rest.ApiException as exc:
        raise Error(
            MESSAGES.CREATE_DOCKER_REGCRED_ERROR_MESSAGE.format(
                CONSTS.DOCKER_REGISTRY_SECRET
            )
        ) from exc
    return MESSAGES.SETUP_DOCKER_REGCRED_SUCCESS_MESSAGE


@start_spinner
def apply_deployment(
    runner_config: RunnerConfig,
    k8s_apps_api_instance: k8s.client.AppsV1Api,
    message_queue: queue.Queue,
) -> None:
    """Apply deployment for runner in Kubernetes.

    :param runner_config (RunnerConfig): Runner configuration.
    :param k8s_apps_api_instance (k8s.client.AppsV1Api): Kubernetes Apps API instance.
    :param message_queue (queue.Queue): Message queue.
    """
    message_queue.put(
        MESSAGES.APPLY_DEPLOYMENT_MESSAGE.format(
            runner_config.name, runner_config.id[-6:]
        )
    )
    logs_folder = CONSTS.RUNNER_LOG_DIR / runner_config.id

    try:
        deployment = k8s.client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata={
                "name": CONSTS.RUNNER_DEPLOYMENT_NAME,
                "namespace": runner_config.kubectl_namespace,
                "labels": {"app": CONSTS.RUNNER_DEPLOYMENT_NAME},
            },
            spec=K8S_CONFIG.get_deployment_spec(runner_config, logs_folder),
        )
        k8s_apps_api_instance.create_namespaced_deployment(
            namespace=runner_config.kubectl_namespace, body=deployment
        )
    except k8s.client.rest.ApiException as exc:
        if (
            exc.status != 409
            and json.loads(exc.body).get("reason", "") != "AlreadyExists"
        ):
            raise Error(
                MESSAGES.APPLY_DEPLOYMENT_ERROR_MESSAGE.format(
                    exc.body,
                    CONSTS.RUNNER_DEPLOYMENT_NAME,
                    runner_config.kubectl_namespace,
                )
            ) from exc
    return MESSAGES.APPLY_DEPLOYMENT_SUCCESS_MESSAGE.format(
        CONSTS.RUNNER_DEPLOYMENT_NAME
    )


def initialize_runner(
    runner_config: RunnerConfig,
    k8s_apps_api_instance: k8s.client.AppsV1Api,
    k8s_custom_api_instance: k8s.client.CustomObjectsApi,
) -> None:
    """Initialize runner in Kubernetes.

    :param runner_config (RunnerConfig): Runner configuration.
    :param k8s_apps_api_instance (k8s.client.AppsV1Api): Kubernetes Apps API instance.
    :param k8s_custom_api_instance (k8s.client.CustomObjectsApi): Kubernetes Custom API instance.
    """
    try:
        patch = {
            "spec": {
                "validator": {
                    "driver": {
                        "env": [
                            {
                                "name": "DISABLE_DEV_CHAR_SYMLINK_CREATION",
                                "value": "true",
                            }
                        ]
                    }
                }
            }
        }
        k8s_custom_api_instance.patch_cluster_custom_object(
            group="nvidia.com",
            version="v1",
            plural="clusterpolicies",
            name="cluster-policy",
            body=patch,
        )
    except k8s.client.rest.ApiException as exc:
        if exc.status == 404:
            print(MESSAGES.PATCH_CLUSTER_POLICY_NOT_FOUND_ERROR_MESSAGE)
            raise Error(MESSAGES.PATCH_CLUSTER_POLICY_NOT_FOUND_ERROR_MESSAGE) from exc
        print(MESSAGES.PATCH_CLUSTER_POLICY_ERROR_MESSAGE.format(exc.body))
        raise Error(
            MESSAGES.PATCH_CLUSTER_POLICY_ERROR_MESSAGE.format(exc.body)
        ) from exc

    with alive_bar(
        CONSTS.RUNNER_INITIALIZATION_NUM_CHECKS,
        title=MESSAGES.INITIALIZE_RUNNER_MESSAGE,
        title_length=27,
        length=30,
        stats=True,
        elapsed=False,
    ) as progress_bar:
        for current_check in range(CONSTS.RUNNER_INITIALIZATION_NUM_CHECKS):
            response = k8s_apps_api_instance.read_namespaced_deployment(
                name=CONSTS.RUNNER_DEPLOYMENT_NAME,
                namespace=runner_config.kubectl_namespace,
            )
            if response.status.conditions is None:
                time.sleep(CONSTS.RUNNER_INITIALIZATION_SLEEP_SECONDS)
                progress_bar()
                continue

            runner_initialization_query = " ".join(
                [
                    f"{condition.status} {condition.type}"
                    for condition in response.status.conditions
                ]
            )

            if "True Available" in runner_initialization_query:
                progress_bar(CONSTS.RUNNER_INITIALIZATION_NUM_CHECKS - current_check)
                return

            time.sleep(CONSTS.RUNNER_INITIALIZATION_SLEEP_SECONDS)
            progress_bar()

    print(
        MESSAGES.INITIALIZE_RUNNER_ERROR_MESSAGE.format(
            runner_config.name, runner_config.id[-6:]
        )
    )
    raise Error(
        MESSAGES.INITIALIZE_RUNNER_ERROR_MESSAGE.format(
            runner_config.name, runner_config.id[-6:]
        )
    )


def truncate_text(text: str, max_length: int = 10) -> str:
    """Truncate text to a maximum length.

    :param text (str): Text to truncate.
    :param max_length (int): Maximum length, default is 10 characters.
    :return (str): Truncated text.
    """
    text_width = wcswidth(text)
    if text_width <= max_length:
        return text

    current_width = 0
    truncated_text = ""

    for char in text:
        char_width = wcswidth(char)
        if current_width + char_width > max_length - 3:
            break

        truncated_text += char
        current_width += char_width

    truncated_text += "..."
    space_padding = max_length - wcswidth(truncated_text)
    truncated_text += " " * space_padding
    return truncated_text


def format_runner_status(runner_config: RunnerConfig) -> None:
    """Format runner status and print to stdout.

    :param runner_config (RunnerConfig): Runner configuration.
    """
    name_padding = max(0, 26 - (wcswidth(runner_config.name) - len(runner_config.name)))
    full_status = runner_config.status.status + (
        " [SUSPENDED]" if runner_config.status.suspended else ""
    )
    ram_gib = str(int(runner_config.system_specs.ram_total / 1e9))
    cuda_major = runner_config.gpus[-1].device_cuda_version // 1e3
    cuda_minor = (runner_config.gpus[-1].device_cuda_version % 1e3) // 10
    cuda_version = f"{cuda_major}.{cuda_minor}"

    print(f"+{'-' * 73}+")
    print(f"| {'RUNNER NAME':<26} {'HASH':<10} {'STATUS':<22} {'SECRET KEY':<10} |")
    print(
        f"| {truncate_text(runner_config.name, 26):<{name_padding}} "
        f"{runner_config.id[-6:]:<10} {full_status:<22} "
        f"{'Valid' if runner_config.status.valid_secret_key else 'Invalid':<10} |"
    )
    print(f"|{'=' * 73}|")
    print(f"| {'Cores':<10} {'RAM':<15} {'GPUs':<10} {'CUDA':<10} {'Driver':<22} |")
    print(
        f"| {runner_config.system_specs.num_cores:<10} {ram_gib:<5} {'GiB':<9} "
        f"{len(runner_config.gpus):<10} {cuda_version:<10} "
        f"{runner_config.gpus[-1].device_driver_version:<22} |"
    )
    print(f"|{'-' * 73}|")
    print(f"| {'GPU':<10} {'Name':<26} {'VRAM':<10} {'CC':<22} |")
    for gpu in runner_config.gpus:
        gpu_device_name_padding = max(
            0, 26 - (wcswidth(gpu.device_name) - len(gpu.device_name))
        )
        vram_gib = str(int(gpu.device_vram_bytes / 1e9))
        print(
            f"| {gpu.device_id:<10} "
            f"{truncate_text(gpu.device_name, 26):<{gpu_device_name_padding}} "
            f"{vram_gib:<4} {'GiB':<5} {gpu.device_compute_capability:<22} |"
        )
    print(f"+{'-' * 73}+")

    if len(runner_config.status.runs) > 0:
        print(f"+{'-' * 80}+")
        print(
            f"| {'RUN HASH':<9} {'IMAGE':<15} {'STATUS':<12} "
            f"{'STARTED AT':<20} {'RAM':<10} {'GPUs':<7} |"
        )
        for run in runner_config.status.runs:
            run_hash = run.id[-6:]
            run_allocated_memory_gib = str(int(run.allocated_memory / 1e9))
            run_image_name_padding = max(
                0, 15 - (wcswidth(run.image_name) - len(run.image_name))
            )

            print(
                f"| {run_hash:<9} {truncate_text(run.image_name, 15):<{run_image_name_padding}} "
                f"{run.status:<12} {run.started:<20} "
                f"{run_allocated_memory_gib:<4} {'GiB':<5} {run.num_gpus:<7} |"
            )
            print(f"+{'-' * 80}+")


def format_runner_list(runner_configs: List[RunnerConfig]) -> None:
    """Format runner list and print to stdout.

    :param runner_configs (List[RunnerConfig]): List of runner configurations.
    """
    print(f"{'RUNNER NAME':<26} {'HASH':<10} {'STATUS':<22} {'SECRET KEY':<10}")

    for runner_config in runner_configs:
        name_padding = max(
            0, 26 - (wcswidth(runner_config.name) - len(runner_config.name))
        )
        full_status = runner_config.status.status + (
            " [SUSPENDED]" if runner_config.status.suspended else ""
        )
        runner_hash = runner_config.id[-6:]
        print(
            f"{truncate_text(runner_config.name, 26):<{name_padding}} "
            f"{runner_hash:<10} {full_status:<22} "
            f"{'Valid' if runner_config.status.valid_secret_key else 'Invalid':<10}"
        )
