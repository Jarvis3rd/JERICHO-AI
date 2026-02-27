#!/usr/env/bin python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   predictor.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   TensorRT predictor module.
"""

# pylint: disable=E1121,R0902,R0903,R0913,R0914

import glob
import os
from abc import ABC, abstractmethod
from typing import Dict, Tuple

import cv2
import numpy as np

try:
    import tritonclient.http as httpclient
except ImportError as import_exc:
    raise ModuleNotFoundError(
        "Triton Inference Server not installed! "
        "Please visit https://developers.datature.io/docs/tensorrt-export "
        "to learn how to set up your environment."
    ) from import_exc
from PIL import Image

from .logger import trt_logger
from .prediction_utils import (
    clamp,
    draw_bboxes,
    draw_class_labels,
    draw_instance_masks,
    draw_keypoints,
    draw_semantic_masks,
    draw_yolov8_instance_masks,
    get_model_config,
    load_label_map,
    load_skeleton,
    nms_boxes,
    postprocess_predictions,
    xywh2xyxy,
)

# Default Triton Inference Server URL
# if not set, it will default to localhost:8000
TRITON_DEFAULT_URL = "localhost:8000"


class BasePredictor(ABC):
    """Base class for all predictors"""

    def __init__(
        self,
        dtype: str,
        input_path: str,
        model_name: str,
        label_map_path: str,
        threshold: float = 0.7,
        save: bool = True,
        output_path: str = "",
        **kwargs,
    ) -> None:
        """Initialize the predictor.

        Args:
            dtype (str): The data type of the input image.
            input_path (str): The path to the input image.
            model_name (str): The name of the model.
            label_map_path (str): The path to the label map.
            threshold (float): The confidence threshold for object detection, defaults to 0.7.
            save (bool): Whether to save the output, defaults to True.
            output_path (str): The path to the output directory, defaults to "".
        """
        self._dtype = dtype
        self._input_path = input_path
        self._model_name = model_name
        self._label_map_path = label_map_path
        self._skeleton_file_path = kwargs.get("skeleton_file_path")
        self._threshold = threshold
        self._save = save
        self._output_path = output_path
        self._model_config = get_model_config(self._model_name)
        trt_logger.debug("Model config:")
        trt_logger.debug(self._model_config)

        self._triton_client = httpclient.InferenceServerClient(url=TRITON_DEFAULT_URL)

        ## Load label map
        self._category_index = load_label_map(self._label_map_path)

        ## Load color map
        self._color_map = {}
        for each_class in self._category_index:
            self._color_map[each_class] = np.array(
                [int(i) for i in np.random.choice(range(256), size=3)], dtype=np.uint8
            )
        self._color_map[0] = np.array([0, 0, 0], dtype=np.uint8)

    @abstractmethod
    def __call__(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def _preprocess(self, path: str) -> np.ndarray:
        raise NotImplementedError

    @abstractmethod
    def _postprocess(self, response_outputs, num_classes: int):
        raise NotImplementedError

    @abstractmethod
    def _run_inference_client(self, model_input: np.ndarray) -> Dict:
        raise NotImplementedError

    def _predict(self, image: np.ndarray) -> Tuple[np.ndarray]:
        """Send an image for prediction, then process it to be returned
        afterwards.

        Args:
            image (np.ndarray): The image to be predicted.

        Returns:
            Tuple[np.ndarray]: Prediction outputs.
        """
        preprocessed = self._preprocess(image)
        predicted = self._run_inference_client(preprocessed)
        postprocessed = self._postprocess(predicted, len(self._category_index))
        return postprocessed


class ImagePredictor(BasePredictor):
    """Generic model predictor for image tasks"""

    def __init__(
        self,
        dtype: str,
        input_path: str,
        model_name: str,
        label_map_path: str,
        threshold: float = 0.7,
        save: bool = True,
        output_path: str = "",
        **kwargs,
    ) -> None:
        super().__init__(
            dtype=dtype,
            input_path=input_path,
            model_name=model_name,
            label_map_path=label_map_path,
            threshold=threshold,
            save=save,
            output_path=output_path,
            **kwargs,
        )
        self._input_shape = [1] + self._model_config["input"][0]["dims"]
        self._input_names = [input["name"] for input in self._model_config["input"]]
        self._output_names = [output["name"] for output in self._model_config["output"]]
        self._output_shapes = [
            output["dims"] for output in self._model_config["output"]
        ]

    def _run_inference_client(self, model_input: np.ndarray) -> Dict:
        """Run inference using the Triton Inference Server client.

        Args:
            model_input (np.ndarray): The model input array.

        Returns:
            Dict: The model response outputs.
        """
        inputs = [
            httpclient.InferInput(input_name, self._input_shape, datatype="FP32")
            for input_name in self._input_names
        ]
        for inp in inputs:
            inp.set_data_from_numpy(model_input, binary_data=True)
        request_outputs = [
            httpclient.InferRequestedOutput(output_name, binary_data=True)
            for output_name in self._output_names
        ]
        response_outputs = self._triton_client.infer(
            model_name=self._model_name, inputs=inputs, outputs=request_outputs
        )
        return response_outputs


class ObjectDetectionPredictor(ImagePredictor):
    """Tensorflow Object Detection model predictor"""

    def __call__(self) -> None:
        for each_image in glob.glob(os.path.join(self._input_path, "*")):
            trt_logger.info("Predicting for %s ...", each_image)
            if not each_image.endswith((".jpg", ".jpeg", ".png")):
                continue

            scores, classes, bboxes = self._predict(each_image)

            if self._save:
                image_origi = cv2.imread(each_image)
                for box, class_id, score in zip(bboxes, classes, scores):
                    image_origi = draw_bboxes(
                        image_origi,
                        box,
                        class_id,
                        score,
                        self._color_map,
                        self._category_index,
                    )

                ## Save predicted image
                image_name = os.path.basename(each_image)
                specific_output_path = os.path.join(self._output_path, image_name)
                cv2.imwrite(specific_output_path, image_origi)
                trt_logger.info("Prediction saved to %s", specific_output_path)

    def _preprocess(self, path: str) -> np.ndarray:
        """Load and preprocess the image array before it is fed to the model.

        Args:
            path (str): The path to the image file.

        Returns:
            np.ndarray: The preprocessed image array.
        """
        image = Image.open(path).convert("RGB")
        image = image.resize((self._input_shape[1], self._input_shape[2]))
        model_input = np.array(image).astype(self._dtype)
        model_input = np.expand_dims(model_input, 0)
        return model_input

    def _postprocess(self, response_outputs, _) -> np.ndarray:
        """Postprocess the model output.

        Args:
            response_outputs (Dict): The model response outputs.
            num_classes (int): The number of classes in the model.

        Returns:
            Tuple[np.ndarray]: The postprocessed model output
                containing scores, classes, and boxes.
        """
        boxes = response_outputs.as_numpy("detection_boxes")[0]
        classes = response_outputs.as_numpy("detection_classes")[0]
        scores = response_outputs.as_numpy("detection_scores")[0]

        fltr = scores >= self._threshold
        boxes = boxes[fltr]
        classes = classes[fltr]
        scores = scores[fltr]

        if len(boxes) == 0:
            return np.array([]), np.array([]), np.array([])
        return scores, classes, boxes


class MaskPredictor(ImagePredictor):
    """Instance segmentation predictor"""

    _input_name: str = "inputs"

    def __call__(self) -> None:
        for each_image in glob.glob(os.path.join(self._input_path, "*")):
            trt_logger.info("Predicting for %s ...", each_image)
            if not each_image.endswith((".jpg", ".jpeg", ".png")):
                continue

            scores, classes, bboxes, masks = self._predict(each_image)

            if self._save:
                image_origi = cv2.imread(each_image)
                for box, mask, class_id, score in zip(bboxes, masks, classes, scores):
                    image_origi = draw_instance_masks(
                        image_origi,
                        box,
                        mask,
                        class_id,
                        self._color_map,
                        self._category_index,
                    )
                    image_origi = draw_bboxes(
                        image_origi,
                        box,
                        class_id,
                        score,
                        self._color_map,
                        self._category_index,
                    )

                ## Save predicted image
                image_name = os.path.basename(each_image)
                specific_output_path = os.path.join(self._output_path, image_name)
                cv2.imwrite(specific_output_path, image_origi)
                trt_logger.info("Prediction saved to %s", specific_output_path)

    def _preprocess(self, path: str) -> np.ndarray:
        """Load and preprocess the image array before it is fed to the model.

        Args:
            path (str): The path to the image file.

        Returns:
            np.ndarray: The preprocessed image array.
        """
        img = Image.open(os.path.join(path)).convert("RGB")
        model_input = img.resize((self._input_shape[1], self._input_shape[2]))
        model_input = np.array(model_input).astype(np.float32)
        model_input = np.expand_dims(model_input, 0)
        return model_input

    def _postprocess(self, response_outputs, _) -> np.ndarray:
        """Postprocess the model output.

        Args:
            response_outputs (Dict): The model response outputs.
            num_classes (int): The number of classes in the model.

        Returns:
            Tuple[np.ndarray]: The postprocessed model output
                containing scores, classes, boxes, and masks.
        """
        preds = []
        for output_name in self._output_names:
            output = response_outputs.as_numpy(output_name)
            preds.append(output)
        _, boxes, scores, classes, masks = preds
        scores = scores[0]
        classes = classes[0].astype(np.int16)
        boxes = boxes[0]
        masks = masks[0]
        _filter = np.where(scores > self._threshold)
        scores = scores[_filter]
        classes = classes[_filter]
        boxes = boxes[_filter]
        boxes = [
            [
                clamp(box[0]),
                clamp(box[1]),
                clamp(box[2]),
                clamp(box[3]),
            ]
            for box in boxes
        ]

        masks = masks[_filter]
        masks_output = []
        for each_mask in masks:
            instance_mask = np.zeros_like(each_mask, np.uint8)
            instance_mask[np.where(each_mask > self._threshold)] = 1
            masks_output.append(instance_mask)

        if masks_output:
            masks_output = np.stack(masks_output)
        else:
            masks_output = None
        return scores, classes, boxes, masks_output


class SemanticPredictor(ImagePredictor):
    """Semantic segmentation predictor"""

    def __call__(self) -> None:
        for each_image in glob.glob(os.path.join(self._input_path, "*")):
            trt_logger.info("Predicting for %s ...", each_image)
            if not each_image.endswith((".jpg", ".jpeg", ".png")):
                continue

            mask = self._predict(each_image)
            if mask is None:
                trt_logger.info("No detections for %s", each_image)
                continue

            if self._save:
                image_origi = cv2.imread(each_image)
                image_origi = draw_semantic_masks(
                    image_origi,
                    mask,
                    self._color_map,
                )

                ## Save predicted image
                image_name = os.path.basename(each_image)
                specific_output_path = os.path.join(self._output_path, image_name)
                cv2.imwrite(specific_output_path, image_origi)
                trt_logger.info("Prediction saved to %s", specific_output_path)

    def _preprocess(self, path: str) -> np.ndarray:
        """Load and preprocess the image array before it is fed to the model

        Args:
            path (str): The path to the image file.

        Returns:
            np.ndarray: The preprocessed image array.
        """
        img = Image.open(os.path.join(path)).convert("RGB")
        model_input = img.resize((self._input_shape[1], self._input_shape[2]))
        model_input = np.array(model_input).astype(np.float32)
        model_input = np.expand_dims(model_input, 0)
        return model_input

    def _postprocess(self, response_outputs, _) -> np.ndarray:
        """Postprocess the model output

        Args:
            response_outputs (Dict): The model response outputs.

        Returns:
            np.ndarray: The postprocessed model output
                containing the semantic mask.
        """
        mask = response_outputs.as_numpy(self._output_names[0])[0]
        binary_mask = np.zeros_like(mask[0], np.uint8)
        mask = (mask - np.min(mask)) / (np.max(mask) - np.min(mask))
        for class_id, class_mask in enumerate(mask):
            if class_id > 0:
                binary_mask[np.where(class_mask > self._threshold)] = class_id
        return binary_mask


class YOLOv8Predictor(ImagePredictor):
    """Base class for YOLOv8 predictors"""

    def _preprocess(self, path: str) -> np.ndarray:
        """Load and preprocess the image array before it is fed to the model.

        Args:
            path (str): The path to the image file.

        Returns:
            np.ndarray: The preprocessed image array.
        """
        image = Image.open(path).convert("RGB")
        image = image.resize((self._input_shape[2], self._input_shape[3]))
        model_input = np.array(image).astype(self._dtype)
        model_input = np.transpose(model_input, (2, 0, 1))
        model_input = np.expand_dims(model_input, 0)
        model_input = model_input / 255.0
        return model_input


class YOLOv8BoxPredictor(YOLOv8Predictor):
    """YOLOv8 bounding box predictor"""

    def __call__(self) -> None:
        for each_image in glob.glob(os.path.join(self._input_path, "*")):
            trt_logger.info("Predicting for %s ...", each_image)
            if not each_image.endswith((".jpg", ".jpeg", ".png")):
                continue

            scores, classes, bboxes = self._predict(each_image)

            if self._save:
                image_origi = cv2.imread(each_image)
                for box, class_id, score in zip(bboxes, classes, scores):
                    image_origi = draw_bboxes(
                        image_origi,
                        box,
                        class_id,
                        score,
                        self._color_map,
                        self._category_index,
                    )

                ## Save predicted image
                image_name = os.path.basename(each_image)
                specific_output_path = os.path.join(self._output_path, image_name)
                cv2.imwrite(specific_output_path, image_origi)
                trt_logger.info("Prediction saved to %s", specific_output_path)

    def _postprocess(self, response_outputs, num_classes: int) -> Tuple[np.ndarray]:
        """Postprocess the model output.

        Args:
            response_outputs (Dict): The model response outputs.
            num_classes (int): The number of classes in the model.

        Returns:
            Tuple[np.ndarray]: The postprocessed model output
                containing scores, classes, and boxes.
        """
        preds = []
        for output_name in self._output_names:
            output = response_outputs.as_numpy(output_name)[0]
            preds.append(output)
        prediction = preds[0]

        if len(prediction) == 0:
            return np.array([]), np.array([]), np.array([])

        mask_index = 4 + num_classes
        candidates = prediction[4:mask_index].max(0) > 0.05
        prediction = prediction.transpose()[candidates]

        scores, classes, boxes, _ = postprocess_predictions(prediction, num_classes)

        if len(boxes) > 0:
            boxes, classes, scores, _, _, _ = nms_boxes(
                boxes, classes, scores, 0.7, self._dtype
            )
            boxes = xywh2xyxy(boxes, self._input_shape[2], self._input_shape[3])
        fltr = scores > self._threshold
        scores = scores[fltr]
        boxes = boxes[fltr]
        classes = classes[fltr]
        boxes = [
            [
                clamp(box[1]),
                clamp(box[0]),
                clamp(box[3]),
                clamp(box[2]),
            ]
            for box in boxes
        ]  # yxyx
        return scores, classes, boxes


class YOLOv8MaskPredictor(YOLOv8Predictor):
    """YOLOv8 instance mask predictor"""

    def __call__(self) -> None:
        for each_image in glob.glob(os.path.join(self._input_path, "*")):
            trt_logger.info("Predicting for %s ...", each_image)
            if not each_image.endswith((".jpg", ".jpeg", ".png")):
                continue

            scores, classes, bboxes, masks = self._predict(each_image)

            if self._save:
                image_origi = cv2.imread(each_image)
                for box, mask, class_id, score in zip(bboxes, masks, classes, scores):
                    image_origi = draw_yolov8_instance_masks(
                        image_origi,
                        box,
                        mask,
                        class_id,
                        self._color_map,
                        self._category_index,
                    )
                    image_origi = draw_bboxes(
                        image_origi,
                        box,
                        class_id,
                        score,
                        self._color_map,
                        self._category_index,
                    )

                ## Save predicted image
                image_name = os.path.basename(each_image)
                specific_output_path = os.path.join(self._output_path, image_name)
                cv2.imwrite(specific_output_path, image_origi)
                trt_logger.info("Prediction saved to %s", specific_output_path)

    def _postprocess(self, response_outputs, num_classes: int) -> Tuple[np.ndarray]:
        """Postprocess the model output.

        Args:
            response_outputs (Dict): The model response outputs.
            num_classes (int): The number of classes in the model.

        Returns:
            Tuple[np.ndarray]: The postprocessed model output containing
                scores, classes, boxes, and masks.
        """
        preds = []
        for output_name in self._output_names:
            output = response_outputs.as_numpy(output_name)
            preds.append(output)

        protos = preds[0]
        predictions = preds[1]

        # Take only the first batch
        proto = protos[0]
        prediction = predictions[0]

        mask_index = 4 + num_classes
        candidates = prediction[4:mask_index].max(0) > 0.05
        prediction = prediction.transpose()[candidates]

        if len(prediction) == 0:
            return (
                np.ndarray(0, dtype=np.int32),
                np.ndarray(0, dtype=np.float32),
                np.ndarray((0, 4), dtype=np.float32),
                np.ndarray(0, dtype=np.float32),
            )

        scores, classes, boxes, masks = postprocess_predictions(prediction, num_classes)

        # Perform the below only for yolov8seg models.
        channels, mask_height, mask_width = proto.shape
        masks = masks @ proto.astype(np.float64).reshape(channels, -1)
        masks = 1 / (1 + np.exp(-1 * masks))  # use -1*mask over -mask to avoid overflow

        masks = masks.reshape(-1, mask_height, mask_width)
        binary_masks = np.where(masks > 0.1, np.uint8(1), np.uint8(0))

        if len(boxes) > 0:
            boxes, classes, scores, binary_masks, _, _ = nms_boxes(
                boxes, classes, scores, 0.7, self._dtype, binary_masks
            )
            boxes = xywh2xyxy(boxes, self._input_shape[2], self._input_shape[3])

        # Filter out low confidence predictions and prepare boxes for drawing
        fltr = scores > self._threshold
        scores = scores[fltr]
        boxes = boxes[fltr]
        classes = classes[fltr]
        binary_masks = binary_masks[fltr]
        boxes = [
            [
                clamp(box[1]),
                clamp(box[0]),
                clamp(box[3]),
                clamp(box[2]),
            ]
            for box in boxes
        ]  # y1, x1, y2, x2

        return scores, classes, boxes, binary_masks


class YOLOv8PosePredictor(YOLOv8Predictor):
    """YOLOv8 pose predictor"""

    def __call__(self) -> None:
        skeletons = load_skeleton(self._skeleton_file_path)

        for each_image in glob.glob(os.path.join(self._input_path, "*")):
            trt_logger.info("Predicting for %s ...", each_image)
            if not each_image.endswith((".jpg", ".jpeg", ".png")):
                continue

            _, classes, _, keypoints, keypoint_confidences = self._predict(each_image)

            if self._save:
                image_origi = cv2.imread(each_image)
                for keypoint, keypoint_confidence, class_id in zip(
                    keypoints, keypoint_confidences, classes
                ):
                    image_origi = draw_keypoints(
                        image_origi,
                        keypoint,
                        keypoint_confidence,
                        class_id,
                        self._color_map,
                        self._category_index,
                        skeletons,
                    )

                ## Save predicted image
                image_name = os.path.basename(each_image)
                specific_output_path = os.path.join(self._output_path, image_name)
                cv2.imwrite(specific_output_path, image_origi)
                trt_logger.info("Prediction saved to %s", specific_output_path)

    def _postprocess(self, response_outputs, num_classes: int) -> Tuple[np.ndarray]:
        """Postprocess the model output.

        Args:
            response_outputs (Dict): The model response outputs.
            num_classes (int): The number of classes in the model.

        Returns:
            Tuple[np.ndarray]: The postprocessed model output containing
                scores, classes, boxes, keypoints, and keypoint confidences.
        """
        preds = []
        for output_name in self._output_names:
            output = response_outputs.as_numpy(output_name)[0]
            preds.append(output)

        # Take only the first batch
        prediction = preds[0]

        keypoints_index = 4 + num_classes
        candidates = prediction[4:keypoints_index].max(0) > 0.05

        prediction = prediction.transpose()[candidates]

        if len(prediction) == 0:
            return (
                np.ndarray(0, dtype=np.int32),
                np.ndarray(0, dtype=np.float32),
                np.ndarray((0, 4), dtype=np.float32),
                np.ndarray((0, 3), dtype=np.float32),
                np.ndarray((0, 3), dtype=np.float32),
            )

        scores, classes, boxes, keypoints = postprocess_predictions(
            prediction, num_classes
        )

        # Perform the below only for yolov8pose models
        keypoints = keypoints.reshape(len(scores), -1, 3)
        keypoints[..., 0] /= self._input_shape[3]
        keypoints[..., 1] /= self._input_shape[2]

        keypoint_confidences = keypoints[..., 2].copy()

        keypoints[..., 2] = np.where(
            np.any(keypoints[..., :2] > 1.0, axis=-1)
            | np.any(keypoints[..., :2] < 0.0, axis=-1),
            0,
            2,
        )

        if len(boxes) > 0:
            boxes, classes, scores, _, keypoints, keypoint_confidences = nms_boxes(
                boxes,
                classes,
                scores,
                0.7,
                self._dtype,
                keypoints=keypoints,
                keypoint_confs=keypoint_confidences,
            )
            boxes = xywh2xyxy(boxes, self._input_shape[2], self._input_shape[3])

        # Filter out low confidence predictions and prepare boxes for drawing
        fltr = scores > self._threshold
        scores = scores[fltr]
        classes = classes[fltr]
        boxes = boxes[fltr]
        keypoints = keypoints[fltr]
        keypoint_confidences = keypoint_confidences[fltr]

        return scores, classes, boxes, keypoints, keypoint_confidences


class YOLOv8ClassificationPredictor(YOLOv8Predictor):
    """YOLOv8 classification predictor"""

    def __call__(self) -> None:
        for each_image in glob.glob(os.path.join(self._input_path, "*")):
            trt_logger.info("Predicting for %s ...", each_image)
            if not each_image.endswith((".jpg", ".jpeg", ".png")):
                continue

            scores, classes = self._predict(each_image)

            if self._save:
                image_origi = cv2.imread(each_image)
                for class_id, score in zip(classes, scores):
                    image_origi = draw_class_labels(
                        image_origi,
                        class_id,
                        score,
                        self._color_map,
                        self._category_index,
                    )
                ## Save predicted image
                image_name = os.path.basename(each_image)
                specific_output_path = os.path.join(self._output_path, image_name)
                cv2.imwrite(specific_output_path, image_origi)
                trt_logger.info("Prediction saved to %s", specific_output_path)

    def _postprocess(self, response_outputs, _) -> Tuple[np.ndarray]:
        """Postprocess the model output.

        Args:
            response_outputs (Dict): The model response outputs.

        Returns:
            Tuple[np.ndarray]: The postprocessed model output containing
                scores and classes.
        """
        preds = []
        for output_name in self._output_names:
            output = response_outputs.as_numpy(output_name)[0]
            preds.append(output)

        pred = preds[0]
        score = np.max(pred)
        cls = np.argmax(pred)
        score = np.expand_dims(score, axis=0).astype(np.float32)
        cls = np.expand_dims(cls, axis=0).astype(np.int32)
        return score, cls


class VideoClassificationPredictor(BasePredictor):
    """Video classification predictor"""

    def __init__(
        self,
        dtype: str,
        input_path: str,
        model_name: str,
        label_map_path: str,
        threshold: float = 0.7,
        save: bool = True,
        output_path: str = "",
        **kwargs,
    ) -> None:
        super().__init__(
            dtype=dtype,
            input_path=input_path,
            model_name=model_name,
            label_map_path=label_map_path,
            threshold=threshold,
            save=save,
            output_path=output_path,
            **kwargs,
        )
        self._states = []
        self._input_index = 0
        for i, item in enumerate(self._model_config["input"]):
            if item["name"] == "image":
                input_state = httpclient.InferInput(
                    item["name"],
                    [1] + item["dims"],
                    datatype="FP32" if item["data_type"] == "TYPE_FP32" else "INT32",
                )
                self._input_shape = item["dims"]
                self._input_index = i
            else:
                input_state = httpclient.InferInput(
                    item["name"],
                    [1] + item["dims"],
                    datatype="FP32" if item["data_type"] == "TYPE_FP32" else "INT32",
                )
                input_state.set_data_from_numpy(
                    (
                        np.zeros(input_state.shape(), dtype=np.float32)
                        if item["data_type"] == "TYPE_FP32"
                        else np.zeros(input_state.shape(), dtype=np.int32)
                    ),
                    binary_data=True,
                )
            self._states.append(input_state)
        self._outputs = [
            httpclient.InferRequestedOutput(output["name"], binary_data=True)
            for output in self._model_config["output"]
        ]
        self._output_name = "output_1"

    def __call__(self) -> None:
        for each_video in glob.glob(os.path.join(self._input_path, "*")):
            trt_logger.info("Predicting for %s ...", each_video)
            pred_label, conf = self._predict(each_video)
            trt_logger.info("Prediction: %s", pred_label)
            trt_logger.info("Confidence score: %s", conf)

    def _run_inference_client(self, model_input: np.ndarray) -> Dict:
        """Run inference using the Triton Inference Server client.

        Args:
            model_input (np.ndarray): The model input array.

        Returns:
            Dict: The model response outputs.
        """
        all_logits = None
        for clip in model_input:
            self._states[self._input_index].set_data_from_numpy(
                clip.astype(np.float32), binary_data=True
            )

            response_outputs = self._triton_client.infer(
                model_name=self._model_name,
                inputs=self._states,
                outputs=self._outputs,
            )

            for state in self._states:
                result = response_outputs.as_numpy(state.name())
                if result is not None:
                    state.set_data_from_numpy(
                        result,
                        binary_data=True,
                    )
            logits = response_outputs.as_numpy(self._output_name)
            all_logits = logits
        return all_logits

    def _preprocess(self, path: str) -> np.ndarray:
        """Load video and sample frames.

        Args:
            path (str): The path to the video file.

        Returns:
            np.ndarray: The preprocessed video array.
        """
        video = cv2.VideoCapture(path)
        frames = []
        video_length = video.get(cv2.CAP_PROP_FRAME_COUNT)
        for _ in range(int(video_length)):
            ret, frame = video.read()
            if not ret:
                break
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (self._input_shape[1], self._input_shape[2]))
            frame = np.expand_dims(np.expand_dims(frame, 0), 0)
            frames.append(frame)
        clips = np.array(frames, dtype=np.float32)
        return clips

    def _postprocess(self, response_outputs, _) -> np.ndarray:
        """Postprocess the model output.

        Args:
            response_outputs (Dict): The model response outputs.
            num_classes (int): The number of classes in the model.

        Returns:
            Tuple: The postprocessed model output
                containing class name and confidence score.
        """
        probs = response_outputs.flatten()
        label = np.argmax(probs)
        score = max(probs)
        label = self._category_index[label]["name"]
        return label, score
