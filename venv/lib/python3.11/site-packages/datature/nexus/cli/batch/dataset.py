#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   dataset.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   CLI Dataset Functions.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

from colorama import Fore
from InquirerPy import inquirer
from wcwidth import wcswidth

import datature.nexus.cli.batch.functions as batch_functions
from datature.nexus import error
from datature.nexus.cli.functions import get_default_datature_client
from datature.nexus.utils import utils

logging.basicConfig(level=logging.CRITICAL)


def create_dataset(dataset_type: str = "custom") -> str:
    """
    Creates a new Dataset.

    :param dataset_type: The type of the Dataset to create.
    :return: The ID of the created Dataset.
    """
    sdk_project = get_default_datature_client()

    dataset_name = (
        (
            inquirer.text(
                "Enter a name for the Dataset:",
                validate=utils.NameAndEmptyInputValidator(),
            )
            .execute()
            .strip()
        )
        if dataset_type == "custom"
        else f"dataset-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"
    )

    dataset_path = (
        inquirer.filepath(
            "Enter the path to the Dataset file:",
            validate=utils.PathAndEmptyInputValidator(),
        )
        .execute()
        .strip()
    )

    try:
        dataset = sdk_project.batch.datasets.create(
            name=dataset_name,
            dataset_path=str(Path(dataset_path).expanduser().resolve()),
        )

        print()  # for new line
        print(f"{Fore.GREEN}✓{Fore.RESET} Dataset created successfully")

        updated_dataset = sdk_project.batch.datasets.wait_until_done(dataset.id)
    except error.Error as exc:
        print(f"{Fore.CYAN}●{Fore.RESET} Error creating Dataset: {exc.message}")
        sys.exit(1)

    print(f"{Fore.GREEN}✓{Fore.RESET} Dataset uploaded and processed successfully.")

    batch_functions.print_dataset_object(updated_dataset)
    return dataset.id


def get_dataset(dataset_id: str) -> None:
    """
    Gets a Dataset by ID.

    :param dataset_id: The ID of the Dataset to get.
    """
    sdk_project = get_default_datature_client()

    if not dataset_id:
        dataset_id = batch_functions.select_entry("datasets")

    try:
        dataset = sdk_project.batch.datasets.get(dataset_id)
    except error.Error as exc:
        print(f"{Fore.CYAN}●{Fore.RESET} Error getting Dataset: {exc.message}")
        sys.exit(1)

    batch_functions.print_dataset_object(dataset)


def list_datasets() -> None:
    """
    Lists all Datasets.
    """
    sdk_project = get_default_datature_client()

    try:
        datasets_response = sdk_project.batch.datasets.list()
        datasets_response.data.reverse()
    except error.Error as exc:
        print(f"{Fore.CYAN}●{Fore.RESET} Error listing Webhooks: {exc.message}")
        sys.exit(1)

    if len(datasets_response.data) == 0:
        print(f"{Fore.CYAN}●{Fore.RESET} No Datasets found.")
        return

    print()  # for new line
    print(f"{'ID':<45} {'NAME':<20} {'STATUS':<20}")
    for dataset in datasets_response.data:
        name_padding = max(0, 20 - (wcswidth(dataset.name) - len(dataset.name)))
        print(
            f"{dataset.id:<45} {utils.truncate_text(dataset.name, 20):<{name_padding}} "
            f"{dataset.status.overview:<20}"
        )
    print()  # for new line


def delete_dataset(dataset_id: str) -> None:
    """
    Deletes a Dataset by ID.

    :param dataset_id: The ID of the Dataset to delete.
    """
    sdk_project = get_default_datature_client()

    if not dataset_id:
        dataset_id = batch_functions.select_entry("datasets")

    try:
        sdk_project.batch.datasets.delete(dataset_id)
    except error.Error as exc:
        print(f"{Fore.CYAN}●{Fore.RESET} Error deleting Dataset: {exc.message}")
        sys.exit(1)
    print(f"{Fore.GREEN}✓{Fore.RESET} Dataset deleted successfully.")
