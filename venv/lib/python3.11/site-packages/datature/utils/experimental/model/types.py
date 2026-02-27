# !/usr/env/bin python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   types.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Custom model config types module.
"""
# pylint: disable=C0203, E1133

from enum import Enum, EnumMeta, unique


class FormatMeta(EnumMeta):
    """Metaclass for format options."""

    def __contains__(self, item):
        return item in [member.value for member in self]

    def __str__(self) -> str:
        return str([format.value for format in self])

    def __values__(self) -> list:
        return [format.value for format in self]


@unique
class ConfigRequiredFields(Enum, metaclass=FormatMeta):
    """Config fields for custom models."""

    TASK = "task"
    INPUTS = "inputs"
    OUTPUTS = "outputs"


@unique
class TaskTypes(Enum, metaclass=FormatMeta):
    """Task types for custom models."""

    CLASSIFICATION = "classification"
    BBOX = "bbox"
    SEMANTIC = "semantic"


class InputRequiredFields(Enum, metaclass=FormatMeta):
    """Input required fields for custom models."""

    CLASSIFICATION = ["image"]
    BBOX = ["image"]
    SEMANTIC = ["image"]


@unique
class OutputRequiredFields(Enum, metaclass=FormatMeta):
    """Output required fields for custom models."""

    CLASSIFICATION = ["class_scores"]
    BBOX = ["class_scores", "bounding_boxes"]
    SEMANTIC = ["mask_scores"]


@unique
class InputFormatOptions(Enum, metaclass=FormatMeta):
    """Input format options for custom models."""

    NCHW = ["n", "c", "h", "w"]
    NHWC = ["n", "h", "w", "c"]


@unique
class ClassificationOutputFormatOptions(Enum, metaclass=FormatMeta):
    """Output format options for image classification models."""

    CLASS_SCORES = [["batch_size", "num_classes"]]


class BboxFormats(Enum, metaclass=FormatMeta):
    """Output format options for bounding boxes."""

    XYXY = ["batch_size", "num_det", ["xmin", "ymin", "xmax", "ymax"]]
    YXYX = ["batch_size", "num_det", ["ymin", "xmin", "ymax", "xmax"]]
    XYWH = ["batch_size", "num_det", ["xmin", "ymin", "width", "height"]]
    CXCYWH = ["batch_size", "num_det", ["cx", "cy", "width", "height"]]


@unique
class BboxOutputFormatOptions(Enum, metaclass=FormatMeta):
    """Output format options for custom models."""

    CLASS_SCORES = [["batch_size", "num_det", "num_classes"]]
    BOUNDING_BOXES = BboxFormats.__values__()
    BOX_SCORES = [["batch_size", "num_det"]]


class SemanticOutputFormatOptions(Enum, metaclass=FormatMeta):
    """Output format options for semantic segmentation models."""

    MASK_SCORES = [["batch_size", "num_classes", "height", "width"]]


class OutputFormatOptions(Enum, metaclass=FormatMeta):
    """Output format options for custom models."""

    CLASSIFICATION = ClassificationOutputFormatOptions
    BBOX = BboxOutputFormatOptions
    SEMANTIC = SemanticOutputFormatOptions
