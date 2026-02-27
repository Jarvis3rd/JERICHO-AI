#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   webhook.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   CLI Webhook Functions.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

from colorama import Fore
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.validator import EmptyInputValidator
from wcwidth import wcswidth

import datature.nexus.cli.batch.functions as batch_functions
from datature.nexus import error
from datature.nexus.cli.functions import get_default_datature_client
from datature.nexus.utils import utils

logging.basicConfig(level=logging.CRITICAL)


def create_webhook_secret(prompt_for_save: bool = True) -> str:
    """
    Creates a Webhook secret key and either prints it to the console or saves it to a file.

    :param: prompt_for_save: Whether to prompt the user to save the secret key to a file.
    :return: The generated Webhook secret key.
    """
    webhook_secret = utils.generate_webhook_secret()

    if prompt_for_save:
        webhook_secret_filepath = (
            inquirer.filepath(
                "Enter the path to the file where the generated Webhook secret key will be saved:",
                mandatory=False,
                long_instruction="Leave blank to print to console",
            )
            .execute()
            .strip()
        )

        if webhook_secret_filepath:
            try:
                webhook_secret_filepath = (
                    Path(webhook_secret_filepath).expanduser().resolve()
                )
                if not webhook_secret_filepath.parent.exists():
                    webhook_secret_filepath.parent.mkdir(parents=True, exist_ok=True)
                webhook_secret_filepath.write_text(webhook_secret, encoding="utf-8")
            except (FileNotFoundError, PermissionError) as exc:
                print(
                    f"{Fore.CYAN}●{Fore.RESET} Error creating and writing to file: {exc}. "
                    "Please ensure that the file path is correct and that "
                    "you have the necessary write permissions."
                )
                sys.exit(1)

    print(f"{Fore.GREEN}✓{Fore.RESET} Webhook secret key generated successfully:")
    print(f"\n  {webhook_secret}\n")
    return webhook_secret


def handle_webhook_secret() -> str:
    """
    Handles the generation of a Webhook secret key.

    :return: The Webhook secret key.
    """
    webhook_secret_generation_method = inquirer.select(
        message="Select how you would like Datature to sign Webhook requests:",
        choices=[
            Choice(name="Generate a new Webhook secret key", value="new"),
            Choice(
                name="Load an existing Webhook secret key from a file", value="file"
            ),
            Choice(name="Enter an existing Webhook secret key", value="input"),
        ],
        border=True,
    ).execute()

    if webhook_secret_generation_method == "new":
        webhook_secret = create_webhook_secret()
    elif webhook_secret_generation_method == "file":
        webhook_secret_filepath = (
            inquirer.filepath(
                "Enter the path to the file containing the secret key:",
                validate=utils.PathAndEmptyInputValidator(),
            )
            .execute()
            .strip()
        )

        try:
            webhook_secret = (
                Path(webhook_secret_filepath)
                .expanduser()
                .resolve()
                .read_text(encoding="utf-8")
                .strip()
            )
        except (FileNotFoundError, PermissionError) as exc:
            print(
                f"{Fore.CYAN}●{Fore.RESET} Error reading file: {exc}. "
                "Please ensure the path is correct and you have the necessary read permissions."
            )
            sys.exit(1)
    else:
        webhook_secret = (
            inquirer.secret("Enter the secret key:", validate=EmptyInputValidator())
            .execute()
            .strip()
        )
    return webhook_secret


