#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   job.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   CLI Batch Job Functions.
"""
# pylint: disable=R0913,R0914

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
from colorama import Fore
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.validator import EmptyInputValidator
from wcwidth import wcswidth

import datature.nexus.cli.batch.functions as batch_functions
from datature.nexus import error, models
from datature.nexus.api.batch import models as batch_models
from datature.nexus.cli import consts
from datature.nexus.cli.batch.dataset import create_dataset
from datature.nexus.cli.batch.webhook import create_webhook
from datature.nexus.cli.functions import get_default_datature_client
from datature.nexus.utils import utils

logging.basicConfig(level=logging.CRITICAL)


def prompt_for_timings() -> Tuple[int, int]:
    """
    Prompts the user for the start and stop times of the BatchJob.

    :return: The start and stop times of the BatchJob in milliseconds.
    """
    timezone = utils.get_timezone()

    start_datetime = inquirer.text(
        "Enter when you want the BatchJob to start:",
        long_instruction="Leave blank to start immediately",
        mandatory=False,
        validate=utils.DateTimeValidator(timezone=timezone),
        filter=lambda x: utils.DateTimeValidator.parse(x, timezone),
    ).execute()

    if not start_datetime:
        start_datetime = datetime.now(timezone)

    start_time_ms = int(start_datetime.timestamp() * 1000)
    start_time_difference = start_datetime - datetime.now(timezone)

    print(
        f"Start Time: {Fore.GREEN}"
        f"{utils.pretty_print_datetime(start_datetime, timezone)}",
        (
            f"{Fore.CYAN}[in {utils.timedelta_to_str(start_time_difference)}]{Fore.RESET}"
            if start_time_difference.total_seconds() > 0
            else f"{Fore.CYAN}[Now]{Fore.RESET}"
        ),
    )

    stop_datetime = inquirer.text(
        "Enter when you want the BatchJob to stop:",
        long_instruction=(
            "Leave blank to stop only after all Dataset items "
            "are predicted (default cutoff 3 days)"
        ),
        mandatory=False,
        validate=utils.DateTimeValidator(
            start_datetime=start_datetime, timezone=timezone
        ),
        filter=lambda x: utils.DateTimeValidator.parse(x, timezone),
    ).execute()

    if stop_datetime:
        stop_time_ms = int(stop_datetime.timestamp() * 1000)
        stop_time_difference = stop_datetime - datetime.now(timezone)
        print(
            f"Cutoff Time: {Fore.GREEN}"
            f"{utils.pretty_print_datetime(stop_datetime, timezone)}",
            (
                f"{Fore.CYAN}[in {utils.timedelta_to_str(stop_time_difference)}]{Fore.RESET}"
                if stop_time_difference.total_seconds() > 0
                else f"{Fore.CYAN}[Now]{Fore.RESET}"
            ),
        )
    else:
        stop_time_ms = None
        print(
            f"Cutoff Time: {Fore.CYAN}After all Dataset items are predicted{Fore.RESET}"
        )

    return start_time_ms, stop_time_ms


def prompt_for_webhook() -> str:
    """
    Prompts the user to select an existing Webhook or create a new one.

    :return: The ID of the selected or created Webhook.
    """
    sdk_project = get_default_datature_client()

    has_existing_webhooks = len(sdk_project.batch.webhooks.list().data) > 0
    webhook_choices = [
        (
            Choice(name="Select an existing Webhook", value="existing")
            if has_existing_webhooks
            else None
        ),
        Choice(name="Create a new Webhook with default settings", value="default"),
        Choice(name="Create a new custom Webhook", value="custom"),
    ]
    webhook_choices = [choice for choice in webhook_choices if choice is not None]
    webhook_type = inquirer.select(
        message="Select how you want the BatchJob to deliver prediction results:",
        choices=webhook_choices,
        default="default",
        border=True,
    ).execute()

    if webhook_type == "existing":
        return batch_functions.select_entry("webhooks")
    return create_webhook(webhook_type)


def prompt_for_dataset() -> str:
    """
    Prompts the user to select an existing Dataset or create a new one.

    :return: The ID of the selected or created Dataset.
    """
    sdk_project = get_default_datature_client()

    has_existing_datasets = len(sdk_project.batch.datasets.list().data) > 0
    dataset_choices = [
        (
            Choice(name="Select an existing Dataset", value="existing")
            if has_existing_datasets
            else None
        ),
        Choice(name="Create a new Dataset with default settings", value="default"),
        Choice(name="Create a new custom Dataset", value="custom"),
    ]
    dataset_choices = [choice for choice in dataset_choices if choice is not None]
    dataset_type = inquirer.select(
        message="Select how you want to specify the Dataset for prediction by this BatchJob:",
        choices=dataset_choices,
        default="default",
        border=True,
    ).execute()

    if dataset_type == "existing":
        return batch_functions.select_entry("datasets")
    return create_dataset(dataset_type)


def get_available_instances(
    artifact_id: str, resource: Optional[str] = None, region: str = "*"
) -> List[models.AvailableInstance]:
    """
    Gets the available instances for a given Artifact, region, and resource type.

    :param artifact_id: The ID of the Artifact to deploy.
    :param region: The region to deploy the Artifact to.
    :param resource: The resource type to deploy the Artifact on.
    :return: The available instances for the given Artifact, region, and resource type.
    """
    sdk_project = get_default_datature_client()

    try:
        available_instances = sdk_project.artifacts.get_available_instances(
            artifact_id, region
        )
    except error.Error as exc:
        print(
            f"{Fore.CYAN}●{Fore.RESET} Error getting available instances: {exc.message}"
        )
        sys.exit(1)

    # filter available instances by resource type
    if not resource:
        return available_instances.instances
    if resource == consts.ResourceType.CPU.value:
        return [
            instance
            for instance in available_instances.instances
            if not instance.accelerator
        ]

    return [
        instance for instance in available_instances.instances if instance.accelerator
    ]


def create_job_with_new_deployment(
    deployment_type: str,
    job_name: str,
    dataset_id: str,
    webhook_id: str,
    start_time_ms: int,
    stop_time_ms: int,
) -> batch_models.Job:
    """
    Creates a new Batch Job with a new Deployment.

    :param deployment_type: The type of Deployment to create.
    :param job_name: The name of the Batch Job.
    :param dataset_id: The ID of the Dataset to use for prediction.
    :param webhook_id: The ID of the Webhook to deliver prediction results.
    :param start_time_ms: The start time of the Batch Job in milliseconds.
    :param stop_time_ms: The stop time of the Batch Job in milliseconds.
    :return: The created Batch Job.
    """
    sdk_project = get_default_datature_client()

    artifacts = sdk_project.artifacts.list()
    if not artifacts:
        print(
            f"{Fore.CYAN}●{Fore.RESET} No Artifacts found in your project. "
            "Please first create a workflow and run a training on Nexus. "
            "For more information, refer to our Developer's Documentation: "
            "https://developers.datature.io/docs/workflows"
        )
        sys.exit(0)

    artifact_id = inquirer.fuzzy(
        message="Select the Artifact to deploy:",
        choices=[
            Choice(
                name=f"{artifact.flow_title} [#{artifact.run_id[-6:]}]",
                value=artifact.id,
            )
            for artifact in artifacts
        ],
        max_height=consts.INQUIRER_CHOICES_MAX_VISIBLE_ENTRIES,
        border=True,
    ).execute()

    inference_region = (
        inquirer.select(
            message="Select the Batch Job Inference Region:",
            long_instruction=(
                "Please choose the region closest to you for faster processing and "
                "reduced costs. If Any is selected, our servers will select "
                "a region at random based on availability."
            ),
            choices=[
                Choice(name="US", value="us"),
                Choice(name="Asia", value="asia-east1"),
                Choice(name="Any", value="*"),
            ],
            default="*",
            border=True,
        ).execute()
        if deployment_type == "custom"
        else "*"
    )

    resource = (
        inquirer.select(
            message="Do you want to use a CPU-only or GPU instance?",
            choices=[
                Choice(name="CPU-only", value="CPU"),
                Choice(name="GPU", value="GPU"),
            ],
            long_instruction=(
                "For more information on selecting the right instance: "
                "https://developers.datature.io/docs/deployment-configuration"
            ),
            border=True,
        ).execute()
        if deployment_type == "custom"
        else None
    )

    available_instances = get_available_instances(
        artifact_id, resource, inference_region
    )

    if resource:
        if resource == consts.ResourceType.GPU.value:
            instance_choices = [
                Choice(
                    name=(
                        f"{instance.id.split('_')[-1]}  [{instance.resources.cpu}x CPUs, "
                        f"{instance.resources.ram // 1000}GB RAM, "
                        f"{instance.accelerator.count}x {instance.accelerator.name}]"
                    ),
                    value=instance.id,
                )
                for instance in available_instances
            ]
        else:
            instance_choices = [
                Choice(
                    name=(
                        f"{instance.id.split('_')[-1]} [{instance.resources.cpu}x CPUs, "
                        f"{instance.resources.ram // 1000}GB RAM]"
                    ),
                    value=instance.id,
                )
                for instance in available_instances
            ]

        if not instance_choices:
            raise error.Error(
                "No instances currently available for the selected resource type. Please try again "
                "in a few minutes, or contact support at support@datature.io for assistance."
            )

        instance_type = inquirer.fuzzy(
            message="Select the Deployment instance type:",
            choices=instance_choices,
            default=(
                "x1cpu-standard"
                if resource == consts.ResourceType.CPU.value
                else "t4-standard-1g"
            ),
            long_instruction=(
                "For more information on selecting the right instance: "
                "https://developers.datature.io/docs/deployment-configuration"
            ),
            max_height=consts.INQUIRER_CHOICES_MAX_VISIBLE_ENTRIES,
            border=True,
        ).execute()
    else:
        default_instances = [
            instance.id
            for instance in available_instances
            if instance.id in consts.DEFAULT_INSTANCES
        ]
        if not default_instances:
            raise error.Error(
                "No default instances available. Please create a custom temporary Deployment."
            )
        instance_type = np.random.choice(default_instances)

    num_replicas = (
        inquirer.number(
            "Enter the number of replicas for the Deployment [1-8]:",
            default=1,
            min_allowed=1,
            max_allowed=8,
            validate=EmptyInputValidator(),
        ).execute()
        if deployment_type == "custom"
        else 1
    )

    try:
        return sdk_project.batch.jobs.create(
            name=job_name,
            job_options={
                "dataset_id": dataset_id,
                "webhook_id": webhook_id,
                "artifact_id": artifact_id,
                "deployment_metadata": (
                    {
                        "instance_id": instance_type,
                        "replicas": num_replicas,
                        "region": inference_region if inference_region != "*" else None,
                    }
                ),
                "start_at_time": start_time_ms,
                "stop_at_time": stop_time_ms,
            },
        )
    except error.Error as exc:
        print(f"{Fore.CYAN}●{Fore.RESET} Error creating Job: {exc.message}")
        sys.exit(1)


def create_job_with_existing_deployment(
    job_name: str,
    dataset_id: str,
    webhook_id: str,
    start_time_ms: int,
    stop_time_ms: int,
) -> batch_models.Job:
    """
    Creates a new Batch Job with an existing Deployment.

    :param job_name: The name of the Batch Job.
    :param dataset_id: The ID of the Dataset to use for prediction.
    :param webhook_id: The ID of the Webhook to deliver prediction results.
    :param start_time_ms: The start time of the Batch Job in milliseconds.
    :param stop_time_ms: The stop time of the Batch Job in milliseconds.
    :return: The created Batch Job.
    """
    sdk_project = get_default_datature_client()

    deployments_response = sdk_project.deployments.list()
    deployment_choices = [
        Choice(name=item.name, value=item.id) for item in deployments_response
    ]
    deployment_id = inquirer.fuzzy(
        message="Which deployment do you want to select?",
        choices=deployment_choices,
        max_height=consts.INQUIRER_CHOICES_MAX_VISIBLE_ENTRIES,
        border=True,
    ).execute()

    try:
        return sdk_project.batch.jobs.create(
            name=job_name,
            job_options={
                "dataset_id": dataset_id,
                "webhook_id": webhook_id,
                "deployment_id": deployment_id,
                "start_at_time": start_time_ms,
                "stop_at_time": stop_time_ms,
            },
        )
    except error.Error as exc:
        print(f"{Fore.CYAN}●{Fore.RESET} Error creating Job: {exc.message}")
        sys.exit(1)


def prompt_for_deployment(
    job_name: str,
    dataset_id: str,
    webhook_id: str,
    start_time_ms: int,
    stop_time_ms: int,
) -> None:
    """
    Prompts the user to select an existing Deployment or create a new one.

    :param job_name: The name of the Batch Job.
    :param dataset_id: The ID of the Dataset to use for prediction.
    :param webhook_id: The ID of the Webhook to deliver prediction results.
    :param start_time_ms: The start time of the Batch Job in milliseconds.
    :param stop_time_ms: The stop time of the Batch Job in milliseconds.
    """
    sdk_project = get_default_datature_client()

    has_existing_deployments = len(sdk_project.deployments.list()) > 0
    deployment_choices = [
        (
            Choice(name="Select an existing Deployment", value="existing")
            if has_existing_deployments
            else None
        ),
        Choice(
            name="Create a temporary Deployment with default settings", value="default"
        ),
        Choice(name="Create a custom temporary Deployment", value="custom"),
    ]
    deployment_choices = [choice for choice in deployment_choices if choice is not None]
    deployment_type = inquirer.select(
        message="Select how you want the BatchJob to perform prediction on Dataset items:",
        choices=deployment_choices,
        border=True,
    ).execute()

    if deployment_type == "existing":
        return create_job_with_existing_deployment(
            job_name, dataset_id, webhook_id, start_time_ms, stop_time_ms
        )
    return create_job_with_new_deployment(
        deployment_type, job_name, dataset_id, webhook_id, start_time_ms, stop_time_ms
    )


def create_job() -> None:
    """
    Creates a new Batch Job.
    """
    sdk_project = get_default_datature_client()

    job_type = inquirer.select(
        "Select how you want to create a BatchJob:",
        choices=[
            Choice(name="Create a new BatchJob with default settings", value="default"),
            Choice(name="Create a new custom BatchJob", value="custom"),
        ],
        default="default",
    ).execute()

    job_name = (
        (
            inquirer.text(
                "Enter a name for the BatchJob:",
                validate=utils.NameAndEmptyInputValidator(),
            )
            .execute()
            .strip()
        )
        if job_type == "custom"
        else f"batchjob-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"
    )

    start_time_ms, stop_time_ms = (
        prompt_for_timings()
        if job_type == "custom"
        else (int(datetime.now().timestamp() * 1000), None)
    )
    webhook_id = prompt_for_webhook()
    dataset_id = prompt_for_dataset()
    job = prompt_for_deployment(
        job_name, dataset_id, webhook_id, start_time_ms, stop_time_ms
    )

    print()  # for new line
    print(
        f"{Fore.GREEN}✓{Fore.RESET} Job created successfully. "
        f"Run `datature batch jobs wait-until-done {job.id}` to monitor the progress."
    )

    try:
        dataset_count = sdk_project.batch.datasets.get(
            job.spec.dataset_id
        ).status.item_count
    except error.Error as exc:
        print(f"{Fore.CYAN}●{Fore.RESET} Error getting Dataset count: {exc.message}")
        sys.exit(1)

    batch_functions.print_job_object(job, dataset_count)


def get_job(job_id: str) -> None:
    """
    Gets a Batch Job by ID.

    :param job_id: The ID of the Batch Job to get.
    """
    sdk_project = get_default_datature_client()

    if not job_id:
        job_id = batch_functions.select_entry("jobs")

    try:
        job = sdk_project.batch.jobs.get(job_id)
    except error.Error as exc:
        print(f"{Fore.CYAN}●{Fore.RESET} Error getting Job: {exc.message}")
        sys.exit(1)

    try:
        dataset_count = sdk_project.batch.datasets.get(
            job.spec.dataset_id
        ).status.item_count
    except error.Error as exc:
        print(f"{Fore.CYAN}●{Fore.RESET} Error getting Dataset count: {exc.message}")
        sys.exit(1)

    batch_functions.print_job_object(job, dataset_count)


def list_jobs() -> None:
    """
    Lists all Batch Jobs.
    """
    sdk_project = get_default_datature_client()

    try:
        jobs_response = sdk_project.batch.jobs.list()
        jobs_response.data.reverse()
    except error.Error as exc:
        print(f"{Fore.CYAN}●{Fore.RESET} Error listing Jobs: {exc.message}")
        sys.exit(1)

    if len(jobs_response.data) == 0:
        print(f"{Fore.CYAN}●{Fore.RESET} No Jobs found.")
        return

    print()  # for new line
    print(f"{'ID':<45} {'NAME':<20} {'STATUS':<20}")
    for job in jobs_response.data:
        name_padding = max(0, 20 - (wcswidth(job.name) - len(job.name)))
        print(
            f"{job.id:<45} {utils.truncate_text(job.name, 20):<{name_padding}} "
            f"{job.status.overview:<20}"
        )
    print()  # for new line


def cancel_job(job_id: str) -> None:
    """
    Cancels a Batch Job by ID.

    :param job_id: The ID of the Batch Job to cancel.
    """
    sdk_project = get_default_datature_client()

    if not job_id:
        job_id = batch_functions.select_entry("jobs")

    try:
        sdk_project.batch.jobs.cancel(job_id)
    except error.Error as exc:
        print(f"{Fore.CYAN}●{Fore.RESET} Error cancelling Job: {exc.message}")
        sys.exit(1)
    print(f"{Fore.GREEN}✓{Fore.RESET} Job cancelled successfully.")


def delete_job(job_id: str) -> None:
    """
    Deletes a Batch Job by ID.

    :param job_id: The ID of the Batch Job to delete.
    """
    sdk_project = get_default_datature_client()

    if not job_id:
        job_id = batch_functions.select_entry("jobs")

    try:
        sdk_project.batch.jobs.delete(job_id)
    except error.Error as exc:
        print(f"{Fore.CYAN}●{Fore.RESET} Error deleting Job: {exc.message}")
        sys.exit(1)
    print(f"{Fore.GREEN}✓{Fore.RESET} Job deleted successfully.")


def get_job_logs(
    job_id: str,
    max_entries: int,
    since: int,
    until: int,
    level: str,
    output_path: str,
) -> None:
    """
    Gets the logs for a Batch Job by ID.

    :param job_id: The ID of the Batch Job to get logs for.
    :param max_entries: The maximum number of log entries to return.
    :param since: The timestamp in milliseconds to filter logs after.
    :param until: The timestamp in milliseconds to filter logs before.
    :param level: The minimum log level to return.
    :param output_path: The path to save the logs to.
    """
    sdk_project = get_default_datature_client()

    if not job_id:
        job_id = batch_functions.select_entry("jobs")

    try:
        logs_filter = {
            "max_entries": max_entries if max_entries > 0 else None,
            "before_time": until if until >= 0 else None,
            "after_time": since if since >= 0 else None,
            "min_level": level,
        }

        if output_path:
            job = sdk_project.batch.jobs.get(job_id)

            output_path = Path(output_path).expanduser().resolve()
            if not output_path.parent.exists():
                output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as output_file:
                output_file.write(f"{'JOB ID:':<15} {job_id}\n")
                output_file.write(f"{'JOB NAME:':<15} {job.name}\n")
                output_file.write(f"{'PROJECT ID:':<15} {job.project_id}\n")
                output_file.write(
                    f"{'START TIME:':<15} "
                    f"{utils.utc_timestamp_ms_to_iso8601(job.spec.start_at_time)}\n"
                )
                output_file.write(
                    f"{'CUTOFF TIME:':<15} "
                    f"{utils.utc_timestamp_ms_to_iso8601(job.spec.stop_at_time)}\n"
                )

                output_file.write(f"{'-' * 65}\n")
                output_file.write(
                    f"{'ID':<25} {'KIND':<15} {'TIME':<30} {'LEVEL':<6} {'ITEM':<35} "
                    f"{'STATUS':<15} {'DURATION (ms)':<15} {'MESSAGE':<20}\n"
                )
                for entry in sdk_project.batch.jobs.get_all_log_entries(
                    job_id, logs_filter
                ):
                    output_file.write(
                        f"{entry.id:<25} {entry.kind:<15} "
                        f"{utils.utc_timestamp_ms_to_iso8601(entry.create_time):<30}"
                        f" {entry.level.upper():<6} {entry.item:<35} {entry.status:<15} "
                        f"{int(entry.time_ms):<15} {entry.reason:<20}\n"
                    )
            print(f"{Fore.GREEN}✓{Fore.RESET} Job logs saved to {output_path}")

        else:
            job_logs = sdk_project.batch.jobs.get_logs(job_id, logs_filter)

            if len(job_logs.entries) == 0:
                print(f"{Fore.CYAN}●{Fore.RESET} No Job logs found.")
                sys.exit(0)

            print(
                f"\n{'TIME':<30} {'LEVEL':<6} {'ITEM':<35} "
                f"{'STATUS':<15} {'DURATION (ms)':<15} {'MESSAGE':<20}"
            )
            for entry in job_logs.entries:
                print(
                    f"{utils.utc_timestamp_ms_to_iso8601(entry.create_time):<30}"
                    f" {entry.level.upper():<6} {entry.item:<35} "
                    f"{entry.status:<15} {int(entry.time_ms):<15} {entry.reason:<20}"
                )

    except (FileNotFoundError, PermissionError) as exc:
        print(f"{Fore.CYAN}●{Fore.RESET} Error saving Job logs: {exc}")
    except error.Error as exc:
        print(f"{Fore.CYAN}●{Fore.RESET} Error getting Job logs: {exc.message}")
        sys.exit(1)


def wait_until_done(job_id: str) -> None:
    """
    Waits until a Batch Job is done, shows a progress bar.

    :param job_id: The ID of the Batch Job to wait for.
    """
    sdk_project = get_default_datature_client()

    if not job_id:
        job_id = batch_functions.select_entry("jobs")

    try:
        job = sdk_project.batch.jobs.wait_until_done(job_id)
    except error.Error as exc:
        print(f"{Fore.CYAN}●{Fore.RESET} Error waiting for Job: {exc.message}")
        sys.exit(1)

    print()  # for new line
    print(f"{Fore.GREEN}✓{Fore.RESET} Job completed successfully.")

    try:
        dataset_count = sdk_project.batch.datasets.get(
            job.spec.dataset_id
        ).status.item_count
    except error.Error as exc:
        print(f"{Fore.CYAN}●{Fore.RESET} Error getting Dataset count: {exc.message}")
        sys.exit(1)

    batch_functions.print_job_object(job, dataset_count)
