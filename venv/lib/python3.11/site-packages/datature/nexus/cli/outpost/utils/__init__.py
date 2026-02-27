#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   init.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   CLI Outpost utils import module.
"""

from .config import (
    create_configuration,
    list_configurations,
    prompt_for_configuration_version,
    prompt_for_python_version,
    prompt_for_runtime_config,
    select_default_artifact,
)
from .device_config import DEVICE_CONFIG
from .helper import interpolate_config_variables, start_spinner
from .system_specs import check_system_specs, get_current_device_info
from .utils import (
    deregister_device,
    format_outpost_runtime_status,
    generate_device_config,
    generate_device_info,
    generate_metadata_spec,
    generate_pem_keys,
    get_certificate_expiry,
    get_device,
    get_outpost_device_config_files,
    get_outpost_runtime_files,
    get_outpost_runtime_status,
    get_runtime_status_message,
    get_service_status,
    install_runtime,
    list_devices,
    parse_systemctl_output,
    patch_device,
    register_device,
    setup_outpost_credentials,
    uninstall_runtime,
    validate_certificate,
    validate_device,
)