def create_webhook(webhook_type: str = "custom") -> str:
    """
    Creates a new Webhook.

    :param webhook_type: The type of the Webhook to create.
    :return: The ID of the created Webhook.
    """
    sdk_project = get_default_datature_client()

    webhook_name = (
        (
            inquirer.text(
                "Enter a name for the Webhook:",
                validate=utils.NameAndEmptyInputValidator(),
            )
            .execute()
            .strip()
        )
        if webhook_type == "custom"
        else f"webhook-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"
    )

    webhook_endpoint = (
        inquirer.text("Enter the Webhook endpoint:", validate=EmptyInputValidator())
        .execute()
        .strip()
    )

    max_retries = (
        int(
            inquirer.number(
                "Enter the maximum number of retries per request [0-5]:",
                default=3,
                min_allowed=0,
                max_allowed=5,
            ).execute()
        )
        if webhook_type == "custom"
        else 3
    )

    max_delay = (
        int(
            inquirer.number(
                "Enter the maximum delay between retries in seconds [0-60]:",
                default=15,
                min_allowed=0,
                max_allowed=60,
            ).execute()
        )
        * 1000
        if webhook_type == "custom"
        else 15000
    )

    webhook_secret = (
        handle_webhook_secret()
        if webhook_type == "custom"
        else create_webhook_secret(prompt_for_save=False)
    )

    try:
        webhook = sdk_project.batch.webhooks.create(
            name=webhook_name,
            webhook_spec={
                "endpoint": webhook_endpoint,
                "secret": {"contents": webhook_secret},
                "retries": {
                    "max_retries": int(max_retries),
                    "max_retry_delay": int(max_delay),
                },
            },
        )
    except error.Error as exc:
        print(f"{Fore.CYAN}●{Fore.RESET} Error creating Webhook: {exc.message}")
        sys.exit(1)

    print(
        f"{Fore.GREEN}✓{Fore.RESET} Webhook created successfully. "
        f"Run 'datature batch webhooks test {webhook.id}' to test the Webhook."
    )

    batch_functions.print_webhook_object(webhook)
    return webhook.id


def get_webhook(webhook_id: str) -> None:
    """
    Gets a Webhook by ID.

    :param webhook_id: The ID of the Webhook to get.
    """
    sdk_project = get_default_datature_client()

    if not webhook_id:
        webhook_id = batch_functions.select_entry("webhooks")

    try:
        webhook = sdk_project.batch.webhooks.get(webhook_id)
    except error.Error as exc:
        print(f"{Fore.CYAN}●{Fore.RESET} Error getting Webhook: {exc.message}")
        sys.exit(1)

    batch_functions.print_webhook_object(webhook)


def list_webhooks() -> None:
    """
    Lists all Webhooks.
    """
    sdk_project = get_default_datature_client()

    try:
        webhooks_response = sdk_project.batch.webhooks.list()
        webhooks_response.data.reverse()
    except error.Error as exc:
        print(f"{Fore.CYAN}●{Fore.RESET} Error listing Webhooks: {exc.message}")
        sys.exit(1)

    if len(webhooks_response.data) == 0:
        print(f"{Fore.CYAN}●{Fore.RESET} No Webhooks found.")
        return

    print()  # for new line
    print(f"{'ID':<45} {'NAME':<20} {'ENDPOINT':<20}")
    for webhook in webhooks_response.data:
        name_padding = max(0, 20 - (wcswidth(webhook.name) - len(webhook.name)))
        endpoint_padding = max(
            0, 20 - (wcswidth(webhook.endpoint) - len(webhook.endpoint))
        )
        print(
            f"{webhook.id:<45} {utils.truncate_text(webhook.name, 20):<{name_padding}} "
            f"{utils.truncate_text(webhook.endpoint, 20):<{endpoint_padding}}"
        )
    print()  # for new line


def delete_webhook(webhook_id: str) -> None:
    """
    Deletes a Webhook by ID.

    :param webhook_id: The ID of the Webhook to delete.
    """
    sdk_project = get_default_datature_client()

    if not webhook_id:
        webhook_id = batch_functions.select_entry("webhooks")

    try:
        sdk_project.batch.webhooks.delete(webhook_id)
    except error.Error as exc:
        print(f"{Fore.CYAN}●{Fore.RESET} Error deleting Webhook: {exc.message}")
        sys.exit(1)
    print(f"{Fore.GREEN}✓{Fore.RESET} Webhook deleted successfully.")


