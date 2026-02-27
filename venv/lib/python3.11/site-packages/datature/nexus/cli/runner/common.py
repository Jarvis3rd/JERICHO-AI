#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   common.py
@Author  :   Wei Loon Cheng, Kai Xuan Lee
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Custom runner common functions.
"""

import shlex
import subprocess
import sys
import traceback
from datetime import datetime

from datature.nexus.cli.runner import commands as COMMANDS
from datature.nexus.cli.runner import consts as CONSTS
from datature.nexus.cli.runner import messages as MESSAGES


def install_pip_package(package_name: str):
    """Install pip package.

    :param package_name (str): Package name.
    :return (bool): True if successful, False otherwise.ise.
    """
    result = subprocess.run(
        shlex.split(
            COMMANDS.PIP_INSTALL_PACKAGE_COMMAND.format(sys.executable, package_name)
        ),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
        text=True,
    )
    if result.returncode != 0:
        return False
    return True


def log_errors(unknown: bool = False) -> None:
    """Log errors to file.

    :param unknown (bool): True if error is unknown, False otherwise.
    """
    CONSTS.ERROR_LOG_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now()
    logs_path = (
        CONSTS.ERROR_LOG_DIR / f"datature-{now.strftime('%Y-%m-%d_%H-%M-%S')}.log"
    )
    logs_path.write_text(traceback.format_exc())
    if unknown:
        print(MESSAGES.RUNNER_UNKNOWN_ERROR_MESSAGE.format(logs_path))
    else:
        print(MESSAGES.RUNNER_TRACEBACK_MESSAGE.format(logs_path))
