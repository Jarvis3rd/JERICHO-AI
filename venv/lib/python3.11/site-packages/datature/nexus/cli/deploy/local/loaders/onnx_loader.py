#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   onnx_loader.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   ONNX Loader class.
"""

# pylint: disable=R0914

import ast
import json
import logging
import queue
import subprocess
import sys
from typing import Dict

try:
    import onnxruntime as ort

except (ModuleNotFoundError, ImportError):
    print("Installing onnxruntime...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "onnxruntime"])

    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-q", "onnxruntime-gpu"]
        )
    except subprocess.CalledProcessError:
        pass

    import onnxruntime as ort

from datature.nexus.cli.deploy.local.loaders.base_loader import BaseLoader
from datature.nexus.cli.deploy.local.types.skeleton import Skeleton
from datature.nexus.cli.deploy.local.utils.colors import get_color_for_label_id
from datature.nexus.cli.deploy.local.utils.common import start_spinner
from datature.nexus.cli.deploy.local.utils.inference import (
    PredictionTaskType,
    TensorDescription,
    TensorDtype,
)
from datature.nexus.cli.deploy.local.utils.label_map import (
    LabelMap,
    LabelMapEntry,
    LabelMapFromPbtxt,
)
from datature.nexus.cli.deploy.local.utils.model import (
    KeypointModel,
    Model,
    ModelArchitecture,
    ModelBackend,
    ModelType,
)

logger = logging.getLogger("datature-nexus")

ULTRALYTICS_MODELS = ["yolov8", "yolov9", "yolo11"]

ULTRALYTICS_TASKS = {
    "ObjectDetection": "detect",
    "InstanceSegmentation": "segment",
    "SemanticSegmentation": "segment",
    "KeypointDetection": "pose",
    "ImageClassification": "classify",
}

POLYBIUS_PREDICTION_TYPES: Dict[str, PredictionTaskType] = {
    "bbox": PredictionTaskType.OBJECT_DETECTION,
    "instance": PredictionTaskType.INSTANCE_SEGMENTATION,
    "semantic": PredictionTaskType.SEMANTIC_SEGMENTATION,
    "semantic_3d": PredictionTaskType.SEMANTIC_3D_SEGMENTATION,
    "classification": PredictionTaskType.IMAGE_CLASSIFICATION,
    "keypoints": PredictionTaskType.KEYPOINT_DETECTION,
}

LEGACY_MODEL_ARCHITECTURES: Dict[str, ModelArchitecture] = {
    "deeplabv3": ModelArchitecture.DEEPLABV3,
    "yolov4": ModelArchitecture.YOLOV4,
    "yolox": ModelArchitecture.YOLOX,
}

LEGACY_MODEL_TASK_TYPES: Dict[str, PredictionTaskType] = {
    "deeplabv3": PredictionTaskType.SEMANTIC_SEGMENTATION,
    "yolov4": PredictionTaskType.OBJECT_DETECTION,
    "yolox": PredictionTaskType.OBJECT_DETECTION,
}

EXECUTION_PROVIDERS = {
    "CPU": "CPUExecutionProvider",
    "CUDA": "CUDAExecutionProvider",
}

ONNX_SUPPORTED_DTYPES: Dict[str, TensorDtype] = {
    "tensor(float)": TensorDtype.FP32,
    "tensor(float16)": TensorDtype.FP16,
    "tensor(uint8)": TensorDtype.UINT8,
    "tensor(uint16)": TensorDtype.UINT16,
    "tensor(uint32)": TensorDtype.UINT32,
    "tensor(uint64)": TensorDtype.UINT64,
    "tensor(int8)": TensorDtype.INT8,
    "tensor(int16)": TensorDtype.INT16,
    "tensor(int32)": TensorDtype.INT32,
    "tensor(int64)": TensorDtype.INT64,
    "tensor(bool)": TensorDtype.BOOL,
}


def _tensor_description_from_onnx_node_arg(node_arg: ort.NodeArg):
    """Create TensorDescription from ONNX NodeArg."""
    if node_arg.type not in ONNX_SUPPORTED_DTYPES:
        raise ValueError(
            f"Cannot infer TensorDescription from ONNX NodeArg of type "
            f"{node_arg.type}, expected one of: "
            f"{', '.join(ONNX_SUPPORTED_DTYPES.keys())}"
        )

    name = node_arg.name

    # Important! We don't preserve any distinctions between the unknown
    # tensor dimension sizes, so we assume they can vary freely.
    shape = tuple(map(lambda size: -1 if "unk" in str(size) else size, node_arg.shape))

    return TensorDescription(
        name=name, dtype=ONNX_SUPPORTED_DTYPES[node_arg.type], shape=shape
    )


class ONNXLoader(BaseLoader):
    """ONNX Loader class."""

    @start_spinner
    def load(self, message_queue: queue.Queue = queue.Queue()):
        """Load ONNX model."""
        message_queue.put("Loading ONNX model...")

        session_options = ort.SessionOptions()
        session_options.log_severity_level = 3
        session = ort.InferenceSession(
            self._model_path,
            sess_options=session_options,
            providers=[self._execution_provider],
        )

        model_type = session.get_modelmeta().description

        if any(model_name in self._model_path for model_name in ULTRALYTICS_MODELS):
            self._model = self._load_ultralytics_yolo_model(session)
        elif "Polybius" in model_type:
            self._model = self._load_polybius_v1_model(session)
        elif "object_detection" in model_type:
            self._model = self._load_object_detection_model(session)
        else:
            self._model = self._load_legacy_model(session)

        return self._model, "ONNX model loaded."

    def _load_ultralytics_yolo_model(self, session: ort.InferenceSession) -> Model:
        """Load Ultralytics YOLO model."""
        inputs = session.get_inputs()
        outputs = session.get_outputs()

        model_description = session.get_modelmeta().description
        metadata_map = session.get_modelmeta().custom_metadata_map
        label_map_entries = []

        if "colors" in metadata_map:
            color_map = ast.literal_eval(metadata_map["colors"])
        else:
            color_map = None

        label_information = ast.literal_eval(metadata_map["names"])

        if isinstance(label_information, list):
            # For compatibility with both new and old versions of yolov8/9
            label_information = dict(enumerate(label_information))

        for label_id, label_name in label_information.items():
            if color_map is None or label_name not in color_map:
                color = get_color_for_label_id(label_id)
            else:
                color = color_map[label_name]

            label_map_entries.append(
                LabelMapEntry(
                    label_id=label_id,
                    name=label_name,
                    color=color,
                )
            )

        skeletons: Dict[str, Skeleton] = {}

        if "cls" in model_description:
            task_type = PredictionTaskType.IMAGE_CLASSIFICATION

        elif "seg" in model_description:
            task_type = PredictionTaskType.INSTANCE_SEGMENTATION

        elif "pose" in model_description:
            task_type = PredictionTaskType.KEYPOINT_DETECTION
            skeletons_json = ast.literal_eval(metadata_map["skeletons"])["skeletons"]
            for sk_name, sk_object in skeletons_json.items():
                if "name" not in sk_object:
                    sk_object["name"] = sk_name
                skeletons[sk_name] = Skeleton.from_json(sk_object)

            return KeypointModel(
                model=session,
                versions=[1],
                backend=ModelBackend.ONNX,
                task_type=task_type,
                model_type=ModelType.ULTRALYTICS,
                label_map=LabelMap(label_map_entries),
                inputs=list(map(_tensor_description_from_onnx_node_arg, inputs)),
                outputs=list(map(_tensor_description_from_onnx_node_arg, outputs)),
                skeletons=skeletons,
            )

        else:
            task_type = PredictionTaskType.OBJECT_DETECTION

        return Model(
            model=session,
            versions=[1],
            backend=ModelBackend.ONNX,
            task_type=task_type,
            model_type=ModelType.ULTRALYTICS,
            label_map=LabelMap(label_map_entries),
            inputs=list(map(_tensor_description_from_onnx_node_arg, inputs)),
            outputs=list(map(_tensor_description_from_onnx_node_arg, outputs)),
        )

    def _load_polybius_v1_model(self, session: ort.InferenceSession) -> Model:
        """Load Polybius v1 model."""
        inputs = session.get_inputs()
        outputs = session.get_outputs()

        if len(inputs) != 1:
            raise RuntimeError(
                f"Cannot load Polybius model having {len(inputs)} " "inputs, expected 1"
            )

        model_description = session.get_modelmeta().description

        model_version, prediction_type = [
            info.lower() for info in model_description.split("_", 1)[-1].split(".")
        ]

        if model_version != "v1":
            raise RuntimeError(
                f"Cannot load Polybius model with version {model_version}, "
                "expected 'v1'"
            )

        metadata_map = session.get_modelmeta().custom_metadata_map

        if "colors" in metadata_map:
            color_map = json.loads(metadata_map["colors"])
        else:
            color_map = None

        with open(self._label_map_path, "r", encoding="utf-8") as label_map_file:
            label_map = LabelMapFromPbtxt(label_map_file, color_map)

        return Model(
            model=session,
            versions=[1],
            backend=ModelBackend.ONNX,
            task_type=POLYBIUS_PREDICTION_TYPES[prediction_type],
            model_type=ModelType.POLYBIUS_V1,
            label_map=label_map,
            inputs=list(map(_tensor_description_from_onnx_node_arg, inputs)),
            outputs=list(map(_tensor_description_from_onnx_node_arg, outputs)),
        )

    def _load_object_detection_model(self, session: ort.InferenceSession) -> Model:
        """Load Tensorflow Object Detection model."""
        inputs = session.get_inputs()
        outputs = session.get_outputs()

        if len(inputs) != 1:
            raise RuntimeError(
                f"Cannot load Object Detection model having {len(inputs)} "
                "inputs, expected 1"
            )

        task_type = PredictionTaskType.OBJECT_DETECTION

        for output in outputs:
            if "masks" in output.name:
                task_type = PredictionTaskType.INSTANCE_SEGMENTATION
                break

        metadata_map = session.get_modelmeta().custom_metadata_map

        if "colors" in metadata_map:
            color_map = json.loads(metadata_map["colors"])
        else:
            color_map = None

        with open(self._label_map_path, "r", encoding="utf-8") as label_map_file:
            label_map = LabelMapFromPbtxt(label_map_file, color_map)

        return Model(
            model=session,
            versions=[1],
            backend=ModelBackend.ONNX,
            task_type=task_type,
            model_type=ModelType.OBJECT_DETECTION,
            label_map=label_map,
            inputs=list(map(_tensor_description_from_onnx_node_arg, inputs)),
            outputs=list(map(_tensor_description_from_onnx_node_arg, outputs)),
        )

    def _load_legacy_model(self, session: ort.InferenceSession) -> Model:
        """Load legacy model."""
        inputs = session.get_inputs()
        outputs = session.get_outputs()
        model_type = session.get_modelmeta().description

        if len(inputs) != 1:
            raise RuntimeError(
                f"Cannot load {model_type} model having {len(inputs)} "
                "inputs, expected 1"
            )

        if (
            model_type not in LEGACY_MODEL_ARCHITECTURES
            or model_type not in LEGACY_MODEL_TASK_TYPES
        ):
            raise RuntimeError(
                f"Cannot load {model_type} as legacy model, we have no "
                "knowledge of this model type"
            )

        metadata_map = session.get_modelmeta().custom_metadata_map
        if "colors" in metadata_map:
            color_map = json.loads(metadata_map["colors"])
        else:
            color_map = None

        with open(self._label_map_path, "r", encoding="utf-8") as label_map_file:
            label_map = LabelMapFromPbtxt(label_map_file, color_map)

        return Model(
            model=session,
            versions=[1],
            backend=ModelBackend.ONNX,
            model_type=LEGACY_MODEL_ARCHITECTURES[model_type],
            label_map=label_map,
            inputs=list(map(_tensor_description_from_onnx_node_arg, inputs)),
            outputs=list(map(_tensor_description_from_onnx_node_arg, outputs)),
            task_type=LEGACY_MODEL_TASK_TYPES[model_type],
        )
