#!/usr/env/bin python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   logger.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   TensorRT logging module.
"""

import logging

from colorama import Fore, Style

trt_logger = logging.getLogger("trt")
trt_logger.setLevel(logging.DEBUG)


class ColoredFormatter(logging.Formatter):
    """Logging colored formatter"""

    def __init__(self):
        super().__init__()
        self._formats = {
            logging.DEBUG: (
                f" {Fore.BLUE} %(levelname)s"
                f" {Fore.WHITE} %(message)s{Style.RESET_ALL}"
            ),
            logging.INFO: (
                f" {Style.RESET_ALL}{Fore.CYAN} %(levelname)s"
                f" {Fore.WHITE} %(message)s{Style.RESET_ALL}"
            ),
            logging.WARNING: (
                f" {Style.RESET_ALL}{Fore.YELLOW} %(levelname)s"
                f" {Fore.YELLOW + Style.BRIGHT} %(message)s{Style.RESET_ALL}"
            ),
            logging.ERROR: (
                f" {Style.RESET_ALL}{Fore.RED} %(levelname)s"
                f" {Style.BRIGHT} %(message)s{Style.RESET_ALL}"
            ),
            logging.CRITICAL: (
                f" {Style.RESET_ALL}{Fore.RED} %(levelname)s"
                f" {Style.BRIGHT} %(message)s{Style.RESET_ALL}"
            ),
        }

    def format(self, record):
        log_fmt = self._formats.get(record.levelno)
        date_fmt = "%Y-%m-%d %H:%M:%S"
        formatter = logging.Formatter(fmt=log_fmt, datefmt=date_fmt)
        return formatter.format(record)


stdout_handler = logging.StreamHandler()
stdout_handler.setLevel(logging.INFO)
stdout_handler.setFormatter(ColoredFormatter())

trt_logger.addHandler(stdout_handler)

warnings_logger = logging.getLogger("py.warnings")
warnings_logger.addHandler(stdout_handler)
