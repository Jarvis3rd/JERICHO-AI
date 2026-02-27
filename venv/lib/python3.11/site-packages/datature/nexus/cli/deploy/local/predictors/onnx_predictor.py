#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   onnx_predictor.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   ONNX predictor class.
"""

# pylint: disable=R0911,R0914

from typing import Any

import cv2
import numpy as np
from scipy.ndimage import zoom

from datature.nexus.cli.deploy.local.predictors.base_predictor import BasePredictor
from datature.nexus.cli.deploy.local.utils.inference import (
    PredictionTaskType,
    TensorDtype,
)
from datature.nexus.cli.deploy.local.utils.postprocess import box_xywh2xyxyn, clamp, nms

DTYPE_MAPPING = {
    TensorDtype.FP16: np.float16,
    TensorDtype.FP32: np.float32,
    TensorDtype.FP64: np.float64,
    TensorDtype.UINT8: np.uint8,
    TensorDtype.UINT16: np.uint16,
    TensorDtype.UINT32: np.uint32,
    TensorDtype.UINT64: np.uint64,
    TensorDtype.INT8: np.int8,
    TensorDtype.INT16: np.int16,
    TensorDtype.INT32: np.int32,
    TensorDtype.INT64: np.int64,
    TensorDtype.BOOL: np.bool_,
}


class ONNXUltralyticsPredictor(BasePredictor):
    """ONNX predictor class for Ultralytics models."""

    def _predict(self, **kwargs) -> Any:
        """Predict on image."""
        if self._model.task_type == PredictionTaskType.INSTANCE_SEGMENTATION:
            raw_output = self._model.model.run(
                [output.name for output in self._model.outputs],
                {self._model.inputs[0].name: kwargs["model_input"]},
            )

        else:
            raw_output = self._model.model.run(
                [self._model.outputs[0].name],
                {self._model.inputs[0].name: kwargs["model_input"]},
            )

        return {"raw_output": raw_output}

    def _preprocess(self, **kwargs) -> Any:
        """Preprocess image for prediction compatibility."""
        image = kwargs["image"]
        input_shape = self._model.inputs[0].shape[2:]
        dtype = DTYPE_MAPPING[self._model.inputs[0].dtype]

        resized_image = cv2.resize(image, input_shape)
        preprocessed_image = resized_image.astype(dtype)
        preprocessed_image /= 255
        preprocessed_image = np.transpose(preprocessed_image, (2, 0, 1))
        preprocessed_image = np.expand_dims(preprocessed_image, axis=0)

        return {"model_input": preprocessed_image}

    def _postprocess(self, **kwargs) -> dict[str, Any]:
        """Postprocess raw model output into interpretable predictions."""
        if self._model.task_type == PredictionTaskType.IMAGE_CLASSIFICATION:
            return self._postprocess_image_classification(**kwargs)

        if self._model.task_type == PredictionTaskType.OBJECT_DETECTION:
            return self._postprocess_object_detection(**kwargs)

        if self._model.task_type == PredictionTaskType.INSTANCE_SEGMENTATION:
            return self._postprocess_instance_segmentation(**kwargs)

        if self._model.task_type == PredictionTaskType.KEYPOINT_DETECTION:
            return self._postprocess_keypoint_detection(**kwargs)

        raise ValueError("Task type not supported")

    def _postprocess_image_classification(self, **kwargs) -> dict[str, Any]:
        """Postprocess classification outputs."""
        prediction = kwargs["raw_output"][0][0]

        scores = np.max(prediction)
        classes = np.argmax(prediction)
        scores = np.expand_dims(scores, axis=0).astype(np.float32)
        classes_int32 = np.expand_dims(classes, axis=0).astype(np.int32)

        postprocessed_output = {
            "classes": classes_int32,
            "scores": scores,
        }

        return postprocessed_output

    def _postprocess_object_detection(self, **kwargs) -> dict[str, Any]:
        """Postprocess object detection outputs."""
        # Take only the first batch
        prediction = kwargs["raw_output"][0][0]

        num_classes = len(self.model.label_map)

        mask_index = 4 + num_classes
        candidates = prediction[4:mask_index].max(0) > 0.05

        prediction = prediction.transpose()[candidates]

        if len(prediction) == 0:
            return {
                "classes": np.ndarray(0, dtype=np.int32),
                "scores": np.ndarray(0, dtype=np.float32),
                "boxes": np.ndarray((0, 4), dtype=np.float32),
            }

        boxes = prediction[..., :4]

        class_end = 4 + num_classes
        score_classes = prediction[..., 4:class_end]
        scores = np.max(score_classes, axis=1)
        classes = np.argmax(score_classes, axis=1).astype(np.int32)

        if len(boxes) == 0:
            return {
                "classes": np.ndarray(0, dtype=np.int32),
                "scores": np.ndarray(0, dtype=np.float32),
                "boxes": np.ndarray((0, 4), dtype=np.float32),
            }

        filtered_boxes, filtered_classes, filtered_scores, _, _, _ = nms(
            boxes, classes, scores, iou_threshold=0.7
        )

        input_shape = self._model.inputs[0].shape[2:]
        filtered_boxes_xyxyn = box_xywh2xyxyn(
            filtered_boxes, input_shape[1], input_shape[0]
        )

        clamped_boxes = [
            [
                clamp(box[1]),
                clamp(box[0]),
                clamp(box[3]),
                clamp(box[2]),
            ]
            for box in filtered_boxes_xyxyn
        ]

        postprocessed_output = {
            "classes": filtered_classes,
            "scores": filtered_scores,
            "boxes": clamped_boxes,
        }

        return postprocessed_output

    def _postprocess_instance_segmentation(self, **kwargs) -> dict[str, Any]:
        """Postprocess instance segmentation outputs."""
        prediction = kwargs["raw_output"][0][0]
        proto = kwargs["raw_output"][1][0]

        num_classes = len(self.model.label_map)

        mask_index = 4 + num_classes
        candidates = prediction[4:mask_index].max(0) > 0.05

        prediction = prediction.transpose()[candidates]

        if len(prediction) == 0:
            return {
                "classes": np.ndarray(0, dtype=np.int32),
                "scores": np.ndarray(0, dtype=np.float32),
                "boxes": np.ndarray((0, 4), dtype=np.float32),
                "masks": np.ndarray(0, dtype=np.float32),
            }

        num_extras = prediction.shape[1] - num_classes - 4
        boxes = prediction[..., :4]
        class_end = 4 + num_classes
        score_classes = prediction[..., 4:class_end]
        masks = prediction[..., class_end : class_end + num_extras]

        scores = np.max(score_classes, axis=1)
        classes = np.argmax(score_classes, axis=1).astype(np.int32)

        # Perform the below only for yolov8seg models.
        channels, mask_height, mask_width = proto.shape
        masks = masks @ proto.astype(np.float32).reshape(channels, -1)
        masks = 1 / (1 + np.exp(-1 * masks))  # use -1*mask over -mask to avoid overflow

        masks = masks.reshape(-1, mask_height, mask_width)
        binary_masks = np.where(masks > 0.1, np.uint8(1), np.uint8(0))

        if len(boxes) == 0:
            return {
                "classes": np.ndarray(0, dtype=np.int32),
                "scores": np.ndarray(0, dtype=np.float32),
                "boxes": np.ndarray((0, 4), dtype=np.float32),
                "masks": np.ndarray(0, dtype=np.float32),
            }

        (
            filtered_boxes,
            filtered_classes,
            filtered_scores,
            filtered_masks,
            _,
            _,
        ) = nms(boxes, classes, scores, masks=binary_masks, iou_threshold=0.7)

        input_shape = self._model.inputs[0].shape[2:]
        filtered_boxes_xyxyn = box_xywh2xyxyn(
            filtered_boxes, input_shape[0], input_shape[1]
        )

        clamped_boxes = [
            [clamp(vertex) for vertex in box] for box in filtered_boxes_xyxyn
        ]

        postprocessed_output = {
            "classes": filtered_classes,
            "scores": filtered_scores,
            "boxes": clamped_boxes,
            "masks": filtered_masks,
        }

        return postprocessed_output

    def _postprocess_keypoint_detection(self, **kwargs) -> dict[str, Any]:
        """Postprocess keypoint detection outputs."""
        prediction = kwargs["raw_output"][0][0]

        num_classes = len(self.model.label_map)

        keypoints_index = 4 + num_classes
        candidates = prediction[4:keypoints_index].max(0) > 0.05

        prediction = prediction.transpose()[candidates]

        if len(prediction) == 0:
            return {
                "classes": np.ndarray(0, dtype=np.int32),
                "scores": np.ndarray(0, dtype=np.float32),
                "boxes": np.ndarray((0, 4), dtype=np.float32),
                "keypoints": np.ndarray((0, 3), dtype=np.float32),
                "keypoint_confidences": np.ndarray((0, 3), dtype=np.float32),
            }

        num_extras = prediction.shape[1] - num_classes - 4
        boxes = prediction[..., :4]
        class_end = 4 + num_classes
        score_classes = prediction[..., 4:class_end]
        keypoints = prediction[..., class_end : class_end + num_extras]

        scores = np.max(score_classes, axis=1)
        classes = np.argmax(score_classes, axis=1).astype(np.int32)

        # Perform the below only for yolov8pose models
        input_shape = self._model.inputs[0].shape[2:]
        keypoints = keypoints.reshape(len(scores), -1, 3)
        keypoints[..., 0] /= input_shape[1]
        keypoints[..., 1] /= input_shape[0]

        keypoint_confidences = keypoints[..., 2].copy()

        keypoints[..., 2] = np.where(
            np.any(keypoints[..., :2] > 1.0, axis=-1)
            | np.any(keypoints[..., :2] < 0.0, axis=-1),
            0,
            2,
        )

        (
            filtered_boxes,
            filtered_classes,
            filtered_scores,
            _,
            filtered_keypoints,
            filtered_keypoint_confidences,
        ) = nms(
            boxes,
            classes,
            scores,
            keypoints=keypoints,
            keypoint_confidences=keypoint_confidences,
            iou_threshold=0.7,
        )

        filtered_boxes_xyxyn = box_xywh2xyxyn(
            filtered_boxes, input_shape[1], input_shape[0]
        )

        clamped_boxes = [
            [
                clamp(box[0]),
                clamp(box[1]),
                clamp(box[2]),
                clamp(box[3]),
            ]
            for box in filtered_boxes_xyxyn
        ]

        postprocessed_output = {
            "classes": filtered_classes,
            "scores": filtered_scores,
            "boxes": clamped_boxes,
            "keypoints": filtered_keypoints,
            "keypoint_confidences": filtered_keypoint_confidences,
        }

        return postprocessed_output


class ONNXClassificationPredictor(BasePredictor):
    """ONNX predictor class for classification models."""

    def _predict(self, **kwargs) -> Any:
        """Predict on image."""
        raw_output = self._model.model.run(
            [self._model.outputs[0].name],
            {self._model.inputs[0].name: kwargs["model_input"]},
        )
        return {"raw_output": raw_output}

    def _preprocess(self, **kwargs) -> Any:
        """Preprocess image for prediction compatibility."""
        image = kwargs["image"]
        input_shape = self._model.inputs[0].shape[1:3]
        dtype = DTYPE_MAPPING[self._model.inputs[0].dtype]

        resized_image = cv2.resize(image, input_shape)
        preprocessed_image = resized_image.astype(dtype)
        preprocessed_image = np.expand_dims(preprocessed_image, axis=0)

        return {"model_input": preprocessed_image}

    def _postprocess(self, **kwargs) -> dict[str, Any]:
        """Postprocess raw model output into interpretable predictions."""
        prediction = kwargs["raw_output"][0][0]

        probs = prediction.flatten()
        label = np.argmax(probs)
        score = max(probs)

        return {
            "classes": np.array([label]),
            "scores": np.array([score]),
        }


class ONNXObjectDetectionPredictor(BasePredictor):
    """ONNX predictor class for Tensorflow Object Detection models."""

    def _predict(self, **kwargs) -> Any:
        """Predict on image."""
        raw_output = self._model.model.run(
            [self._model.outputs[0].name],
            {self._model.inputs[0].name: kwargs["model_input"]},
        )
        return {"raw_output": raw_output}

    def _preprocess(self, **kwargs) -> Any:
        """Preprocess image for prediction compatibility."""
        image = kwargs["image"]
        input_shape = self._model.inputs[0].shape[1:3]
        dtype = DTYPE_MAPPING[self._model.inputs[0].dtype]

        resized_image = cv2.resize(image, input_shape)
        preprocessed_image = resized_image.astype(dtype)
        preprocessed_image = np.expand_dims(preprocessed_image, axis=0)

        return {"model_input": preprocessed_image}

    def _postprocess(self, **kwargs) -> dict[str, Any]:
        """Postprocess raw model output into interpretable predictions."""
        prediction = kwargs["raw_output"][0][0]
        slicer = prediction[:, -1]
        output = prediction[:, :6][slicer != 0]

        if len(output) == 0:
            return {
                "classes": np.array([]),
                "scores": np.array([]),
                "boxes": np.array([]),
            }

        scores = output[:, 4]
        classes = output[:, 5]
        output = output[classes != 0]

        # Postprocess detections
        input_shape = self._model.inputs[0].shape[1:3]

        boxes = output[:, :4]
        classes = output[:, 5].astype(np.int32)
        scores = output[:, 4]
        boxes[:, 0], boxes[:, 1] = (
            boxes[:, 1] * input_shape[0],
            boxes[:, 0] * input_shape[1],
        )
        boxes[:, 2], boxes[:, 3] = (
            boxes[:, 3] * input_shape[0],
            boxes[:, 2] * input_shape[1],
        )

        boxes = boxes.astype(np.float32)
        scores = scores.astype(np.float32)
        filtered_boxes, filtered_classes, filtered_scores, _, _, _ = nms(
            boxes, classes, scores, iou_threshold=0.1
        )

        clamped_boxes = [
            [
                clamp(bbox[1] / input_shape[0]),
                clamp(bbox[0] / input_shape[1]),
                clamp(bbox[3] / input_shape[0]),
                clamp(bbox[2] / input_shape[1]),
            ]
            for bbox in filtered_boxes
        ]  # y1, x1, y2, x2

        postprocessed_output = {
            "classes": filtered_classes,
            "scores": filtered_scores,
            "boxes": clamped_boxes,
        }

        return postprocessed_output


class ONNXSegmentationPredictor(BasePredictor):
    """ONNX predictor class for segmentation models."""

    def _predict(self, **kwargs) -> Any:
        """Predict on image."""
        model_input_names = list(map(lambda _input: _input.name, self._model.inputs))
        model_output_names = list(
            map(lambda _output: _output.name, self._model.outputs)
        )

        raw_output = self._model.model.run(
            model_output_names,
            dict(zip(model_input_names, kwargs["model_input"])),
        )

        return {"raw_output": raw_output}

    def _preprocess(self, **kwargs) -> Any:
        """Preprocess image for prediction compatibility."""
        image = kwargs["image"]
        input_shape = self._model.inputs[0].shape[1:3]
        dtype = DTYPE_MAPPING[self._model.inputs[0].dtype]

        resized_image = cv2.resize(image, input_shape)
        preprocessed_image = resized_image.astype(dtype)
        preprocessed_image = np.expand_dims(preprocessed_image, axis=0)

        return {"model_input": [preprocessed_image]}

    def _postprocess(self, **kwargs) -> dict[str, Any]:
        """Postprocess raw model output into interpretable predictions."""
        if self._model.task_type == PredictionTaskType.INSTANCE_SEGMENTATION:
            return self._postprocess_instance_segmentation(**kwargs)

        if self._model.task_type == PredictionTaskType.SEMANTIC_SEGMENTATION:
            return self._postprocess_semantic_segmentation(**kwargs)

        raise ValueError(f"Unsupported task type: {self._model.task_type}")

    def _postprocess_instance_segmentation(self, **kwargs) -> dict[str, Any]:
        """Postprocess instance segmentation outputs."""
        _, scores, classes, boxes, masks = kwargs["raw_output"]
        scores = scores[0]
        classes = classes[0].astype(np.int16)
        boxes = boxes[0]
        masks = masks[0]

        postprocessed_output = {
            "classes": classes,
            "scores": scores,
            "boxes": boxes,
            "masks": masks,
        }

        return postprocessed_output

    def _postprocess_semantic_segmentation(self, **kwargs) -> dict[str, Any]:
        """Postprocess semantic segmentation outputs."""
        prediction = kwargs["raw_output"][0][0]

        # Get confidence masks for each class
        confidence_mask = (prediction - np.min(prediction)) / (
            np.max(prediction) - np.min(prediction)
        )

        # Get confidence scores and predicted class for each pixel in the mask
        scores = np.max(confidence_mask, axis=0)
        class_mask = np.argmax(confidence_mask, axis=0)

        postprocessed_output = {
            "masks": class_mask.astype(np.uint8),
            "scores": scores,
        }

        return postprocessed_output


class ONNXSemantic3DSegmentationPredictor(BasePredictor):
    """ONNX predictor class for semantic 3D segmentation models."""

    def _predict(self, **kwargs) -> Any:
        """Predict on image."""
        model_input_names = list(map(lambda _input: _input.name, self._model.inputs))
        model_output_names = list(
            map(lambda _output: _output.name, self._model.outputs)
        )

        raw_output = self._model.model.run(
            model_output_names,
            dict(zip(model_input_names, kwargs["model_input"])),
        )

        return {
            "raw_output": raw_output,
            "image_shape": kwargs["image_shape"],
        }

    def _preprocess(self, **kwargs) -> Any:
        """Preprocess image for prediction compatibility."""
        image = kwargs["image"]
        input_shape = self._model.inputs[0].shape[1:4]
        dtype = DTYPE_MAPPING[self._model.inputs[0].dtype]

        zoom_factors = [input_shape[i] / image.shape[i] for i in range(3)]
        resized = zoom(image, zoom_factors, order=1)
        preprocessed_image = np.array(resized).astype(dtype)
        preprocessed_image = np.expand_dims(preprocessed_image, axis=0)

        return {
            "model_input": [preprocessed_image],
            "image_shape": image.shape,
        }

    def _postprocess(self, **kwargs) -> dict[str, Any]:
        """Postprocess raw model output into interpretable predictions."""
        prediction = kwargs["raw_output"][0][0]

        confidence_mask = (prediction - np.min(prediction)) / (
            np.max(prediction) - np.min(prediction)
        )

        scores = np.max(confidence_mask, axis=0)
        predicted_mask = np.argmax(confidence_mask, axis=0)

        postprocessed_output = {
            "masks": predicted_mask.astype(np.uint8),
            "scores": scores,
        }

        return postprocessed_output
