#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   functions.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   CLI Functions
"""
# pylint: disable=E1102,R0912,C0103,R0914

import os
import re
import sys
import time
from os.path import basename, exists, isdir, join
from pathlib import Path

import requests
from alive_progress import alive_bar
from halo import Halo
from InquirerPy import inquirer

from datature import nexus
from datature.nexus import config, error
from datature.nexus.cli import messages
from datature.nexus.cli.config import Config
from datature.nexus.utils import utils


def start_spinner(fn: callable):
    """Start spinner for the function."""

    def wrapper(*args, **kwargs):
        wait_spinner = Halo(text=messages.REQUEST_SERVER_MESSAGE, spinner="dots")
        wait_spinner.start()

        try:
            result = fn(*args, **kwargs)
            return result
        finally:
            wait_spinner.stop()

    return wrapper


def get_default_datature_client():
    """
    Get default datature client from configuration file.

    :return: The default datature client.
    """
    cli_config = Config()
    project = cli_config.get_default_project()

    if project is None:
        print(messages.NO_PROJECT_MESSAGE)
        sys.exit(1)

    return nexus.Client(project.get("project_secret")).get_project(
        project.get("project_id")
    )


@start_spinner
def sdk_list_project(secret_key: str):
    """Retrieve project from server."""
    sdk_client = nexus.Client(secret_key)

    projects = sdk_client.list_projects()
    # Support to use workspace after one secret support multiple projects
    return projects


@start_spinner
def sdk_retrieve_project(project_secret: str, project_id: str):
    """Retrieve project from server."""
    sdk_project = nexus.Client(project_secret)

    project = sdk_project.get_project(project_id)

    return project


@start_spinner
def sdk_create_upload_session():
    """Retrieve project from server."""
    sdk_project = get_default_datature_client()

    import_session = sdk_project.annotations.create_import_session()

    return import_session


def sdk_retrieve_operation(op_id: str):
    """Retrieve operation from server."""
    sdk_project = get_default_datature_client()

    operation = sdk_project.operations.get(op_id)
    return operation


def download_file_from_link(link: str, download_path: str):
    """
    Download file from link.

    :param link: The url link.
    :param download_path: The path to download file.
    :return: None
    """
    query_string_removed = link.split("?")[0]
    file_name = basename(query_string_removed)

    resp = requests.get(link, stream=True, timeout=120)

    total = int(resp.headers.get("content-length", 0))
    current_size = 0
    with open(join(download_path, file_name), "wb") as file, alive_bar(
        total, title="Downloading", title_length=12, manual=True
    ) as progress_bar:
        for data in resp.iter_content(chunk_size=1024):
            size = file.write(data)
            current_size += size
            progress_bar(float(current_size / total))
        progress_bar(1.0)


def authenticate():
    """
    Authenticate the Workspace Secret with the server and creates a
    configuration file for it.

    :param secret_key: Secret key to use for the client login.
    :return: None
    """
    secret_key = inquirer.secret(message="Enter the secret key").execute().strip()

    secret_key = secret_key.strip()
    if secret_key == "":
        print(messages.AUTHENTICATION_REMINDER_MESSAGE)
        sys.exit(1)

    try:
        projects = sdk_list_project(secret_key)

        project_name = inquirer.select(
            "Which project do you want to select?",
            choices=[project.get_info().name for project in projects],
            border=True,
        ).execute()

        for project in projects:
            if project.get_info().name == project_name:
                project_id = project.get_info().id
                break
        else:
            print(messages.INVALID_PROJECT_MESSAGE)
            sys.exit(1)

        default_project = inquirer.confirm(
            f"Make [{project_name}] the default project?", default=True
        ).execute()

        cli_config = Config()
        cli_config.set_project(project_id, project_name, secret_key, default_project)

    except error.ForbiddenError:
        print(messages.INVALID_PROJECT_SECRET_MESSAGE)
        sys.exit(1)
    print(messages.AUTHENTICATION_MESSAGE)


def select_project():
    """
    Select project from saved configuration file.

    :return: None
    """
    cli_config = Config()
    project_names = cli_config.get_all_project_names()

    project_name = inquirer.select(
        "Which project do you want to select?", choices=project_names, border=True
    ).execute()
    project = cli_config.get_project_by_name(project_name)

    cli_config.set_default_project(project.get("project_id"))
    print(f"{messages.ACTIVE_PROJECT_MESSAGE}: [{project_name}]")


def list_projects():
    """
    List projects from saved configuration file.

    :return: None
    """
    cli_config = Config()
    project_names = cli_config.get_all_project_names()
    default_project = cli_config.get_default_project()

    output = [["NAME", "TOTAL_ASSETS", "ANNOTATED_ASSETS", "ANNOTATIONS", "TAGS"]]
    for project_name in project_names:
        project = cli_config.get_project_by_name(project_name)
        try:
            project = sdk_retrieve_project(
                project.get("project_secret"), project.get("project_id")
            )
            project_info = project.get_info()

            total_assets = project_info.statistic.total_assets
            annotated_assets = project_info.statistic.annotated_assets
            total_annotations = project_info.statistic.total_annotations
            tags = project_info.tags

            output.append(
                [
                    project_name,
                    total_assets,
                    annotated_assets,
                    total_annotations,
                    len(tags),
                ]
            )
        except error.ForbiddenError:
            print(
                (
                    f"Project {[project_name]} "
                    "authentication failed, please use 'datature projects auth' "
                    "again.\n"
                )
            )

    if len(output) == 0:
        print(messages.NO_PROJECT_MESSAGE)
        sys.exit(1)

    print_table(output, 20)

    active_project = default_project.get("project_name")

    print(f"\n{messages.ACTIVE_PROJECT_MESSAGE}: [{active_project}]")


def cli_loop_operation(op_id: str, data_size: int):
    """
    Upload annotations from path.

    :param path: The annotation path to upload.
    :param annotation_format: The annotation format to upload.
    :return: None
    """
    # Custom manage loop
    try:
        with alive_bar(
            data_size, title="Processing", title_length=12, length=30, manual=True
        ) as progress_bar:
            while True:
                operation = sdk_retrieve_operation(op_id)

                if operation.status.overview == "Errored":
                    print(messages.UNKNOWN_ERROR_MESSAGE)
                    sys.exit(1)

                count = operation.status.progress.with_status

                queued = count.Queued
                running = count.Running
                finished = count.Finished
                cancelled = count.Cancelled
                errored = count.Errored
                percentage = float(
                    (int(errored) + int(cancelled) + int(finished))
                    / (
                        int(errored)
                        + int(cancelled)
                        + int(finished)
                        + int(queued)
                        + int(running)
                    )
                )

                if percentage == 1:
                    break

                progress_bar(percentage)
                time.sleep(config.OPERATION_LOOPING_DELAY_SECONDS)
            progress_bar(1.0)

    except KeyboardInterrupt:
        print(f"\n⚠️  Operation monitoring interrupted for operation {op_id}")
        print("   The upload operation may continue in the background.")
        print("   You can check the operation status later.")
        sys.exit(0)

    print(messages.SERVER_COMPLETED_MESSAGE)


def upload_assets():
    """
    Upload assets from path.

    :param path: The folder to upload assets.
    :return: None
    """

    path = (
        Path(
            inquirer.filepath(
                message=messages.ASSETS_FOLDER_MESSAGE, default=os.getcwd()
            ).execute()
        )
        .expanduser()
        .resolve()
    )

    if not exists(path):
        print(messages.PATH_NOT_EXISTS_MESSAGE)
        sys.exit(1)

    # find all images under folder and sub folders
    file_paths = utils.find_all_assets(path)

    if len(file_paths) == 0:
        print(messages.NO_ASSETS_FOUND_MESSAGE)
        sys.exit(1)

    groups_res = inquirer.text(
        messages.ASSETS_GROUPS_MESSAGE,
        default="main",
        validate=lambda x: re.match(r"^[A-Za-z0-9,\s?]*$", x),
    ).execute()
    groups = [group.strip() for group in groups_res.split(",") if group.strip()]

    confirm = inquirer.confirm(
        f"""{len(file_paths)} assets will be uploaded to group(s) ({
            ', '.join(groups)})?""",
        default=True,
    ).execute()

    if not confirm:
        sys.exit(0)

    sdk_project = get_default_datature_client()

    try:
        upload_session = sdk_project.assets.create_upload_session(
            groups=groups, background=True, show_progress=False
        )

        with alive_bar(
            len(file_paths),
            length=30,
            title="Uploading",
            title_length=12,
        ) as progress_bar, upload_session as session:
            for file_path in file_paths:
                session.add_path(file_path)
                progress_bar()

        operations = upload_session.get_operation_ids()

        cli_loop_operation(operations[0], len(upload_session))

    except KeyboardInterrupt:
        print("\n⚠️  Asset upload interrupted")
        sys.exit(0)

    except error.Error as exc:
        print(f"Error uploading assets: {exc}")
        sys.exit(1)


def upload_annotations():
    """
    Upload annotations from path.

    :param path: The annotation path to upload.
    :return: None
    """
    path = (
        Path(
            inquirer.filepath(
                message=messages.ANNOTATION_FOLDER_MESSAGE, default=os.getcwd()
            ).execute()
        )
        .expanduser()
        .resolve()
    )

    # find all images under folder and sub folders
    if isdir(path):
        file_paths = utils.find_all_annotations_files(path)
    else:
        file_paths = [path]

    confirm = inquirer.confirm(
        f"{len(file_paths)} file(s) will be uploaded?", default=True
    ).execute()
    if not confirm:
        sys.exit(0)

    batch_size = config.ANNOTATION_IMPORT_SESSION_BATCH_SIZE

    num_batches = len(file_paths) // batch_size
    batches = [
        file_paths[i * batch_size : (i + 1) * batch_size] for i in range(num_batches)
    ]

    if len(file_paths) % batch_size != 0:
        batches.append(file_paths[num_batches * batch_size :])

    # Loop Prepare asset metadata
    for _, batch in enumerate(batches):
        import_session = sdk_create_upload_session()

        with alive_bar(
            len(batch),
            length=30,
            title="Preparing",
            title_length=12,
        ) as progress_bar, import_session as session:
            for file_path in batch:
                progress_bar()

                session.add_path(file_path)

    print(messages.SERVER_COMPLETED_MESSAGE)


def download_artifact():
    """
    Download artifact model.

    :param artifact_id: The id of the artifact.
    :param model_format: The artifact model to download.
    :param path: The path to download the model.
    :return: None
    """
    path = (
        Path(
            inquirer.filepath(
                message=messages.ARTIFACT_MODEL_FOLDER_MESSAGE, default=os.getcwd()
            ).execute()
        )
        .expanduser()
        .resolve()
    )

    if not exists(path):
        print(messages.PATH_NOT_EXISTS_MESSAGE)
        sys.exit(1)

    sdk_project = get_default_datature_client()

    # call server to list all artifacts
    artifacts = sdk_project.artifacts.list(include_exports=True)
    if len(artifacts) == 0:
        print(messages.NO_ARTIFACTS_MESSAGE)
        sys.exit(1)

    artifact_lists = []
    artifacts_key_map = {}
    for artifact in artifacts:
        key = f"""{artifact.get('run_id')[-6:].upper()
                    }-{artifact.get('flow_title')}"""
        artifact_lists.append(key)
        artifacts_key_map[key] = artifact

    artifact_key = inquirer.select(
        message=messages.ARTIFACT_DOWNLOAD_MESSAGE,
        choices=artifact_lists,
        border=True,
    ).execute()
    artifact = artifacts_key_map.get(artifact_key)

    model_format = inquirer.select(
        message=messages.ARTIFACT_MODEL_FORMAT_DOWNLOAD_MESSAGE,
        choices=[option.format for option in artifact.export_options],
        border=True,
    ).execute()

    exported_formats = [export.format for export in artifact.exports]
    if model_format in exported_formats:
        # already exported, can download directly
        for model in artifact.exports:
            if model.format == model_format and model.status == "Finished":
                download_file_from_link(model.download.url, path)

    else:
        # not exported, need looping query download status
        # Loop to query status,
        wait_spinner = Halo(
            text=messages.EXPORT_ARTIFACT_WAITING_MESSAGE, spinner="dots"
        )
        wait_spinner.start()
        models = sdk_project.artifacts.create_export(
            artifact.id, {"format": model_format}
        )

        while True:
            models = sdk_project.artifacts.list_exported_models(artifact.get("id"))
            for model in models:
                if (
                    model.get("format") == model_format
                    and model.get("status") == "Finished"
                ):
                    # start download
                    wait_spinner.stop()
                    download_file_from_link(model.download.url, path)

                    return

            time.sleep(config.OPERATION_LOOPING_DELAY_SECONDS)


def download_annotations():
    """
    Export annotations from path.

    :param path: The annotation path to export.
    :param annotation_format: The annotation format to export.
    :return: None
    """
    sdk_project = get_default_datature_client()
    project_info = sdk_project.get_info()
    num_annotated_assets = project_info.statistic.annotated_assets

    if num_annotated_assets == 0:
        print(messages.NO_ANNOTATIONS_MESSAGE)
        sys.exit(1)

    path = (
        Path(
            inquirer.filepath(
                message=messages.EXPORT_ANNOTATION_FOLDER_MESSAGE,
                default=os.getcwd(),
            ).execute()
        )
        .expanduser()
        .resolve()
    )

    if not exists(path):
        print(messages.PATH_NOT_EXISTS_MESSAGE)
        sys.exit(1)

    annotations_formats = utils.get_exportable_annotations_formats(project_info.type)
    annotation_format = inquirer.select(
        message=messages.ANNOTATION_FORMAT_MESSAGE,
        choices=annotations_formats,
        border=True,
    ).execute()

    normalized = inquirer.confirm(
        message=messages.DOWNLOAD_ANNOTATIONS_NORMALIZED_MESSAGE
    ).execute()

    if num_annotated_assets > 1:
        split_ratio = round(
            int(
                inquirer.number(
                    message=messages.DOWNLOAD_ANNOTATIONS_SPLIT_RATIO_MESSAGE,
                    default=0,
                    min_allowed=0,
                    max_allowed=100,
                ).execute()
            )
            / 100,
            2,
        )
    else:
        split_ratio = 0.0

    # Loop to query status
    wait_spinner = Halo(text=messages.ANNOTATION_DOWNLOAD_MESSAGE, spinner="dots")
    wait_spinner.start()
    operation = sdk_project.annotations.create_export(
        {
            "format": annotation_format,
            "options": {
                "split_ratio": split_ratio,
                "seed": 1337,
                "normalized": normalized,
            },
        }
    )

    wait_spinner.stop()

    cli_loop_operation(operation.id, 1)

    sdk_project.annotations.download_exported_file(operation.id, path)

    print(messages.ANNOTATION_DOWNLOADED_MESSAGE)


def print_table(data: [[str]], column_width: int = 16):
    """
    List assets group statistics.

    :param data: The element array.
    :param column_width: The column widths and separator characters
    :return: None
    """
    # Print the table header
    print("".join(f"{item:{column_width}}" for _, item in enumerate(data[0])))

    # Print the table data
    for row in data[1:]:
        print("".join(f"{str(item):{column_width}}" for _, item in enumerate(row)))


def assets_group():
    """
    List assets group statistics.

    :param group: The name of group.
    :return: None
    """
    sdk_project = get_default_datature_client()

    project = sdk_project.get_info()

    groups = project.groups
    if groups is None or len(groups) == 0:
        print(messages.NO_ASSETS_GROUP_MESSAGE)
        sys.exit(1)

    selected_groups = inquirer.select(
        messages.CHOOSE_GROUP_MESSAGE,
        choices=groups,
        multiselect=True,
        default=groups,
        border=True,
    ).execute()

    statistics = sdk_project.assets.list_groups(selected_groups)

    table = [["NAME", "TOTAL", "ANNOTATED", "REVIEW", "TOFIX", "COMPLETED"]]
    for result in statistics:
        table.append(
            [
                result.group,
                result.statistic.total_assets,
                result.statistic.annotated_assets,
                result.statistic.reviewed_assets,
                result.statistic.to_fixed_assets,
                result.statistic.completed_assets,
            ]
        )
    print_table(table)
