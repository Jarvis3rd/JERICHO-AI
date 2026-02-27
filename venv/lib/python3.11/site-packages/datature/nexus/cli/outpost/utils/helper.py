#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   helper.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Common helper functions for Outpost.
"""

# pylint: disable=W0719

import queue
import re
import sys
import threading
from functools import wraps
from typing import Dict

from colorama import Fore
from halo import Halo

from datature.nexus.error import Error

VAR_RE = re.compile(
    r"\${{\s*([a-zA-Z_][a-zA-Z0-9_]{0,63})\s*}}", flags=re.DOTALL | re.MULTILINE
)


def start_spinner(func: callable = None, raise_on_error: bool = False) -> callable:
    """Start spinner for the function."""

    def decorator(func: callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            wait_spinner = Halo(spinner="dots")
            message_queue = queue.Queue()
            stop_thread = threading.Event()

            def update_spinner():
                while not stop_thread.is_set():
                    try:
                        new_message = message_queue.get(timeout=0.1)
                        if not kwargs.get("quiet", False) and new_message is not None:
                            wait_spinner.text = new_message
                    except queue.Empty:
                        continue

            thread = threading.Thread(target=update_spinner)
            wait_spinner.start()
            thread.start()

            try:
                result = func(*args, **kwargs, message_queue=message_queue)
                if not kwargs.get("quiet", False):
                    wait_spinner.succeed(result)
                return result

            except Error as exc:
                error_symbol = f"{Fore.CYAN}●{Fore.RESET}"
                wait_spinner.stop_and_persist(error_symbol, exc.message)

                if raise_on_error:
                    raise exc
                sys.exit(1)

            except Exception as exc:  # pylint: disable=W0718
                error_symbol = f"{Fore.CYAN}●{Fore.RESET}"
                wait_spinner.stop_and_persist(error_symbol, str(exc))

                if raise_on_error:
                    raise exc
                sys.exit(1)

            finally:
                stop_thread.set()
                thread.join()
                wait_spinner.stop()

        return wrapper

    if func is None:
        return decorator
    return decorator(func)


def interpolate_config_variables(config_str: str, variables: Dict[str, str]) -> str:
    """Replace all occurrences of ${{ variable_name }} in config_str with
    corresponding values from the variables dictionary.
    """

    def replace_var(match):
        var_name = match.group(1)
        if var_name not in variables:
            raise KeyError(f"Undefined variable referenced in template: '{var_name}'")

        return str(variables[var_name])

    # Use re.sub with a replacement function to replace all matches
    return VAR_RE.sub(replace_var, config_str)
