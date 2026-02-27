#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   predictor_factory.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Factory class for creating model predictors.
"""

from typing import Dict, Tuple, Type

from datature.nexus.cli.deploy.local.predictors.base_predictor import BasePredictor
from datature.nexus.cli.deploy.local.predictors.onnx_predictor import (
    ONNXClassificationPredictor,
    ONNXObjectDetectionPredictor,
    ONNXSegmentationPredictor,
    ONNXSemantic3DSegmentationPredictor,
    ONNXUltralyticsPredictor,
)
from datature.nexus.cli.deploy.local.utils.inference import PredictionTaskType
from datature.nexus.cli.deploy.local.utils.model import ModelBackend, ModelType


class PredictorFactory:
    """Factory class for creating model predictors."""

    _predictors: Dict[
        Tuple[ModelBackend, PredictionTaskType, ModelType], Type[BasePredictor]
    ] = {}

    @classmethod
    def register(
        cls,
        backend: ModelBackend,
        task_type: PredictionTaskType,
        model_type: ModelType,
        predictor_class: Type[BasePredictor],
    ) -> None:
        """Register a predictor class."""
        cls._predictors[(backend, task_type, model_type)] = predictor_class

    @classmethod
    def create(
        cls,
        backend: ModelBackend,
        task_type: PredictionTaskType,
        model_type: ModelType,
        **kwargs,
    ) -> BasePredictor:
        """Create a predictor instance."""
        key = (backend, task_type, model_type)
        if key not in cls._predictors:
            raise ValueError(f"No predictor registered for {key}")

        predictor_class = cls._predictors[key]
        return predictor_class(**kwargs)


# Register default predictors
PredictorFactory.register(
    ModelBackend.ONNX,
    PredictionTaskType.OBJECT_DETECTION,
    ModelType.ULTRALYTICS,
    ONNXUltralyticsPredictor,
)

PredictorFactory.register(
    ModelBackend.ONNX,
    PredictionTaskType.INSTANCE_SEGMENTATION,
    ModelType.ULTRALYTICS,
    ONNXUltralyticsPredictor,
)

PredictorFactory.register(
    ModelBackend.ONNX,
    PredictionTaskType.KEYPOINT_DETECTION,
    ModelType.ULTRALYTICS,
    ONNXUltralyticsPredictor,
)

PredictorFactory.register(
    ModelBackend.ONNX,
    PredictionTaskType.IMAGE_CLASSIFICATION,
    ModelType.ULTRALYTICS,
    ONNXUltralyticsPredictor,
)

PredictorFactory.register(
    ModelBackend.ONNX,
    PredictionTaskType.OBJECT_DETECTION,
    ModelType.OBJECT_DETECTION,
    ONNXObjectDetectionPredictor,
)

PredictorFactory.register(
    ModelBackend.ONNX,
    PredictionTaskType.INSTANCE_SEGMENTATION,
    ModelType.OBJECT_DETECTION,
    ONNXSegmentationPredictor,
)

PredictorFactory.register(
    ModelBackend.ONNX,
    PredictionTaskType.SEMANTIC_SEGMENTATION,
    ModelType.OBJECT_DETECTION,
    ONNXSegmentationPredictor,
)

PredictorFactory.register(
    ModelBackend.ONNX,
    PredictionTaskType.IMAGE_CLASSIFICATION,
    ModelType.POLYBIUS_V1,
    ONNXClassificationPredictor,
)

PredictorFactory.register(
    ModelBackend.ONNX,
    PredictionTaskType.OBJECT_DETECTION,
    ModelType.POLYBIUS_V1,
    ONNXObjectDetectionPredictor,
)

PredictorFactory.register(
    ModelBackend.ONNX,
    PredictionTaskType.INSTANCE_SEGMENTATION,
    ModelType.POLYBIUS_V1,
    ONNXSegmentationPredictor,
)

PredictorFactory.register(
    ModelBackend.ONNX,
    PredictionTaskType.SEMANTIC_SEGMENTATION,
    ModelType.POLYBIUS_V1,
    ONNXSegmentationPredictor,
)

PredictorFactory.register(
    ModelBackend.ONNX,
    PredictionTaskType.SEMANTIC_3D_SEGMENTATION,
    ModelType.POLYBIUS_V1,
    ONNXSemantic3DSegmentationPredictor,
)
