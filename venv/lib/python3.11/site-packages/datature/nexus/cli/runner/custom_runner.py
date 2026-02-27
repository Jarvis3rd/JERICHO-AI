#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   custom_runner.py
@Author  :   Wei Loon Cheng, Kai Xuan Lee
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Custom runner module.
"""

# pylint: disable=W0718,E1120

import json
import queue
import shlex
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List

import requests

from datature.nexus.cli.runner import commands as COMMANDS
from datature.nexus.cli.runner import common
from datature.nexus.cli.runner import consts as CONSTS
from datature.nexus.cli.runner import messages as MESSAGES
from datature.nexus.cli.runner import utils
from datature.nexus.cli.runner.config import RunnerConfig, RunStatus
from datature.nexus.config import REQUEST_TIME_OUT_SECONDS
from datature.nexus.error import Error

try:
    import kubernetes as k8s
except ImportError as exc:
    if not common.install_pip_package("kubernetes"):
        raise Error(
            MESSAGES.INSTALL_PIP_PACKAGE_ERROR_MESSAGE.format(package_name="kubernetes")
        ) from exc
    import kubernetes as k8s


class CustomRunner:
    """Custom Runner class."""

    def __init__(self, **kwargs):
        CONSTS.RUNNER_INIT_ROOT_DIR.mkdir(parents=True, exist_ok=True)
        self._runner_config = RunnerConfig.read_from_file(
            kwargs.get("runner_name_or_hash", None)
        )

        if not self._runner_config.id:
            self._runner_config.id = utils.create_runner_id(self._runner_config)
            self._runner_config.write_to_file()

        k8s_config_data = subprocess.check_output(
            shlex.split(COMMANDS.MICROK8S_CONFIG_COMMAND), stderr=subprocess.STDOUT
        )
        CONSTS.K8S_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONSTS.K8S_CONFIG_FILE_PATH.write_bytes(k8s_config_data)

        k8s_config = k8s.client.Configuration()
        k8s.config.load_kube_config(
            config_file=str(CONSTS.K8S_CONFIG_FILE_PATH),
            client_configuration=k8s_config,
        )
        with k8s.client.ApiClient(k8s_config) as api_client:
            self._k8s_core_api_instance = k8s.client.CoreV1Api(api_client)
            self._k8s_apps_api_instance = k8s.client.AppsV1Api(api_client)
            self._k8s_rbac_api_instance = k8s.client.RbacAuthorizationV1Api(api_client)
            self._k8s_batch_api_instance = k8s.client.BatchV1Api(api_client)
            self._k8s_custom_api_instance = k8s.client.CustomObjectsApi(api_client)

    def install(self):
        """Install custom runner."""
        try:
            utils.register_runner(self._runner_config)
            utils.create_runner_namespace(
                self._runner_config, self._k8s_core_api_instance
            )
            utils.get_runner_metadata(self._runner_config)
            utils.apply_config_map(self._runner_config, self._k8s_core_api_instance)
            utils.apply_service_account(
                self._runner_config,
                self._k8s_core_api_instance,
                self._k8s_rbac_api_instance,
            )
            utils.setup_docker_registry_credentials(
                self._runner_config, self._k8s_core_api_instance
            )
            utils.apply_deployment(self._runner_config, self._k8s_apps_api_instance)
            utils.initialize_runner(
                self._runner_config,
                self._k8s_apps_api_instance,
                self._k8s_custom_api_instance,
            )
            self._cleanup()
        except KeyboardInterrupt:
            print(MESSAGES.KEYBOARD_INTERRUPT_MESSAGE)
            print(MESSAGES.INSTALL_CLEANUP_MESSAGE)
            self._soft_uninstall()
            sys.exit(1)
        except Error:
            common.log_errors()
            self._soft_uninstall()
            sys.exit(1)
        except Exception:
            common.log_errors(unknown=True)
            self._soft_uninstall()
            sys.exit(1)

        print(
            MESSAGES.INSTALL_RUNNER_SUCCESS_MESSAGE.format(
                self._runner_config.workspace_id
            )
        )

    def _soft_uninstall(self):
        """Soft uninstall custom runner. Cleans up broken installations."""
        try:
            requests.delete(
                f"{CONSTS.NEXUS_ENDPOINT}/workspaces/ws_{self._runner_config.workspace_id}"
                f"/runners/{self._runner_config.id}",
                headers={
                    "Secret-Key": self._runner_config.secret_key,
                    "Content-Type": "application/json",
                },
                timeout=REQUEST_TIME_OUT_SECONDS,
            )
            self._k8s_core_api_instance.delete_collection_namespaced_secret(
                self._runner_config.kubectl_namespace
            )
            self._k8s_apps_api_instance.delete_collection_namespaced_deployment(
                self._runner_config.kubectl_namespace
            )
            self._k8s_rbac_api_instance.delete_collection_namespaced_role_binding(
                self._runner_config.kubectl_namespace
            )
            self._k8s_rbac_api_instance.delete_collection_namespaced_role(
                self._runner_config.kubectl_namespace
            )
            self._k8s_core_api_instance.delete_collection_namespaced_service_account(
                self._runner_config.kubectl_namespace
            )
            self._k8s_core_api_instance.delete_collection_namespaced_config_map(
                self._runner_config.kubectl_namespace
            )
            self._k8s_core_api_instance.delete_namespace(
                self._runner_config.kubectl_namespace
            )
        except k8s.client.rest.ApiException as exc:
            if exc.status != 404:
                raise Error(
                    MESSAGES.UNINSTALL_RUNNER_ERROR_MESSAGE.format(
                        exc.body, self._runner_config.name, self._runner_config.id[-6:]
                    )
                ) from exc
        finally:
            self._runner_config.remove_from_file()

    @utils.start_spinner
    def uninstall(self, **kwargs):
        """Uninstall custom runner."""
        message_queue = kwargs.get("message_queue", queue.Queue)
        message_queue.put(
            MESSAGES.UNINSTALL_RUNNER_MESSAGE.format(
                self._runner_config.name, self._runner_config.id[-6:]
            )
        )

        try:
            self._runner_config.update(force=True)
        except Error:
            print(MESSAGES.LOCAL_UNINSTALL_ACTION_MESSAGE)

        try:
            ongoing_runs = self.get_ongoing_runs
            if ongoing_runs:
                message_queue.put(
                    MESSAGES.DELETE_PODS_MESSAGE.format(
                        self._runner_config.kubectl_namespace
                    )
                )
                for run in ongoing_runs:
                    requests.patch(
                        f"{CONSTS.NEXUS_ENDPOINT}/projects/{run['project_id']}/runs/{run['run_id']}",
                        headers={
                            "Secret-Key": self._runner_config.secret_key,
                            "Content-Type": "application/json",
                        },
                        json={"status": "Cancelled"},
                        timeout=REQUEST_TIME_OUT_SECONDS,
                    )
                self._k8s_batch_api_instance.delete_collection_namespaced_job(
                    self._runner_config.kubectl_namespace
                )

            requests.delete(
                f"{CONSTS.NEXUS_ENDPOINT}/workspaces/ws_{self._runner_config.workspace_id}/runners/{self._runner_config.id}",
                headers={
                    "Secret-Key": self._runner_config.secret_key,
                    "Content-Type": "application/json",
                },
                timeout=REQUEST_TIME_OUT_SECONDS,
            )

            message_queue.put(
                MESSAGES.DELETE_SECRETS_MESSAGE.format(
                    self._runner_config.kubectl_namespace
                )
            )
            self._k8s_core_api_instance.delete_collection_namespaced_secret(
                self._runner_config.kubectl_namespace
            )

            message_queue.put(
                MESSAGES.DELETE_DEPLOYMENTS_MESSAGE.format(
                    self._runner_config.kubectl_namespace
                )
            )
            self._k8s_apps_api_instance.delete_collection_namespaced_deployment(
                self._runner_config.kubectl_namespace
            )

            message_queue.put(
                MESSAGES.DELETE_ROLE_BINDINGS_MESSAGE.format(
                    self._runner_config.kubectl_namespace
                )
            )
            self._k8s_rbac_api_instance.delete_collection_namespaced_role_binding(
                self._runner_config.kubectl_namespace
            )

            message_queue.put(
                MESSAGES.DELETE_ROLES_MESSAGE.format(
                    self._runner_config.kubectl_namespace
                )
            )
            self._k8s_rbac_api_instance.delete_collection_namespaced_role(
                self._runner_config.kubectl_namespace
            )

            message_queue.put(
                MESSAGES.DELETE_SERVICE_ACCOUNTS_MESSAGE.format(
                    self._runner_config.kubectl_namespace
                )
            )
            self._k8s_core_api_instance.delete_collection_namespaced_service_account(
                self._runner_config.kubectl_namespace
            )

            message_queue.put(
                MESSAGES.DELETE_CONFIG_MAPS_MESSAGE.format(
                    self._runner_config.kubectl_namespace
                )
            )
            self._k8s_core_api_instance.delete_collection_namespaced_config_map(
                self._runner_config.kubectl_namespace
            )

            message_queue.put(
                MESSAGES.DELETE_NAMESPACE_MESSAGE.format(
                    self._runner_config.kubectl_namespace
                )
            )
            self._k8s_core_api_instance.delete_namespace(
                self._runner_config.kubectl_namespace
            )

            # Wait for namespace to be fully deleted
            while True:
                try:
                    self._k8s_core_api_instance.read_namespace(
                        self._runner_config.kubectl_namespace
                    )
                    time.sleep(5)
                except k8s.client.rest.ApiException as exc:
                    if exc.status == 404:
                        break
        except k8s.client.rest.ApiException as exc:
            if exc.status != 404:
                raise Error(
                    MESSAGES.UNINSTALL_RUNNER_ERROR_MESSAGE.format(
                        exc.body, self._runner_config.name, self._runner_config.id[-6:]
                    )
                ) from exc
        finally:
            self._runner_config.remove_from_file()

        return MESSAGES.UNINSTALL_RUNNER_SUCCESS_MESSAGE.format(
            self._runner_config.name, self._runner_config.id[-6:]
        )

    @utils.start_spinner
    def suspend(self, **kwargs):
        """Suspend custom runner."""
        if self._runner_config.status.suspended:
            return f"Runner '{self._runner_config.name}' [{self._runner_config.id[-6:]}] has already been suspended."

        message_queue = kwargs.get("message_queue", queue.Queue())
        message_queue.put(
            MESSAGES.SUSPEND_RUNNER_MESSAGE.format(
                self._runner_config.name, self._runner_config.id[-6:]
            )
        )

        try:
            response = requests.patch(
                f"{CONSTS.NEXUS_ENDPOINT}/workspaces/ws_{self._runner_config.workspace_id}/runners/{self._runner_config.id}",
                json={"suspended": True},
                headers={
                    "Secret-Key": self._runner_config.secret_key,
                    "Content-Type": "application/json",
                },
                timeout=REQUEST_TIME_OUT_SECONDS,
            )
            response.raise_for_status()
        except requests.exceptions.ConnectionError:
            print(MESSAGES.LOCAL_SUSPEND_ACTION_MESSAGE)
        except requests.exceptions.HTTPError:
            print(MESSAGES.LOCAL_SUSPEND_ACTION_MESSAGE)

        try:
            self._k8s_apps_api_instance.patch_namespaced_deployment(
                CONSTS.RUNNER_DEPLOYMENT_NAME,
                self._runner_config.kubectl_namespace,
                body={"spec": {"replicas": 0}},
            )
        except k8s.client.rest.ApiException as exc:
            if (
                exc.status != 409
                and json.loads(exc.body).get("reason", "") != "AlreadyExists"
            ):
                raise Error(
                    MESSAGES.SUSPEND_RUNNER_UNKNOWN_ERROR_MESSAGE.format(
                        self._runner_config.name, self._runner_config.id[-6:]
                    )
                ) from exc

        self._runner_config.status.suspended = True
        self._runner_config.write_to_file()
        return MESSAGES.SUSPEND_RUNNER_SUCCESS_MESSAGE.format(
            self._runner_config.name, self._runner_config.id[-6:]
        )

    @utils.start_spinner
    def resume(self, **kwargs):
        """Resume custom runner."""
        if not self._runner_config.status.suspended:
            return f"Runner '{self._runner_config.name}' [{self._runner_config.id[-6:]}] is already active."

        message_queue = kwargs.get("message_queue", queue.Queue())
        message_queue.put(
            MESSAGES.RESUME_RUNNER_MESSAGE.format(
                self._runner_config.name, self._runner_config.id[-6:]
            )
        )

        try:
            utils.setup_docker_registry_credentials(
                self._runner_config, self._k8s_core_api_instance
            )
            response = requests.patch(
                f"{CONSTS.NEXUS_ENDPOINT}/workspaces/ws_{self._runner_config.workspace_id}/runners/{self._runner_config.id}",
                json={"suspended": False},
                headers={
                    "Secret-Key": self._runner_config.secret_key,
                    "Content-Type": "application/json",
                },
                timeout=REQUEST_TIME_OUT_SECONDS,
            )
            response.raise_for_status()
        except requests.exceptions.ConnectionError:
            print(MESSAGES.LOCAL_RESUME_ACTION_MESSAGE)
        except requests.exceptions.HTTPError:
            print(MESSAGES.LOCAL_RESUME_ACTION_MESSAGE)

        try:
            self._k8s_apps_api_instance.patch_namespaced_deployment(
                CONSTS.RUNNER_DEPLOYMENT_NAME,
                self._runner_config.kubectl_namespace,
                body={"spec": {"replicas": 1}},
            )
        except k8s.client.rest.ApiException as exc:
            if (
                exc.status != 409
                and json.loads(exc.body).get("reason", "") != "AlreadyExists"
            ):
                raise Error(
                    MESSAGES.RESUME_RUNNER_UNKNOWN_ERROR_MESSAGE.format(
                        self._runner_config.name, self._runner_config.id[-6:]
                    )
                ) from exc

        self._runner_config.status.suspended = False
        self._runner_config.write_to_file()
        return MESSAGES.RESUME_RUNNER_SUCCESS_MESSAGE.format(
            self._runner_config.name, self._runner_config.id[-6:]
        )

    @utils.start_spinner
    def restart(self, **kwargs):
        """Restart custom runner."""
        message_queue = kwargs.get("message_queue", queue.Queue())
        message_queue.put(
            MESSAGES.RESTART_RUNNER_MESSAGE.format(
                self._runner_config.name, self._runner_config.id[-6:]
            )
        )

        try:
            self._runner_config.update(force=True)
        except Error:
            print(MESSAGES.LOCAL_RESTART_ACTION_MESSAGE)

        self.suspend()
        self.resume()

        try:
            now = datetime.now().isoformat("T") + "Z"
            self._k8s_apps_api_instance.patch_namespaced_deployment(
                CONSTS.RUNNER_DEPLOYMENT_NAME,
                self._runner_config.kubectl_namespace,
                body={
                    "spec": {
                        "template": {
                            "metadata": {
                                "annotations": {
                                    "kubectl.kubernetes.io/restartedAt": now
                                }
                            }
                        }
                    }
                },
            )
        except k8s.client.rest.ApiException as exc:
            if (
                exc.status != 409
                and json.loads(exc.body).get("reason", "") != "AlreadyExists"
            ):
                raise Error(
                    MESSAGES.RESTART_RUNNER_ERROR_MESSAGE.format(
                        exc.body,
                        CONSTS.RUNNER_DEPLOYMENT_NAME,
                        self._runner_config.kubectl_namespace,
                    )
                ) from exc
        return MESSAGES.RESTART_RUNNER_SUCCESS_MESSAGE.format(
            CONSTS.RUNNER_DEPLOYMENT_NAME
        )

    @utils.start_spinner
    def reauth(self, **kwargs):
        """Reauthenticate custom runner."""
        message_queue = kwargs.get("message_queue", queue.Queue())
        new_secret_key = kwargs.get("new_secret_key", "")

        try:
            self._runner_config.secret_key = new_secret_key
            utils.ping_server(self._runner_config)

            # New secret key is valid, save to file
            self._runner_config.write_to_file()

            if self.get_ongoing_runs:
                message_queue.put(
                    MESSAGES.DELETE_PODS_MESSAGE.format(
                        self._runner_config.kubectl_namespace
                    )
                )
                for label_selector in CONSTS.DELETE_JOB_LABEL_SELECTORS:
                    self._k8s_batch_api_instance.delete_collection_namespaced_job(
                        self._runner_config.kubectl_namespace,
                        label_selector=label_selector,
                        propagation_policy="Foreground",
                    )
                while self.get_ongoing_runs:
                    # Wait for all runs to be deleted before continuing
                    time.sleep(5)

        except k8s.client.rest.ApiException as exc:
            raise Error(
                MESSAGES.REAUTH_RUNNER_ERROR_MESSAGE.format(
                    exc.body, self._runner_config.kubectl_namespace
                )
            ) from exc

        utils.apply_config_map(self._runner_config, self._k8s_core_api_instance)
        self.restart()
        return MESSAGES.REAUTH_RUNNER_SUCCESS_MESSAGE.format(
            self._runner_config.name, self._runner_config.id[-6:]
        )

    def dump_logs(self, **kwargs) -> None:
        """Dump custom runner logs."""
        logs_input_dir = CONSTS.RUNNER_LOG_DIR / self._runner_config.id
        logs_output_path = kwargs.get("file", None)
        if logs_output_path:
            logs_output_path = Path(logs_output_path)
            logs_output_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            logs_output_path = Path("/dev/stdout")

        run_hash = kwargs.get("run_hash", None)
        if run_hash:
            run_init_log_suffix = f"{run_hash}-init.log"
            run_log_suffix = f"{run_hash}.log"

            run_init_logs_path = next(
                logs_input_dir.glob(f"*{run_init_log_suffix}"), None
            )
            run_logs_path = next(logs_input_dir.glob(f"*{run_log_suffix}"), None)
            if not run_init_logs_path and not run_logs_path:
                print(MESSAGES.RUN_LOGS_NOT_FOUND_ERROR_MESSAGE.format(run_hash))
                return

            logs = ""
            if run_init_logs_path:
                logs += run_init_logs_path.read_text(encoding="utf-8")
            if run_logs_path:
                logs += run_logs_path.read_text(encoding="utf-8")
            logs_output_path.write_text(logs, encoding="utf-8")
        else:
            runner_logs_path = logs_input_dir / "runner.log"
            if not runner_logs_path.exists():
                print(
                    MESSAGES.RUNNER_LOGS_NOT_FOUND_ERROR_MESSAGE.format(
                        self._runner_config.name, self._runner_config.id[-6:]
                    )
                )
                return

            logs_output_path.write_text(
                runner_logs_path.read_text(encoding="utf-8"), encoding="utf-8"
            )
            if logs_output_path != Path("/dev/stdout"):
                print(
                    MESSAGES.DUMP_RUNNER_LOGS_SUCCESS_MESSAGE.format(
                        logs_output_path.resolve()
                    )
                )

    def display_status(self) -> None:
        """Display custom runner status."""
        try:
            self._runner_config.update()
        except Error as exc:
            if (
                "Workspace ID / Secret Key combination has been invalidated"
                in exc.message
            ):
                self._runner_config.status.valid_secret_key = False
            else:
                print(exc.message)
                sys.exit(1)

        try:
            config_map = self._k8s_core_api_instance.read_namespaced_config_map(
                CONSTS.RUNNER_DEPLOYMENT_CONFIG_NAME,
                self._runner_config.kubectl_namespace,
            ).data

            self._runner_config.name = config_map["runner_name"]
            self._runner_config.id = config_map["runner_id"]
            self._runner_config.secret_key = config_map["secret_key"]
            self._runner_config.workspace_id = config_map["workspace_id"]

            jobs = self._k8s_batch_api_instance.list_namespaced_job(
                self._runner_config.kubectl_namespace
            ).items

        except k8s.client.rest.ApiException as exc:
            raise Error(
                MESSAGES.RETRIEVE_RUNNER_STATUS_ERROR_MESSAGE.format(
                    exc.body, self._runner_config.kubectl_namespace
                )
            ) from exc

        runs_status = []
        if self._runner_config.status.valid_secret_key:
            for job in jobs:
                run_id = job.spec.template.metadata.labels["job-name"].replace(
                    "datature-run-", "run_"
                )
                try:
                    project_id = next(
                        filter(
                            lambda x: x.name == "PROJECT_ID",
                            job.spec.template.spec.containers[0].env,
                        )
                    ).value
                except TypeError:
                    continue

                try:
                    run_response = requests.get(
                        f"{CONSTS.NEXUS_ENDPOINT}/projects/{project_id}/runs/{run_id}",
                        headers={
                            "Secret-Key": self._runner_config.secret_key,
                            "Content-Type": "application/json",
                        },
                        timeout=REQUEST_TIME_OUT_SECONDS,
                    )
                    run_response.raise_for_status()
                except requests.exceptions.ConnectionError as exc:
                    raise Error(
                        MESSAGES.REGISTER_RUNNER_CONNECTION_ERROR_MESSAGE.format(
                            self._runner_config.name, self._runner_config.id[-6:]
                        )
                    ) from exc
                except requests.exceptions.HTTPError as exc:
                    if "ForbiddenError" in run_response.text:
                        raise Error(
                            MESSAGES.REGISTER_RUNNER_FORBIDDEN_ERROR_MESSAGE.format(
                                run_response.text,
                                self._runner_config.name,
                                self._runner_config.id[-6:],
                            )
                        ) from exc
                    if run_response.status_code != 405:
                        raise Error(
                            MESSAGES.REGISTER_RUNNER_UNKNOWN_ERROR_MESSAGE.format(
                                run_response.text,
                                self._runner_config.name,
                                self._runner_config.id[-6:],
                            )
                        ) from exc

                run_image = (
                    job.spec.template.spec.containers[0]
                    .image.split("/")[-1]
                    .split(":")[0]
                )
                run_status = run_response.json()["status"]["overview"]
                run_time_started = job.status.start_time.strftime("%Y-%m-%d %H:%M:%S")
                run_memory_allocated = int(
                    job.spec.template.spec.containers[0].resources.limits.get(
                        "memory", ""
                    )
                )
                run_num_gpus = job.spec.template.spec.containers[
                    0
                ].resources.limits.get("nvidia.com/gpu", "")

                runs_status.append(
                    RunStatus(
                        id=run_id,
                        image_name=run_image,
                        status=run_status,
                        started=run_time_started,
                        allocated_memory=run_memory_allocated,
                        num_gpus=run_num_gpus,
                    )
                )

        self._runner_config.status.runs = runs_status
        utils.format_runner_status(self._runner_config)

        if not self._runner_config.status.valid_secret_key:
            print(
                MESSAGES.RUNNER_INVALID_SECRET_KEY_MESSAGE.format(
                    self._runner_config.workspace_id
                )
            )

        self._runner_config.write_to_file()

    @utils.start_spinner
    def _cleanup(self, message_queue: queue.Queue):
        """Cleanup custom runner resources."""
        message_queue.put(MESSAGES.INSTALL_CLEANUP_MESSAGE)
        self._runner_config.write_to_file()
        return MESSAGES.INSTALL_CLEANUP_SUCCESS_MESSAGE

    @property
    def get_ongoing_runs(self) -> List[dict]:
        """Get ongoing runs in custom runner.

        Returns:
            List[str]: List of ongoing runs.
        """
        try:
            pods = self._k8s_core_api_instance.list_namespaced_pod(
                self._runner_config.kubectl_namespace,
                label_selector="app==datature-trainer",
            ).items
            if len(pods) == 0:
                return []

            return [
                {
                    "run_id": pod.metadata.labels["job-name"].replace(
                        "datature-run-", "run_"
                    ),
                    "project_id": next(
                        filter(
                            lambda x: x.name == "PROJECT_ID",
                            pod.spec.containers[0].env,
                        )
                    ).value,
                }
                for pod in pods
            ]
        except k8s.client.rest.ApiException as exc:
            raise Error(
                MESSAGES.RETRIEVE_RUNS_ERROR_MESSAGE.format(
                    exc.body, self._runner_config.kubectl_namespace
                )
            ) from exc

    @property
    def config(self) -> RunnerConfig:
        """Get custom runner config.

        Returns:
            RunnerConfig: Custom runner config.
        """
        return self._runner_config
