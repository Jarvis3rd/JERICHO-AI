#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   functions.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Datature CLI Batch Functions.
"""

import logging
import os
import sys
from datetime import datetime

from colorama import Fore
from InquirerPy import inquirer
from InquirerPy.base.control import Choice

from datature.nexus import error
from datature.nexus.api.batch import models
from datature.nexus.cli import consts
from datature.nexus.cli.functions import get_default_datature_client
from datature.nexus.utils import utils

logging.basicConfig(level=logging.CRITICAL)


def select_entry(entity: str) -> str:
    """
    Selects an entry from the list of entities.

    :param entity: The entity to select from.
    :return: The selected entry ID.
    """
    sdk_project = get_default_datature_client()
    batch_entity = getattr(sdk_project.batch, entity)

    try:
        response = batch_entity.list()
        response.data.reverse()
    except error.Error as exc:
        print(f"{Fore.CYAN}●{Fore.RESET} Error listing {entity}: {exc.message}")
        sys.exit(1)

    if len(response.data) == 0:
        print(f"{Fore.CYAN}●{Fore.RESET} No {entity} found.")
        sys.exit(0)

    if entity == "datasets":
        choices = [
            Choice(
                name=(
                    f"{item.name}  [Expires in "
                    + utils.timedelta_to_str(
                        datetime.fromtimestamp(int(item.expiry_time / 1000))
                        - datetime.now()
                    )
                    + "]"
                ),
                value=item.id,
            )
            for item in response.data
        ]
    else:
        choices = [Choice(name=item.name, value=item.id) for item in response.data]

    return inquirer.fuzzy(
        message="Which entry do you want to select?",
        choices=choices,
        max_height=consts.INQUIRER_CHOICES_MAX_VISIBLE_ENTRIES,
        border=True,
    ).execute()


def clear_terminal_screen():
    """Clear the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def clear_last_lines(num_lines=1):
    """Clear the last n lines of the terminal."""
    for _ in range(num_lines):
        # Move the cursor up one line
        sys.stdout.write("\033[F")
        # Clear the entire line
        sys.stdout.write("\033[K")


def handle_paged_navigation(response, pagination) -> bool:
    """Handle paged navigation for a paginated response."""
    page_choices = (
        [
            (Choice(name="Next Page", value="next") if response.next_page else None),
            (
                Choice(name="Previous Page", value="prev")
                if response.prev_page
                else None
            ),
            Choice(name="Exit", value="exit"),
        ]
        if response.next_page or response.prev_page
        else []
    )
    page_choices = [choice for choice in page_choices if choice]

    if not page_choices:
        return False

    selection = inquirer.select(
        message="Select an action:", choices=page_choices, border=True
    ).execute()

    if selection == "next":
        pagination["page"] = response.next_page
    elif selection == "prev":
        pagination["page"] = response.prev_page
    elif selection == "exit":
        return False

    clear_last_lines(len(response.data) + 3)
    return True


def print_webhook_object(webhook: models.WebhookModel, header_width: int = 20):
    """
    Print the webhook object.

    :param webhook: The webhook object.
    :param header_width: The width of the header.
    """
    print()  # for new line
    print(f"{'ID:':<{header_width}} {webhook.id}")
    print(
        f"{'Name:':<{header_width}} {utils.truncate_text(webhook.name, max_length=70)}"
    )
    print(f"{'Endpoint:':<{header_width}} {webhook.endpoint}")
    print(f"{'Max Retries:':<{header_width}} {webhook.retries.max_retries}")
    print(
        f"{'Max Retry Delay:':<{header_width}} {round(webhook.retries.max_retry_delay / 1000, 2)}s"
    )
    print()  # for new line


def print_dataset_object(dataset: models.Dataset, header_width: int = 15):
    """
    Print the dataset object.

    :param dataset: The dataset object.
    :param header_width: The width of the header.
    """
    print()  # for new line
    print(f"{'ID:':<{header_width}} {dataset.id}")
    print(
        f"{'Name:':<{header_width}} {utils.truncate_text(dataset.name, max_length=70)}"
    )
    print(f"{'Source:':<{header_width}} {dataset.status.source.kind}")
    print(
        f"{'Expires At:':<{header_width}} "
        f"{datetime.fromtimestamp(int(dataset.expiry_time / 1000))}"
    )
    print()  # for new line
    print(f"{'Status:':<{header_width}} {dataset.status.overview}")
    print(f"{'Message:':<{header_width}} {dataset.status.message}")
    print(f"{'Item Count:':<{header_width}} {dataset.status.item_count}")
    print(
        f"{'Last Updated:':<{header_width}} "
        f"{datetime.fromtimestamp(int(dataset.status.update_time / 1000))}"
    )
    print()  # for new line


def print_job_object(job: models.Job, dataset_count: int, header_width: int = 25):
    """
    Print the job object.

    :param job: The job object.
    :param dataset_count: The total number of items in the dataset.
    :param header_width: The width of the header.
    """
    print()  # for new line
    print(f"{'ID:':<{header_width}} {job.id}")
    print(f"{'Name:':<{header_width}} {utils.truncate_text(job.name, max_length=70)}")
    print(
        f"{'Start Time:':<{header_width}} "
        f"{datetime.fromtimestamp(int(job.spec.start_at_time / 1000))}"
    )
    print(
        f"{'Cutoff Time:':<{header_width}} "
        f"{datetime.fromtimestamp(int(job.spec.stop_at_time / 1000))}"
    )
    print(f"{'Dataset ID:':<{header_width}} {job.spec.dataset_id}")
    print()  # for new line
    print("Endpoint:")
    print(
        f"{'  - Webhook:':<{header_width}} {job.spec.result_delivery.destinations[0].webhook_id}"
    )
    print()  # for new line
    print(f"{'Status:':<{header_width}} {job.status.overview}")
    print(f"{'Message:':<{header_width}} {job.status.message}")
    print(f"{'Reason:':<{header_width}} {job.status.reason}")

    print()  # for new line
    print(f"{'Items Processed':<{header_width}} {'Count':<10} {'Description'}")

    print(
        f"{'  - Total:':<{header_width}} {dataset_count:<10} "
        f"{'Total item count in the Dataset.':<40}"
    )
    print(
        f"{'  - Gathered:':<{header_width}} {job.status.items.gathered:<10} "
        f"{job.status.items.get_description('gathered')}"
    )
    print(
        f"{'  - FailedGather:':<{header_width}} {job.status.items.failed_gather:<10} "
        f"{job.status.items.get_description('failed_gather')}"
    )
    print(
        f"{'  - Preprocessed:':<{header_width}} {job.status.items.preprocessed:<10} "
        f"{job.status.items.get_description('preprocessed')}"
    )
    print(
        f"{'  - FailedPreprocess:':<{header_width}} {job.status.items.failed_preprocess:<10} "
        f"{job.status.items.get_description('failed_preprocess')}"
    )
    print(
        f"{'  - Predicted:':<{header_width}} {job.status.items.predicted:<10} "
        f"{job.status.items.get_description('predicted')}"
    )
    print(
        f"{'  - FailedPredict:':<{header_width}} {job.status.items.failed_predict:<10} "
        f"{job.status.items.get_description('failed_predict')}"
    )
    print(
        f"{'  - Delivered:':<{header_width}} {job.status.items.delivered:<10} "
        f"{job.status.items.get_description('delivered')}"
    )
    print(
        f"{'  - FailedDeliver:':<{header_width}} {job.status.items.failed_deliver:<10} "
        f"{job.status.items.get_description('failed_deliver')}"
    )
    print()  # for new line
