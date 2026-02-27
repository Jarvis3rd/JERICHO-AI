# !/usr/env/bin python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   utils.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Custom model utility functions.
"""
# pylint: disable=R0914

import yaml

from .types import (
    ConfigRequiredFields,
    InputFormatOptions,
    InputRequiredFields,
    OutputFormatOptions,
    OutputRequiredFields,
    TaskTypes,
)


def verify_graph_module(graph_module_path: str):
    """Verify the PyTorch GraphModule file.

    :param graph_module_path: Path to the PyTorch GraphModule file.

    :raises ValueError: If the PyTorch GraphModule file is not saved
        using torch.save() or the file is corrupted.
    """
    local_header_magic_number = [b"P", b"K", b"\x03", b"\x04"]
    read_bytes = []

    with open(graph_module_path, "rb") as graph_module_reader:
        for _ in range(4):
            byte = graph_module_reader.read(1)

            if byte == b"":
                break

            read_bytes.append(byte)

    if read_bytes != local_header_magic_number:
        raise ValueError(
            "PyTorch GraphModule does not seem to be saved using "
            "torch.save() or the file is corrupted. "
            "Please save the model using torch.save() and try again."
        )


def verify_yaml_config(yaml_file: str):
    """Verify the YAML configuration file.

    :param yaml_file: Path to the YAML configuration file.
    """
    with open(yaml_file, "r", encoding="utf-8") as yaml_reader:
        yaml_content = yaml.safe_load(yaml_reader)

    assert yaml_content, "YAML file is empty. Please provide a valid YAML file."
    for config_field in ConfigRequiredFields:
        assert config_field.value in yaml_content, (
            f"Config field '{config_field.value}' is missing from the YAML file. "
            "Please provide the missing field."
        )

    task = yaml_content["task"]
    assert task in TaskTypes, f"Task type '{task}' needs to be one of {TaskTypes}"

    inputs = yaml_content["inputs"]
    assert inputs, (
        "No input fields found in the YAML file. "
        "Please provide at least one input field."
    )

    input_required_fields = InputRequiredFields[task.upper()].value
    for input_field in input_required_fields:
        assert inputs.get(input_field), (
            f"Input field '{input_field}' is missing from the YAML file. "
            "Please provide the missing field."
        )

    for key, value in inputs.items():
        assert isinstance(
            value["name"], str
        ), f"Input name '{value['name']}' must be a string"
        assert isinstance(
            value["key"], str
        ), f"Input key '{value['key']} must be a string"
        assert isinstance(
            value["format"], list
        ), f"Input format '{value['format']}' must be a list"
        assert value["format"] in InputFormatOptions, (
            f"Input format '{value['format']}' "
            f"needs to be one of {InputFormatOptions}"
        )
        assert isinstance(
            value["shape"], list
        ), f"Input shape '{value['shape']}' must be a list"
        assert len(value["shape"]) == len(value["format"]), (
            f"Input shape {len(value['shape'])} and input format "
            f"{len(value['format'])} must have the same number of elements"
        )

    outputs = yaml_content["outputs"]
    assert outputs, (
        "No output fields found in the YAML file. "
        "Please provide at least one output field."
    )

    output_required_fields = OutputRequiredFields[task.upper()].value
    for output_field in output_required_fields:
        assert outputs.get(output_field), (
            f"Output field '{output_field}' is missing from the YAML file. "
            "Please provide the missing field."
        )

    output_format_options = OutputFormatOptions[task.upper()].value
    for key, value in outputs.items():
        assert isinstance(
            value["name"], str
        ), f"Output name '{value['name']}' must be a string"
        assert isinstance(
            value["key"], str
        ), f"Output key '{value['key']} must be a string"

        if key in output_required_fields:
            assert value["format"] in output_format_options[key.upper()].value, (
                f"Output format '{value['format']}' "
                f"needs to be one of {output_format_options[key.upper()].value}"
            )

        assert isinstance(
            value["shape"], list
        ), f"Output shape '{value['shape']}' must be a list"
        assert len(value["shape"]) == len(value["format"]), (
            f"Output shape {len(value['shape'])} and format "
            f"{len(value['format'])} must have the same number of elements"
        )
