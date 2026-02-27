#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   inference.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Inference utility types.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Tuple


class ModelExtension(Enum):
    """Model extension enum."""

    TF = "saved_model"
    TFLITE = ".tflite"
    ONNX = ".onnx"
    PYTORCH = ".pth"

    @classmethod
    def has_value(cls, value):
        """Check if enum contains value.

        Args:
            value: Value to check.

        Returns:
            True if value is in enum, False otherwise.
        """
        return value in cls._value2member_map_


class TensorDtype(Enum):
    """Data type of a tensor."""

    FP16 = "FP16"
    FP32 = "FP32"
    FP64 = "FP64"
    UINT8 = "UINT8"
    UINT16 = "UINT16"
    UINT32 = "UINT32"
    UINT64 = "UINT64"
    INT8 = "INT8"
    INT16 = "INT16"
    INT32 = "INT32"
    INT64 = "INT64"
    BOOL = "BOOL"


class PredictionTaskType(Enum):
    """Inference task type enum."""

    IMAGE_CLASSIFICATION = "ImageClassification"
    OBJECT_DETECTION = "ObjectDetection"
    INSTANCE_SEGMENTATION = "InstanceSegmentation"
    SEMANTIC_SEGMENTATION = "SemanticSegmentation"
    SEMANTIC_3D_SEGMENTATION = "Semantic3DSegmentation"
    KEYPOINT_DETECTION = "KeypointDetection"


@dataclass
class TensorDescription:
    """Description of a tensor returned by or fed into a model."""

    name: str
    dtype: TensorDtype
    shape: Tuple[int]