def update_webhook(webhook_id: str) -> None:
    """
    Updates a Webhook by ID.

    :param webhook_id: The ID of the Webhook to update.
    """
    sdk_project = get_default_datature_client()

    if not webhook_id:
        webhook_id = batch_functions.select_entry("webhooks")

    try:
        webhook = sdk_project.batch.webhooks.get(webhook_id)
    except error.Error as exc:
        print(f"{Fore.CYAN}●{Fore.RESET} Error getting Webhook: {exc.message}")
        sys.exit(1)

    webhook_endpoint = (
        inquirer.text(
            "Enter the new Webhook endpoint:",
            long_instruction=f"Leave blank to keep current: {webhook.endpoint}",
        )
        .execute()
        .strip()
    ) or webhook.endpoint

    max_retries = (
        inquirer.number(
            "Enter the maximum number of retries per request [0-5]:",
            long_instruction=f"Leave blank to keep current: {webhook.retries.max_retries}",
            default=None,
            min_allowed=0,
            max_allowed=5,
        ).execute()
        or webhook.retries.max_retries
    )

    max_delay = (
        inquirer.number(
            "Enter the maximum delay between retries in seconds [0-60]:",
            long_instruction=f"Leave blank to keep current: {int(webhook.retries.max_retry_delay / 1000)}",
            default=None,
            min_allowed=0,
            max_allowed=60,
        ).execute()
        or webhook.retries.max_retry_delay
    )

    try:
        updated_webhook = sdk_project.batch.webhooks.update(
            webhook_id=webhook_id,
            webhook_spec={
                "endpoint": webhook_endpoint,
                "retries": {
                    "max_retries": int(max_retries),
                    "max_retry_delay": int(max_delay),
                },
            },
        )
    except error.Error as exc:
        print(f"{Fore.CYAN}●{Fore.RESET} Error updating Webhook: {exc.message}")
        sys.exit(1)

    print()  # for new line
    print(f"{Fore.GREEN}✓{Fore.RESET} Webhook updated successfully.")

    batch_functions.print_webhook_object(updated_webhook)


def update_webhook_secret(webhook_id: str) -> None:
    """
    Updates the secret key of a Webhook by ID.

    :param webhook_id: The ID of the Webhook to update.
    """
    sdk_project = get_default_datature_client()

    if not webhook_id:
        webhook_id = batch_functions.select_entry("webhooks")

    try:
        sdk_project.batch.webhooks.get(webhook_id)
    except error.Error as exc:
        print(f"{Fore.CYAN}●{Fore.RESET} Error getting Webhook: {exc.message}")
        sys.exit(1)

    webhook_secret = handle_webhook_secret()
    try:
        sdk_project.batch.webhooks.update_secret(
            webhook_id=webhook_id, secret=webhook_secret
        )
    except error.Error as exc:
        print(
            f"{Fore.CYAN}●{Fore.RESET} Error updating Webhook secret key: {exc.message}"
        )
        sys.exit(1)

    print(f"{Fore.GREEN}✓{Fore.RESET} Webhook secret key updated successfully.")


def test_webhook(webhook_id: str) -> None:
    """
    Tests a Webhook by ID by sending a sample payload and checking the response.

    :param webhook_id: The ID of the Webhook to ping.
    """
    sdk_project = get_default_datature_client()

    if not webhook_id:
        webhook_id = batch_functions.select_entry("webhooks")

    try:
        webhook_response = sdk_project.batch.webhooks.test(webhook_id)
    except error.Error as exc:
        print(f"{Fore.CYAN}●{Fore.RESET} Error testing Webhook: {exc.message}")
        sys.exit(1)

    header_width = 15
    print()  # for new line
    print("=== Webhook Test Response ===")
    print(f"{'Status:':<{header_width}} {webhook_response.status}")
    print(f"{'Response Code:':<{header_width}} {webhook_response.response_code}")
    print(f"{'Latency (ms):':<{header_width}} {webhook_response.latency_ms}")
    print(f"{'Attempt Count':<{header_width}} {webhook_response.attempt_count}")
    print(f"{'Response Body:':<{header_width}} {webhook_response.body}")
    print(f"{'Reason:':<{header_width}} {webhook_response.reason}")
    print()  # for new line
