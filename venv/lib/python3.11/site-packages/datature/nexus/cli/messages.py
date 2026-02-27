#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   messages.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   collect all string messages variables
"""

REQUEST_SERVER_MESSAGE = "Communicating with server."
SERVER_COMPLETED_MESSAGE = "Server processing completed."
INVALID_PROJECT_SECRET_MESSAGE = (
    "\nInvalid project secret key, "
    "generate one for your project on Nexus: Advanced/API Management"
)
AUTHENTICATION_MESSAGE = "Authentication succeeded."
AUTHENTICATION_REMINDER_MESSAGE = (
    "\nSecret Key needed, "
    "generate one for your project on Nexus: Advanced/API Management"
)
NO_PROJECT_MESSAGE = (
    "\nMissing authentication, please authenticate with 'datature projects auth'."
)
ASSETS_FOLDER_MESSAGE = "Enter the assets folder path to be uploaded"
ASSETS_GROUPS_MESSAGE = "Enter the asset group name(s), split by ','"
ANNOTATION_FOLDER_MESSAGE = (
    "Enter the folder path containing the annotation files to be uploaded"
)
ANNOTATION_FORMAT_MESSAGE = "Select the annotation file format"
NO_ANNOTATIONS_MESSAGE = (
    "\nNo annotations found in the project. Please annotate assets on Nexus, "
    "or upload annotations with 'datature annotations upload'."
)
NO_ARTIFACTS_MESSAGE = (
    "\nNo workspace artifacts found. Please elevate at least "
    "one project artifact to the workspace level."
)
ARTIFACT_DOWNLOAD_MESSAGE = "Which artifact do you want to download?"
ARTIFACT_MODEL_FORMAT_DOWNLOAD_MESSAGE = "Which model format do you want to download?"
EXPORT_ARTIFACT_WAITING_MESSAGE = (
    "Processing artifact for download, it may take 5-10 minutes.\n"
)
ARTIFACT_MODEL_FOLDER_MESSAGE = "Enter the folder path to save model"
EXPORT_ANNOTATION_FOLDER_MESSAGE = "Enter the folder path to save annotation files"
CHOOSE_GROUP_MESSAGE = "Which asset group do you want to list?"
INVALID_PROJECT_MESSAGE = "\nInvalid project name."
PATH_NOT_EXISTS_MESSAGE = "\nPath does not exist."
NO_ASSETS_GROUP_MESSAGE = "\nNo asset groups exist in this project."
DOWNLOAD_ANNOTATIONS_NORMALIZED_MESSAGE = "Should the annotations be normalized?"
DOWNLOAD_ANNOTATIONS_SPLIT_RATIO_MESSAGE = (
    "Enter the split ratio for this download. [0-100%]"
)
INVALID_SPLIT_RATIO_MESSAGE = "\nInvalid split ratio."
AUTHENTICATION_FAILED_MESSAGE = (
    "\nAuthentication failed, please use 'datature projects auth' again."
)
UNKNOWN_ERROR_SUPPORT_MESSAGE = (
    "\nCommunication failed, contact support at support@datature.io."
)
CONNECTION_ERROR_MESSAGE = "\nConnection failed, please check your network."
UNKNOWN_ERROR_MESSAGE = (
    "\nUnknown error occurred, contact support at support@datature.io."
)
ANNOTATION_DOWNLOAD_MESSAGE = "Processing annotations for download."
ANNOTATION_DOWNLOADED_MESSAGE = "Downloaded annotations."
ACTIVE_PROJECT_MESSAGE = "Your active project is now"
NO_ASSETS_FOUND_MESSAGE = (
    "No allowable assets found in folders, please change the folder path."
)
ASSETS_NIFTI_DIRECTION_CHOICE_MESSAGE = (
    "Select the axis of orientation, "
    "if not provided, we will save videos for each axis. ['x','y','z']"
)
RUNNER_EXISTS_MESSAGE = (
    "A Runner already exists. Multiple runners are currently not supported.\n"
    "If you would like to install a new Runner, "
    "please first uninstall the existing Runner by running `datature runner uninstall`.\n"
    "To view all available Runners, run `datature runner list`."
)
RUNNER_INSTALL_SIZE_MESSAGE = (
    "The Runner will take up approximately 754MB of disk space.\n"
    "To run trainings on your Runner, it is also recommended to have "
    "an additional minimum of 8GB of disk space on your system. Continue?"
)
MAX_RETRY_MESSAGE = "Maximum number of retries reached. Please ensure your details are correct and try again."
RUNNER_NAME_MESSAGE = "Please enter the name for your custom runner:"
EMPTY_RUNNER_NAME_MESSAGE = (
    "Runner name cannot be left blank. Please try again.\n"
    "Ensure to provide a meaningful name for easy identification."
)
DUPLICATE_RUNNER_NAME_MESSAGE = (
    "Runner name already exists. Please enter a unique name for your Runner."
)
SECRET_KEY_MESSAGE = "Please enter your workspace secret key:"
NEW_SECRET_KEY_MESSAGE = "Please enter your new workspace secret key:"
EMPTY_SECRET_KEY_MESSAGE = (
    "Workspace secret key cannot be left blank.\n"
    "Generate one for your workspace on Nexus, under Settings/Key Manager."
)
INVALID_SECRET_KEY_LENGTH_MESSAGE = (
    "Invalid secret key length. Please try again.\n"
    "Ensure to provide the correct secret key for your workspace."
)
ALL_RUNNERS_VALID_SECRET_KEYS_MESSAGE = "All Runners have valid secret keys."
WORKSPACE_ID_MESSAGE = "Please enter your workspace ID:"
EMPTY_WORKSPACE_ID_MESSAGE = (
    "Workspace ID cannot be left blank. Please try again.\n"
    "Double-check your workspace ID and enter it correctly."
)
INVALID_WORKSPACE_ID_LENGTH_MESSAGE = (
    "Invalid workspace ID length. Please try again.\n"
    "Ensure to provide the correct workspace ID for your workspace."
)
NO_RUNNERS_MESSAGE = (
    "No existing Runners found. Please run `datature runner install` to set up a Runner.\n"
    "Ensure your environment meets the necessary requirements before installation."
)
NO_ACTIONABLE_RUNNERS_MESSAGE = "No actionable Runners found to {}. Please run `datature runner list` to view Runner statuses."
UNINSTALL_RUNNERS_CONFIRMATION_MESSAGE = (
    "Are you sure you want to uninstall selected Runner(s)? This action is irreversible.\n"
    "Uninstalling will remove all associated data and configurations."
)
KILL_RUNS_CONFIRMATION_MESSAGE = (
    "There may be ongoing runs associated with Runner '{}' [{}] that will be killed.\n"
    "Ensure to save any necessary data before proceeding.\n"
    "Do you wish to continue?"
)
VALID_SECRET_KEY_MESSAGE = (
    "Secret key for Runner '{}' [{}] is valid, reauthentication is not necessary."
)
INVALID_SECRET_KEYS_MESSAGE = (
    "One or more workspace secret keys are invalid. "
    "A user in your workspace may have generated new keys.\n"
    "Please run `datature runner reauth` to reauthenticate, "
    "and double-check your secret keys for accuracy."
)
NO_OUTPOST_DEVICE_REGISTERED_MESSAGE = (
    "This device has not been registered with Outpost. "
    "Please run `datature outpost install` to register this device."
)
