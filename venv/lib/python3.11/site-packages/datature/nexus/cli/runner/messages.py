#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   messages.py
@Author  :   Wei Loon Cheng, Kai Xuan Lee
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Custom runner messages.
"""

from datature.nexus.cli.runner.consts import (
    DOCS_ENV_SETUP_URL,
    DOCS_ERROR_HANDLING_URL,
    SUPPORT_EMAIL,
)

INSTALL_PIP_PACKAGE_ERROR_MESSAGE = (
    "Failed to install {package_name}.\n"
    "You may need to install manually by running `pip install {package_name}` in your environment.\n"
    "Also ensure that your pip version is up-to-date by running `pip install --upgrade pip`.\n"
    f"Refer to {DOCS_ENV_SETUP_URL} for further instructions."
)

INSTALL_RUNNER_SUCCESS_MESSAGE = (
    "Runner installed and initialized. Return to your Nexus workspace to start a training:\n"
    "https://nexus.datature.io/workspace/{}"
)

CHECK_SYSTEM_SPECS_ERROR_MESSAGE = (
    "{}\n"
    "Error checking system specs.\n"
    "Please ensure that you have sufficient CPU cores and RAM.\n"
    f"For more information, please visit our {DOCS_ENV_SETUP_URL}"
)
INSUFFICIENT_RAM_ERROR_MESSAGE = (
    "Error: Insufficient RAM detected. You only have {}GB of RAM.\n"
    "Datature Runner requires at least 8GB of RAM to operate.\n"
    f"For more information, please visit our {DOCS_ENV_SETUP_URL}"
)
INSUFFICIENT_STORAGE_ERROR_MESSAGE = (
    "Error: Insufficient storage detected. You only have {}MB of storage.\n"
    "Datature Runner requires at least 754MB of storage to operate.\n"
    f"For more information, please visit our {DOCS_ENV_SETUP_URL}"
)
CHECK_DRIVERS_MESSAGE = "Info: Verifying NVIDIA driver version..."
FETCH_GPU_INFO_MESSAGE = "Info: Retrieving NVIDIA GPU information..."
DRIVER_VERSION_TOO_OLD_ERROR_MESSAGE = (
    "Error: NVIDIA driver version is incompatible.\n"
    "Your NVIDIA driver version is {driver_version} "
    "but the minimum supported version is {driver_version_lower_bound}."
    f"\nPlease upgrade your NVIDIA drivers.\n"
    f"For additional details, visit {DOCS_ERROR_HANDLING_URL}"
)
DRIVER_VERSION_TOO_NEW_ERROR_MESSAGE = (
    "Error: NVIDIA driver version is incompatible.\n"
    "Your NVIDIA driver version is {driver_version} "
    "but the maximum supported version is {driver_version_upper_bound}."
    f"\nPlease downgrade your NVIDIA drivers.\n"
    f"For additional details, visit {DOCS_ERROR_HANDLING_URL}"
)
NO_GPU_FOUND_ERROR_MESSAGE = (
    "Error: No NVIDIA GPUs detected.\n"
    "Datature Runner requires NVIDIA GPUs for operation.\n"
    f"For information on compatible GPUs, please visit {DOCS_ERROR_HANDLING_URL}"
)
NVML_ERROR_MESSAGE = (
    "{}\n"
    "Error: Datature Runner requires pre-installed NVIDIA drivers.\n"
    "If the necessary NVIDIA drivers are already installed, you might lack sufficient permissions to access them.\n"
    "For guidance on installing and configuring your NVIDIA drivers, "
    f"please visit {DOCS_ERROR_HANDLING_URL}"
)
CHECK_SYSTEM_SPECS_SUCCESS_MESSAGE = "Success: System specs verified."

CHECK_MICROK8S_STATUS_MESSAGE = "Info: Verifying microk8s status..."
MICROK8S_NOT_FOUND_ERROR_MESSAGE = (
    "Error: microk8s not found.\n"
    "Ensure that microk8s is installed on your system and that you have sufficient permissions to run it.\n"
    "Follow the installation and configuration guide at https://microk8s.io/#install-microk8s.\n"
    f"For more information on installing microk8s, please visit {DOCS_ENV_SETUP_URL}"
)
CHECK_MICROK8S_STATUS_ERROR_MESSAGE = (
    "Error: Failed to verify microk8s status.\n"
    "Ensure that microk8s is installed on your system and that you have sufficient permissions to run it.\n"
    "Follow the installation and configuration guide at https://microk8s.io/#install-microk8s.\n"
    f"For more information on installing microk8s, please visit {DOCS_ENV_SETUP_URL}"
)
CHECK_MICROK8S_STATUS_SUCCESS_MESSAGE = "Success: microk8s is installed and running."

REGISTER_RUNNER_MESSAGE = "Info: Registering Runner '{}'..."
REGISTER_RUNNER_CONNECTION_ERROR_MESSAGE = (
    "Error: Failed to connect to Runner '{}'. Ensure you have an active internet connection.\n"
    f"For more information, visit: {DOCS_ERROR_HANDLING_URL} or contact support: {SUPPORT_EMAIL}"
)
REGISTER_RUNNER_FORBIDDEN_ERROR_MESSAGE = (
    "Error: Failed to register Runner '{}'. Workspace ID / Secret Key combination has been invalidated.\n"
    "Ensure you have the correct Workspace ID and Secret Key, "
    "or regenerate one for your workspace on Nexus: "
    "https://nexus.datature.io/workspace/{}/settings#key"
    f"For more information, visit: {DOCS_ERROR_HANDLING_URL} or contact support: {SUPPORT_EMAIL}"
)
REGISTER_RUNNER_CONFLICT_ERROR_MESSAGE = (
    "Error: Failed to register Runner '{}'. Runner with the same configuration already exists.\n"
    "Please ensure that there are no duplicate Runners in your workspace.\n"
    f"For more information, visit: {DOCS_ERROR_HANDLING_URL} or contact support: {SUPPORT_EMAIL}"
)
REGISTER_RUNNER_UNKNOWN_ERROR_MESSAGE = (
    "{}\n"
    "Error: Failed to register Runner '{}'.\n"
    f"For more details, visit: {DOCS_ERROR_HANDLING_URL} or contact support: {SUPPORT_EMAIL}"
)
REGISTER_RUNNER_SUCCESS_MESSAGE = "Success: Runner '{}' [{}] registered."

CREATE_RUNNER_NAMESPACE_MESSAGE = "Info: Creating Runner namespace '{}'..."
CREATE_RUNNER_NAMESPACE_ERROR_MESSAGE = (
    "{}\n"
    "Error: Failed to create Runner namespace '{}'.\n"
    f"For more information, visit: {DOCS_ERROR_HANDLING_URL} or contact support: {SUPPORT_EMAIL}"
)
CREATE_RUNNER_NAMESPACE_SUCCESS_MESSAGE = "Success: Runner namespace '{}' created."

APPLY_CONFIG_MAP_MESSAGE = "Info: Applying config map..."
APPLY_CONFIG_MAP_ERROR_MESSAGE = (
    "{}\n"
    "Error: Failed to apply config map.\n"
    f"For more information, visit: {DOCS_ERROR_HANDLING_URL} or contact support: {SUPPORT_EMAIL}"
)
APPLY_CONFIG_MAP_SUCCESS_MESSAGE = "Success: Config map applied."

APPLY_SERVICE_ACCOUNT_MESSAGE = "Info: Applying service account..."
APPLY_SERVICE_ACCOUNT_ERROR_MESSAGE = (
    "Error: Failed to apply service account.\n"
    f"For more information, visit: {DOCS_ERROR_HANDLING_URL} or contact support: {SUPPORT_EMAIL}"
)
APPLY_SERVICE_ACCOUNT_SUCCESS_MESSAGE = "Success: Service account applied."

DELETE_DOCKER_REGCRED_MESSAGE = "Info: Deleting existing Docker registry secret '{}'..."
DELETE_DOCKER_REGCRED_ERROR_MESSAGE = (
    "Error: Failed to delete existing Docker registry secret '{}'.\n"
    f"For more information, visit: {DOCS_ERROR_HANDLING_URL} or contact support: {SUPPORT_EMAIL}"
)
CREATE_DOCKER_REGCRED_MESSAGE = "Info: Creating new Docker registry secret '{}'..."
CREATE_DOCKER_REGCRED_ERROR_MESSAGE = (
    "Error: Failed to create Docker registry secret '{}'.\n"
    f"For more information, visit: {DOCS_ERROR_HANDLING_URL} or contact support: {SUPPORT_EMAIL}"
)
SETUP_DOCKER_REGCRED_SUCCESS_MESSAGE = "Success: Docker registry credentials set."

APPLY_DEPLOYMENT_MESSAGE = "Info: Applying deployment for Runner '{}' [{}]..."
APPLY_DEPLOYMENT_ERROR_MESSAGE = (
    "{}\n"
    "Error: Failed to apply deployment for Runner '{}' [{}].\n"
    f"For more information, visit: {DOCS_ERROR_HANDLING_URL} or contact support: {SUPPORT_EMAIL}"
)
APPLY_DEPLOYMENT_SUCCESS_MESSAGE = "Success: Deployment '{}' applied."

INITIALIZE_RUNNER_MESSAGE = "Initializing the Runner ..."
PATCH_CLUSTER_POLICY_NOT_FOUND_ERROR_MESSAGE = (
    "Error: NVIDIA cluster policy not found in microk8s. Please ensure to run `microk8s enable nvidia`.\n"
    f"For help with manually patching your cluster policy, visit {DOCS_ERROR_HANDLING_URL}"
)
PATCH_CLUSTER_POLICY_ERROR_MESSAGE = (
    "{}\n"
    "Error: Failed to patch cluster policy.\n"
    f"For help with manually patching your cluster policy, visit {DOCS_ERROR_HANDLING_URL}"
)
INITIALIZE_RUNNER_ERROR_MESSAGE = (
    "Error: Failed to initialize Runner '{}' [{}].\n"
    "This error may be related to a MicroK8s issue during GPU plugin installation.\n"
    f"For guidance on resolving this issue, visit {DOCS_ERROR_HANDLING_URL}"
)
INITIALIZE_RUNNER_SUCCESS_MESSAGE = "Success: Runner '{}' [{}] initialized."

GET_RUNNER_RESPONSE_MESSAGE = "Info: Waiting for Runner response..."
GET_RUNNER_RESPONSE_ERROR_MESSAGE = (
    "Error: Failed to retrieve response from Runner '{}' [{}].\n"
    "This error may be related to a MicroK8s issue during GPU plugin installation.\n"
    f"For guidance on resolving this issue, visit {DOCS_ERROR_HANDLING_URL}"
)
GET_RUNNER_RESPONSE_SUCCESS_MESSAGE = (
    "Success: Received response from Runner '{}' [{}]."
)

KEYBOARD_INTERRUPT_MESSAGE = "Info: Installation interrupted by user!"
INSTALL_CLEANUP_MESSAGE = "Info: Cleaning up resources..."
INSTALL_CLEANUP_SUCCESS_MESSAGE = "Success: Resources cleaned up."

PING_SERVER_CONNECTION_ERROR_MESSAGE = (
    "Error: Failed to connect to server. Ensure you have an active internet connection.\n"
    f"For more information, visit: {DOCS_ERROR_HANDLING_URL} or contact support: {SUPPORT_EMAIL}"
)
FEATURE_NOT_AVAILABLE_ERROR_MESSAGE = (
    "Error: Your workspace does not have access to this feature.\n"
    f"For more information, visit: {DOCS_ERROR_HANDLING_URL} or contact support: {SUPPORT_EMAIL}"
)
PING_SERVER_FORBIDDEN_ERROR_MESSAGE = (
    "Error: Failed to ping server. "
    "The Workspace ID / Secret Key combination has been invalidated. "
    "A user in your workspace may have generated a new key.\n"
    "Please obtain the new key, or regenerate one for your workspace on Nexus: "
    "https://nexus.datature.io/workspace/{}/settings#key\n"
    "Finally, run `datature runner reauth` to reauthenticate."
    f"For more information, visit: {DOCS_ERROR_HANDLING_URL} or contact support: {SUPPORT_EMAIL}"
)
PING_SERVER_UNKNOWN_ERROR_MESSAGE = (
    "{}\n"
    "Error: Failed to ping server.\n"
    f"For more details, visit: {DOCS_ERROR_HANDLING_URL} or contact support: {SUPPORT_EMAIL}"
)

UNINSTALL_RUNNER_MESSAGE = "Info: Uninstalling Runner '{}' [{}]..."
LOCAL_UNINSTALL_ACTION_MESSAGE = (
    "Warning: Server connection with Nexus could not be established. "
    "Runner will only be uninstalled locally."
)
DELETE_PODS_MESSAGE = "Info: Namespace '{}': Deleting all pods..."
DELETE_SECRETS_MESSAGE = "Info: Namespace '{}': Deleting all secrets..."
DELETE_DEPLOYMENTS_MESSAGE = "Info: Namespace '{}': Deleting all deployments..."
DELETE_ROLE_BINDINGS_MESSAGE = "Info: Namespace '{}': Deleting all role bindings..."
DELETE_ROLES_MESSAGE = "Info: Namespace '{}': Deleting all roles..."
DELETE_SERVICE_ACCOUNTS_MESSAGE = (
    "Info: Namespace '{}': Deleting all service accounts..."
)
DELETE_CONFIG_MAPS_MESSAGE = "Info: Namespace '{}': Deleting all config maps..."
DELETE_NAMESPACE_MESSAGE = "Info: Deleting namespace '{}'..."
UNINSTALL_RUNNER_ERROR_MESSAGE = (
    "{}\n"
    "Error: Failed to uninstall Runner '{}' [{}].\n"
    f"For assistance, please contact us at {SUPPORT_EMAIL}."
)
UNINSTALL_RUNNER_SUCCESS_MESSAGE = "Success: Runner '{}' [{}] uninstalled successfully."

SUSPEND_RUNNER_MESSAGE = "Suspending Runner '{}' [{}]..."
LOCAL_SUSPEND_ACTION_MESSAGE = (
    "Warning: Server connection with Nexus could not be established. "
    "Runner will only be suspended locally."
)
SUSPEND_RUNNER_CONNECTION_ERROR_MESSAGE = (
    "Error: Failed to suspend Runner '{}' [{}].\n"
    "Ensure you have an active internet connection.\n"
    f"For assistance with suspending your runner, visit {DOCS_ERROR_HANDLING_URL}."
)
SUSPEND_RUNNER_FORBIDDEN_ERROR_MESSAGE = (
    "Error: Failed to suspend Runner '{}' [{}].\n"
    "The Workspace ID / Secret Key combination has been invalidated. "
    "A user in your workspace may have generated a new key.\n"
    "Please obtain the new key, or regenerate one for your workspace on Nexus: "
    "https://nexus.datature.io/workspace/{}/settings#key\n"
    "Finally, run `datature runner reauth` to reauthenticate."
    f"For assistance with suspending your runner, visit {DOCS_ERROR_HANDLING_URL}."
)
SUSPEND_RUNNER_UNKNOWN_ERROR_MESSAGE = (
    "Error: Failed to suspend Runner '{}' [{}].\n"
    f"For further assistance, please contact us at {SUPPORT_EMAIL}."
)
SUSPEND_RUNNER_SUCCESS_MESSAGE = "Success: Runner '{}' [{}] suspended successfully."

RESUME_RUNNER_MESSAGE = "Resuming Runner '{}' [{}]..."
LOCAL_RESUME_ACTION_MESSAGE = (
    "Warning: Server connection with Nexus could not be established. "
    "Runner will only be resumed locally."
)
RESUME_RUNNER_CONNECTION_ERROR_MESSAGE = (
    "Error: Failed to resume Runner '{}' [{}].\n"
    "Ensure you have an active internet connection.\n"
    f"For assistance with resuming your runner, visit {DOCS_ERROR_HANDLING_URL}."
)
RESUME_RUNNER_FORBIDDEN_ERROR_MESSAGE = (
    "Error: Failed to resume Runner '{}' [{}].\n"
    "The Workspace ID / Secret Key combination has been invalidated. "
    "A user in your workspace may have generated a new key.\n"
    "Please obtain the new key, or regenerate one for your workspace on Nexus: "
    "https://nexus.datature.io/workspace/{}/settings#key\n"
    "Finally, run `datature runner reauth` to reauthenticate."
    f"For assistance with resuming your runner, visit {DOCS_ERROR_HANDLING_URL}."
)
RESUME_RUNNER_UNKNOWN_ERROR_MESSAGE = (
    "Error: Failed to resume Runner '{}' [{}].\n"
    f"For further assistance, please contact us at {SUPPORT_EMAIL}."
)
RESUME_RUNNER_SUCCESS_MESSAGE = "Success: Runner '{}' [{}] resumed successfully."

RESTART_RUNNER_MESSAGE = "Restarting Runner '{}' [{}]..."
LOCAL_RESTART_ACTION_MESSAGE = (
    "Warning: Server connection with Nexus could not be established. "
    "Runner will only be restarted locally."
)
RESTART_RUNNER_ERROR_MESSAGE = (
    "{}\n"
    "Error: Failed to restart deployment '{}' in namespace '{}'.\n"
    f"For assistance, please contact us at {SUPPORT_EMAIL}."
)
RESTART_RUNNER_SUCCESS_MESSAGE = "Success: Deployment '{}' restarted successfully."

UNCHANGED_SECRET_KEY_MESSAGE = (
    "Info: Secret key unchanged, reauthentication is not necessary."
)
REAUTH_RUNNER_SUCCESS_MESSAGE = (
    "Success: Runner '{}' [{}] reauthenticated successfully."
)
REAUTH_RUNNER_ERROR_MESSAGE = (
    "{}\n"
    "Error: Failed to reauthenticate runner in namespace '{}'.\n"
    f"For support, please contact us at {SUPPORT_EMAIL}."
)

DUMP_RUNNER_LOGS_MESSAGE = "Info: Dumping logs for Runner '{}' [{}]..."
FOUND_MULTIPLE_PODS_ERROR_MESSAGE = (
    "Error: Multiple Runner pods found in namespace '{}'.\n"
    f"For help, visit: {DOCS_ERROR_HANDLING_URL} or contact support: {SUPPORT_EMAIL}"
)
READ_RUNNER_LOGS_ERROR_MESSAGE = (
    "Error: Failed to read Runner logs in namespace '{}'.\n"
    f"For more details, visit: {DOCS_ERROR_HANDLING_URL} or contact support: {SUPPORT_EMAIL}"
)
RUN_LOGS_NOT_FOUND_ERROR_MESSAGE = (
    "Error: No logs found for run '{}'. Ensure the run is active and generating logs.\n"
    f"For more information, visit: {DOCS_ERROR_HANDLING_URL}"
)
RUNNER_LOGS_NOT_FOUND_ERROR_MESSAGE = (
    "Error: No logs found for Runner '{}' [{}]. Ensure the Runner is active and generating logs.\n"
    f"For more information, visit: {DOCS_ERROR_HANDLING_URL}"
)
DUMP_RUNNER_LOGS_SUCCESS_MESSAGE = "Logs dumped to {}."

RETRIEVE_RUNS_ERROR_MESSAGE = (
    "Error: Failed to retrieve ongoing runs.\n"
    f"For more details, visit: {DOCS_ERROR_HANDLING_URL} or contact support: {SUPPORT_EMAIL}"
)
RETRIEVE_RUNNER_STATUS_ERROR_MESSAGE = (
    "Error: Failed to get Runner status in namespace '{}'.\n"
    f"For more details, visit: {DOCS_ERROR_HANDLING_URL} or contact support: {SUPPORT_EMAIL}"
)
RUNNER_INVALID_SECRET_KEY_MESSAGE = (
    "The Workspace ID / Secret Key combination has been invalidated. "
    "A user in your workspace may have generated a new key.\n"
    "Please obtain the new key, or regenerate one for your workspace on Nexus: "
    "https://nexus.datature.io/workspace/{}/settings#key\n"
    "Finally, run `datature runner reauth` to reauthenticate.\n"
    f"For more information, visit: {DOCS_ERROR_HANDLING_URL}"
)

RUNNER_UNKNOWN_ERROR_MESSAGE = (
    "Error: An unknown error occurred while processing the Runner. Full traceback logged to {}.\n"
    f"For more information, visit: {DOCS_ERROR_HANDLING_URL} or contact support: {SUPPORT_EMAIL}"
)
RUNNER_TRACEBACK_MESSAGE = "Full traceback logged to {}."

UPDATE_RUNNER_CONNECTION_ERROR_MESSAGE = (
    "Error: Failed to connect to Runner '{}' [{}]. Ensure you have an active internet connection.\n"
    f"For more information, visit: {DOCS_ERROR_HANDLING_URL}"
)
UPDATE_RUNNER_FORBIDDEN_ERROR_MESSAGE = (
    "Error: Failed to update Runner '{}' [{}].\n"
    "The Workspace ID / Secret Key combination has been invalidated. "
    "A user in your workspace may have generated a new key. "
    "Please obtain the new key, or regenerate one for your workspace on Nexus: "
    "https://nexus.datature.io/workspace/{}/settings#key\n"
    "Finally, run `datature runner reauth` to reauthenticate.\n"
    f"For more details, visit: {DOCS_ERROR_HANDLING_URL}"
)
UPDATE_RUNNER_UNKNOWN_ERROR_MESSAGE = (
    "Error: Failed to update Runner '{}' [{}].\n"
    f"For more details, visit: {DOCS_ERROR_HANDLING_URL} or contact support: {SUPPORT_EMAIL}"
)
