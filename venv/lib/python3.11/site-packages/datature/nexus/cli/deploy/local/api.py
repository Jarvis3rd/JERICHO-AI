#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   api.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   API class for the inference server.
"""

# pylint: disable=R0902

import os
from typing import Any, Dict

import litserve as ls
import msgspec

from datature.nexus.cli.deploy.local.consts import RUNTIME_OPTIONS
from datature.nexus.cli.deploy.local.loaders.onnx_loader import ONNXLoader
from datature.nexus.cli.deploy.local.predictors.predictor_factory import (
    PredictorFactory,
)
from datature.nexus.cli.deploy.local.types.prediction_request import PredictRequest
from datature.nexus.cli.deploy.local.types.prediction_response import (
    APIDeploymentPredictionResponse,
    PredictionResponse,
)
from datature.nexus.cli.deploy.local.utils.entropy import (
    calculate_avg_entropy,
    calculate_avg_entropy_per_class,
)
from datature.nexus.cli.deploy.local.utils.image_decoder import (
    decode_image_from_base64,
    decode_image_from_bytes,
    decode_image_from_path,
)
from datature.nexus.cli.deploy.local.utils.management_api import ManagementAPIClient
from datature.nexus.cli.deploy.local.utils.prediction_formatter import (
    PredictionFormatter,
)


class InferenceAPI(ls.LitAPI):
    """Inference API class.

    This class is used to create a local deployment server.
    """

    def __init__(
        self,
        secret_key: str,
        project_id: str,
        artifact_id: str,
        runtime: str,
    ):
        super().__init__()

        self.secret_key = secret_key
        self.project_id = project_id
        self.artifact_id = artifact_id
        self.runtime = runtime

        if runtime not in RUNTIME_OPTIONS:
            raise ValueError(f"Unsupported runtime: {runtime}")

        self.execution_provider = RUNTIME_OPTIONS[runtime]
        self._management_api_client = ManagementAPIClient(
            secret_key=self.secret_key,
            project_id=self.project_id,
        )

        self.model = None
        self.predictor = None
        self.formatter = PredictionFormatter()

        self.current_request = None

    def health(self, **kwargs) -> bool:  # pylint: disable=unused-argument
        """Check the health of the server."""
        return True

    def setup(self, device: Any):  # pylint: disable=unused-argument
        """Initialize the model and set up the inference environment."""
        self.model = ONNXLoader(
            artifact_id=self.artifact_id,
            execution_provider=self.execution_provider,
            model_format="ONNX",
            management_api_client=self._management_api_client,
        ).load()

        self.predictor = PredictorFactory.create(
            backend=self.model.backend,
            task_type=self.model.task_type,
            model_type=self.model.model_type,
            model=self.model,
        )

    def decode_request(
        self, request: dict, **kwargs  # pylint: disable=unused-argument
    ) -> Dict[str, Any]:
        """Decode the incoming request to get the image data.

        Returns:
            Dictionary containing the image data and other metadata, if applicable.
        """
        self.current_request = msgspec.convert(request, type=PredictRequest)

        if isinstance(self.current_request.data, str):
            if self.current_request.encoding == "base64":
                return decode_image_from_base64(
                    self.current_request.data, self.current_request.response_format
                )

            if os.path.exists(self.current_request.data):
                return decode_image_from_path(self.current_request.data)

        if isinstance(self.current_request.data, bytes):
            return decode_image_from_bytes(
                self.current_request.data, self.current_request.response_format
            )

        raise ValueError("Invalid image data")

    def predict(self, x: Dict[str, Any], **kwargs):  # pylint: disable=unused-argument
        """Run inference on the input image."""
        return {
            "predictions": self.predictor.run(**x),
            **x,
        }

    def encode_response(
        self, output: Dict[str, Any], **kwargs  # pylint: disable=unused-argument
    ) -> dict:
        """Encode the model output into the response format."""
        formatted_predictions = self.formatter.run(
            task_type=self.model.task_type,
            response_format=self.current_request.response_format,
            label_map=self.model.label_map,
            skeletons=(
                self.model.skeletons if hasattr(self.model, "skeletons") else None
            ),
            **output,
        )

        avg_entropy = calculate_avg_entropy(formatted_predictions)
        avg_entropy_for_class = calculate_avg_entropy_per_class(
            formatted_predictions, self.model.label_map
        )

        prediction_response = PredictionResponse(
            predictions=formatted_predictions,
            avg_entropy=avg_entropy,
            avg_entropy_for_class=avg_entropy_for_class,
            image=None,
            warnings=None,
        )

        response = APIDeploymentPredictionResponse(
            tags=self.model.label_map.to_dict(),
            response=prediction_response,
        )

        return msgspec.to_builtins(response)
