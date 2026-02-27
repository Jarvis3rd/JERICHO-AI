#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   base_predictor.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Base class for all predictors.
"""

from abc import ABC, abstractmethod
from typing import Any

from datature.nexus.cli.deploy.local.utils.model import Model


class BasePredictor(ABC):
    """Base class for all predictors."""

    _model: Model

    def __init__(self, model: Model, **kwargs):
        """Initialize Base Predictor."""
        self.__dict__.update(kwargs)
        self._model = model

    def run(self, **kwargs) -> dict[str, Any]:
        """Run prediction pipeline."""
        preprocessed_inputs = self._preprocess(**kwargs)
        raw_predictions = self._predict(**preprocessed_inputs, **kwargs)
        postprocessed_predictions = self._postprocess(**raw_predictions, **kwargs)
        return postprocessed_predictions

    @abstractmethod
    def _predict(self, **kwargs) -> Any:
        """Predict on image.

        Args:
            img: Image to predict on.

        Returns:
            Raw model output.
        """
        raise ValueError("Abstract function needs to be implemented")

    @abstractmethod
    def _preprocess(self, **kwargs) -> Any:
        """Preprocess image."""
        raise ValueError("Abstract function needs to be implemented")

    @abstractmethod
    def _postprocess(self, **kwargs) -> dict[str, Any]:
        """Postprocess raw model output into interpretable predictions."""
        raise ValueError("Abstract function needs to be implemented")

    @property
    def model(self) -> Model:
        """Get model."""
        return self._model
