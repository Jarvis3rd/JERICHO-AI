#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   consts.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   CLI Constants.
"""

from enum import Enum, unique

from datature.nexus.api.types import add_mapping

INQUIRER_CHOICES_MAX_VISIBLE_ENTRIES = 10

DEFAULT_INSTANCES = [
    "instance_x1cpu-standard",
    "instance_t4-standard-1g",
    "instance_l4-standard-1g",
]


@add_mapping
@unique
class ResourceType(Enum):
    """Resource type enumeration."""

    GPU = "GPU"
    CPU = "CPU"

    __MAPPING__ = {
        "GPU": GPU,
        "CPU": CPU,
    }
