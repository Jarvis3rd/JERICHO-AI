#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   functions.py
@Author  :   Wei Loon Cheng, Kai Xuan Lee
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Custom runner user functions.
"""

# pylint: disable=W0718,E1120

import logging
import sys
from typing import List

from InquirerPy import inquirer

from datature import nexus
from datature.nexus import error
from datature.nexus.cli import messages
from datature.nexus.cli.config import Config
from datature.nexus.cli.runner import CustomRunner
from datature.nexus.cli.runner.common import log_errors
from datature.nexus.cli.runner.config import RunnerConfig
from datature.nexus.cli.runner.consts import RUNNER_INIT_ROOT_DIR
from datature.nexus.cli.runner.utils import (
    check_system_specs,
    configure_microk8s,
    format_runner_list,
    ping_server,
)


def prompt_runner_details(
    runner_config: RunnerConfig, max_retry_count: int = 3
) -> None:
    """Prompt user for runner details if not provided.

    :param runner_config (RunnerConfig): Runner configuration.
    :param max_retry_count (int): Maximum number of retries.
    """

    existing_runner_names = [
        runner_config.name for runner_config in RunnerConfig.read_all_from_file()
    ]
    name_retry_count = 0
    while not runner_config.name:
        runner_config.name = (
            inquirer.text(messages.RUNNER_NAME_MESSAGE).execute().strip()
        )

        if runner_config.name == "":
            print(messages.EMPTY_RUNNER_NAME_MESSAGE)
        elif runner_config.name in existing_runner_names:
            print(messages.DUPLICATE_RUNNER_NAME_MESSAGE)
            runner_config.name = ""

        name_retry_count += 1
        if name_retry_count >= max_retry_count:
            print(messages.MAX_RETRY_MESSAGE)
            sys.exit(1)

    secret_key_retry_count = 0
    while not runner_config.secret_key:
        runner_config.secret_key = (
            inquirer.secret(messages.SECRET_KEY_MESSAGE).execute().strip().lower()
        )

        if runner_config.secret_key == "":
            print(messages.EMPTY_SECRET_KEY_MESSAGE)
        elif len(runner_config.secret_key) != 64:
            print(messages.INVALID_SECRET_KEY_LENGTH_MESSAGE)
            runner_config.secret_key = ""

        secret_key_retry_count += 1
        if secret_key_retry_count >= max_retry_count:
            print(messages.MAX_RETRY_MESSAGE)
            sys.exit(1)

    workspace_id_retry_count = 0
    while not runner_config.workspace_id:
        runner_config.workspace_id = (
            inquirer.text(messages.WORKSPACE_ID_MESSAGE).execute().strip().lower()
        )

        if runner_config.workspace_id == "":
            print(messages.EMPTY_WORKSPACE_ID_MESSAGE)
        elif len(runner_config.workspace_id) != 32:
            print(messages.INVALID_WORKSPACE_ID_LENGTH_MESSAGE)
            runner_config.workspace_id = ""

        workspace_id_retry_count += 1
        if workspace_id_retry_count >= max_retry_count:
            print(messages.MAX_RETRY_MESSAGE)
            sys.exit(1)


def select_runners(action: str, allow_all: bool = True) -> List[str]:
    """
    Select runner(s) from saved configuration file.

    :param action (str): Action to perform.
    :param allow_all (bool): Allow selecting all runners.
    :return: List of selected runner names.
    """
    runner_configs = RunnerConfig.read_all_from_file()
    if len(runner_configs) == 0:
        sys.exit(1)

    if action == "suspend":
        runner_names = [
            runner_config.name
            for runner_config in runner_configs
            if not runner_config.status.suspended
        ]
    elif action == "resume":
        runner_names = [
            runner_config.name
            for runner_config in runner_configs
            if runner_config.status.suspended
        ]
    elif action == "reauth":
        runner_names = [
            runner_config.name
            for runner_config in runner_configs
            if not runner_config.status.valid_secret_key
        ]
    else:
        runner_names = [runner_config.name for runner_config in runner_configs]
    if allow_all and len(runner_names) > 1:
        runner_names.append("\u200eAll Runners")

    if not runner_names:
        print(messages.NO_ACTIONABLE_RUNNERS_MESSAGE.format(action))
        sys.exit(1)

    runner_name = inquirer.select(
        f"Which runner do you want to {action}?", choices=runner_names, border=True
    ).execute()

    if runner_name == "\u200eAll Runners":
        return runner_names
    return [runner_name]


def install_runner() -> None:
    """
    Install the custom runner.

    :return: None
    """

    RUNNER_INIT_ROOT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        runner_config = RunnerConfig()

        logging.basicConfig(level=logging.CRITICAL)
        cli_config = Config()
        runner_config.secret_key = cli_config.get_default_project().get(
            "project_secret", ""
        )
        runner_config.workspace_id = (
            nexus.Client(runner_config.secret_key).get_info().id.replace("ws_", "")
        )
        ping_server(runner_config)
        logging.basicConfig(level=logging.INFO)
    except error.Error as exc:
        if "Workspace ID / Secret Key combination" in exc.message:
            runner_config.secret_key = ""
            runner_config.workspace_id = ""
        elif "No access rights" in exc.message:
            print(messages.AUTHENTICATION_FAILED_MESSAGE)
            sys.exit(1)
        else:
            print(exc)
            sys.exit(1)

    try:
        check_system_specs(runner_config)
        configure_microk8s()

        install_continue = inquirer.confirm(
            messages.RUNNER_INSTALL_SIZE_MESSAGE, default=True
        ).execute()
        if not install_continue:
            return

        prompt_runner_details(runner_config)
        ping_server(runner_config)
        runner_config.write_to_file()
    except KeyboardInterrupt:
        sys.exit(1)
    except error.Error as exc:
        print(exc)
        sys.exit(1)
    except Exception:
        log_errors(unknown=True)
        sys.exit(1)

    name_or_hash = runner_config.id[-6:] if runner_config.id else runner_config.name
    CustomRunner(runner_name_or_hash=name_or_hash).install()


def uninstall_runner(name_or_hash: str) -> None:
    """
    Uninstall the custom runner.

    :param name_or_hash (str): Runner name or hash.
    :return: None
    """
    try:
        if not name_or_hash:
            runner_configs = RunnerConfig.read_all_from_file()
            if len(runner_configs) == 0:
                print(messages.NO_RUNNERS_MESSAGE)
                sys.exit(1)

            runner_names = select_runners("uninstall")

            continue_uninstall = inquirer.confirm(
                messages.UNINSTALL_RUNNERS_CONFIRMATION_MESSAGE, default=True
            ).execute()

            for runner_config in runner_configs:
                if runner_config.name not in runner_names:
                    continue

                runner = CustomRunner(runner_name_or_hash=runner_config.id[-6:])
                # Prompt for confirmation if there are still ongoing runs
                continue_uninstall_with_ongoing_runs = False
                if runner.get_ongoing_runs:
                    continue_uninstall_with_ongoing_runs = inquirer.confirm(
                        messages.KILL_RUNS_CONFIRMATION_MESSAGE.format(
                            runner_config.name, runner_config.id[-6:]
                        ),
                        default=True,
                    ).execute()

                if not continue_uninstall and not continue_uninstall_with_ongoing_runs:
                    continue
                runner.uninstall()
        else:
            runner = CustomRunner(runner_name_or_hash=name_or_hash)

            # Prompt for confirmation if there are still ongoing runs
            continue_uninstall = inquirer.confirm(
                messages.UNINSTALL_RUNNERS_CONFIRMATION_MESSAGE, default=True
            ).execute()

            continue_uninstall_with_ongoing_runs = False
            if runner.get_ongoing_runs:
                continue_uninstall_with_ongoing_runs = inquirer.confirm(
                    messages.KILL_RUNS_CONFIRMATION_MESSAGE, default=True
                ).execute()

            if not continue_uninstall and not continue_uninstall_with_ongoing_runs:
                return
            runner.uninstall()
    except KeyboardInterrupt:
        sys.exit(1)
    except (error.Error, Exception):
        log_errors()
        sys.exit(1)


def suspend_runner(name_or_hash: str) -> None:
    """
    Suspend the custom runner.

    :param name_or_hash (str): Runner name or hash.
    :return: None
    """

    try:
        if not name_or_hash:
            runner_configs = RunnerConfig.read_all_from_file()
            if len(runner_configs) == 0:
                print(messages.NO_RUNNERS_MESSAGE)
                sys.exit(1)

            runner_names = select_runners("suspend")
            for runner_config in runner_configs:
                if runner_config.name in runner_names:
                    CustomRunner(runner_name_or_hash=runner_config.id[-6:]).suspend()
        else:
            CustomRunner(runner_name_or_hash=name_or_hash).suspend()
    except KeyboardInterrupt:
        sys.exit(1)
    except (error.Error, Exception):
        log_errors()
        sys.exit(1)


def resume_runner(name_or_hash: str) -> None:
    """
    Suspend the custom runner.

    :param name_or_hash (str): Runner name or hash.
    :return: None
    """

    try:
        if not name_or_hash:
            runner_configs = RunnerConfig.read_all_from_file()
            if len(runner_configs) == 0:
                print(messages.NO_RUNNERS_MESSAGE)
                sys.exit(1)

            runner_names = select_runners("resume")
            for runner_config in runner_configs:
                if runner_config.name in runner_names:
                    CustomRunner(runner_name_or_hash=runner_config.id[-6:]).resume()
        else:
            CustomRunner(runner_name_or_hash=name_or_hash).resume()
    except KeyboardInterrupt:
        sys.exit(1)
    except (error.Error, Exception):
        log_errors()
        sys.exit(1)


def restart_runner(name_or_hash: str) -> None:
    """
    Restart the custom runner.

    :param name_or_hash (str): Runner name or hash.
    :return: None
    """

    try:
        if not name_or_hash:
            runner_configs = RunnerConfig.read_all_from_file()
            if len(runner_configs) == 0:
                print(messages.NO_RUNNERS_MESSAGE)
                sys.exit(1)

            runner_names = select_runners("restart")
            for runner_config in runner_configs:
                if runner_config.name in runner_names:
                    CustomRunner(runner_name_or_hash=runner_config.id[-6:]).restart()
        else:
            CustomRunner(runner_name_or_hash=name_or_hash).restart()
    except KeyboardInterrupt:
        sys.exit(1)
    except (error.Error, Exception):
        log_errors()
        sys.exit(1)


def reauth_runner(name_or_hash: str, max_retry_count: int = 3) -> None:
    """
    Reauthenticate the custom runner with a new secret key.

    :param name_or_hash (str): Runner name or hash.
    :return: None
    """

    def get_runner_name_or_hash():
        runner_configs = RunnerConfig.read_all_from_file()
        if len(runner_configs) == 0:
            print(messages.NO_RUNNERS_MESSAGE)
            sys.exit(1)

        runner_choices = []
        for runner_config in runner_configs:
            try:
                runner_config.update()
            except error.Error as exc:
                if "Workspace ID / Secret Key combination" in exc.message:
                    runner_choices.append(runner_config.name)
                else:
                    print(exc.message)
                    sys.exit(1)
            finally:
                runner_config.write_to_file()

        if not runner_choices:
            print(messages.ALL_RUNNERS_VALID_SECRET_KEYS_MESSAGE)
            sys.exit(1)

        name_or_hash = (
            inquirer.select(
                "Which runner do you want to reauthenticate? "
                "(only Runners with invalid secret keys are shown)",
                choices=runner_choices,
                border=True,
            )
            .execute()
            .split(" [")[0]
        )
        return name_or_hash

    try:
        if not name_or_hash:
            name_or_hash = get_runner_name_or_hash()

        runner = CustomRunner(runner_name_or_hash=name_or_hash)
        if runner.config.status.valid_secret_key:
            print(
                messages.VALID_SECRET_KEY_MESSAGE.format(
                    runner.config.name, runner.config.id[-6:]
                )
            )
            sys.exit(1)

        new_secret_key = ""
        secret_key_retry_count = 0
        while not new_secret_key:
            new_secret_key = (
                inquirer.secret(messages.NEW_SECRET_KEY_MESSAGE)
                .execute()
                .strip()
                .lower()
            )
            if new_secret_key == "":
                print(messages.EMPTY_SECRET_KEY_MESSAGE)
            elif len(new_secret_key) != 64:
                new_secret_key = ""
                print(messages.INVALID_SECRET_KEY_LENGTH_MESSAGE)

            secret_key_retry_count += 1
            if secret_key_retry_count >= max_retry_count:
                print(messages.MAX_RETRY_MESSAGE)
                sys.exit(1)

        runner.reauth(new_secret_key=new_secret_key)
    except KeyboardInterrupt:
        sys.exit(1)
    except (error.Error, Exception):
        log_errors()
        sys.exit(1)


def dump_runner_logs(name_or_hash: str, run_hash: str, file: str) -> None:
    """
    Dumps the custom runner logs to a file.

    :param name_or_hash (str): Runner name or hash.
    :return: None
    """

    try:
        if not name_or_hash:
            runner_configs = RunnerConfig.read_all_from_file()

            if len(runner_configs) == 0:
                print(messages.NO_RUNNERS_MESSAGE)
                sys.exit(1)

            runner_names = select_runners("retrieve logs from", allow_all=False)
            for runner_config in runner_configs:
                if runner_config.name in runner_names:
                    CustomRunner(runner_name_or_hash=runner_config.id[-6:]).dump_logs(
                        run_hash=run_hash.lower() if run_hash else "", file=file
                    )
        else:
            CustomRunner(runner_name_or_hash=name_or_hash).dump_logs(
                run_hash=run_hash.lower() if run_hash else "", file=file
            )
    except KeyboardInterrupt:
        sys.exit(1)
    except (error.Error, Exception):
        log_errors()
        sys.exit(1)


def display_runner_status(name_or_hash: str) -> None:
    """
    Dumps the custom runner logs to a file.

    :param name_or_hash (str): Runner name or hash.
    :return: None
    """

    try:
        if not name_or_hash:
            runner_configs = RunnerConfig.read_all_from_file()
            if len(runner_configs) == 0:
                print(messages.NO_RUNNERS_MESSAGE)
                sys.exit(1)

            runner_names = select_runners("display status of")
            for runner_config in runner_configs:
                if runner_config.name in runner_names:
                    CustomRunner(
                        runner_name_or_hash=runner_config.id[-6:]
                    ).display_status()
        else:
            CustomRunner(runner_name_or_hash=name_or_hash).display_status()
    except KeyboardInterrupt:
        sys.exit(1)
    except (error.Error, Exception):
        log_errors()
        sys.exit(1)


def list_runners() -> None:
    """
    List all custom runners.

    :return: None
    """

    try:
        runner_configs = RunnerConfig.read_all_from_file()
        if len(runner_configs) == 0:
            print(messages.NO_RUNNERS_MESSAGE)
            sys.exit(1)

        all_secret_keys_valid = True
        for runner_config in runner_configs:
            try:
                runner_config.update()
            except error.Error as exc:
                if "Workspace ID / Secret Key combination" in exc.message:
                    all_secret_keys_valid = False
                else:
                    print(exc.message)
                    sys.exit(1)
            finally:
                runner_config.write_to_file()

        format_runner_list(runner_configs)
        if not all_secret_keys_valid:
            print(messages.INVALID_SECRET_KEYS_MESSAGE)
    except KeyboardInterrupt:
        sys.exit(1)
    except (error.Error, Exception):
        log_errors()
        sys.exit(1)
