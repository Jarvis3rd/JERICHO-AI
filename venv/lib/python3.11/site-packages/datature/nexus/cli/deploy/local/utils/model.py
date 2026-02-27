#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   model.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Model types.
"""

# pylint: disable=R0902

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np

from datature.nexus.cli.deploy.local.types.skeleton import Skeleton
from datature.nexus.cli.deploy.local.utils.inference import (
    PredictionTaskType,
    TensorDescription,
)
from datature.nexus.cli.deploy.local.utils.label_map import LabelMap


class ModelBackend(Enum):
    """Backend used for model inference."""

    ONNX = "ONNX"
    TENSORFLOW = "TensorFlow"
    PYTORCH = "PyTorch"
    TFLITE = "TFLite"
    OPENVINO = "OpenVINO"


class ModelType(Enum):
    """Model architecture enum."""

    ULTRALYTICS = "Ultralytics"
    POLYBIUS_V1 = "PolybiusV1"
    OBJECT_DETECTION = "ObjectDetection"
    STREAMING = "STREAMING"


class ModelArchitecture(Enum):
    """Model architecture enum."""

    DEEPLABV3 = "DEEPLABV3"
    YOLOV4 = "YOLOV4"
    YOLOX = "YOLOX"
    PALIGEMMA = "PALIGEMMA"


@dataclass
class Model:
    """Base model class."""

    model: Any

    versions: List[int]
    backend: ModelBackend
    model_type: ModelType

    label_map: LabelMap

    inputs: List[TensorDescription]
    outputs: List[TensorDescription]

    task_type: PredictionTaskType


@dataclass
class KeypointModel(Model):
    """Keypoint detection model class."""

    skeletons: Optional[Dict[str, Skeleton]] = None


@dataclass
class VideoClassificationModel(Model):
    """Video classification model class."""

    memory: Dict[str, np.ndarray] = field(default_factory=dict)
    memory_initialized: bool = False
