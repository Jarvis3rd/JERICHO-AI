#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   commands.py
@Author  :   Wei Loon Cheng, Kai Xuan Lee
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Custom runner installation commands.
"""

PIP_INSTALL_PACKAGE_COMMAND = "{} -m pip install {}"
MICROK8S_CONFIG_COMMAND = "microk8s kubectl config view --raw"
MICROK8S_STATUS_COMMAND = "microk8s status --wait-ready"
