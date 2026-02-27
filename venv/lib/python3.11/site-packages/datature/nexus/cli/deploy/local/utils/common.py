#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   common.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Common utilities for the local deployment server.
"""

# pylint: disable=W0718

import queue
import sys
import threading
from functools import wraps
from typing import Callable, Optional, Union

from colorama import Fore
from halo import Halo

from datature.nexus.error import Error


def start_spinner(func: Optional[Callable] = None) -> Union[Callable, Callable]:
    """Start spinner for the function."""

    def decorator(func: Callable):
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
                result, message = func(*args, **kwargs, message_queue=message_queue)
                if not kwargs.get("quiet", False):
                    wait_spinner.succeed(message)
                return result
            except KeyboardInterrupt:
                wait_spinner.stop()
                sys.exit(0)
            except Error as exc:
                error_symbol = f"{Fore.CYAN}●{Fore.RESET}"
                wait_spinner.stop_and_persist(error_symbol, exc.message)
                sys.exit(1)
            except Exception as exc:
                error_symbol = f"{Fore.CYAN}●{Fore.RESET}"
                wait_spinner.stop_and_persist(error_symbol, str(exc))
                sys.exit(1)
            finally:
                stop_thread.set()
                thread.join()
                wait_spinner.stop()

        return wrapper

    if func is None:
        return decorator
    return decorator(func)
