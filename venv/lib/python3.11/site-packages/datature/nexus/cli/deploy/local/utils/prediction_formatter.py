#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   module.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Module for Saver output.
"""

# pylint: disable=R0911,R0913,R0914,R0917

import base64
import os
import tempfile
from typing import Dict, List, Optional

import cv2
import nibabel as nib
import numpy as np
from scipy.ndimage import zoom

from datature.nexus.cli.deploy.local.types.prediction_request import ResponseFormat
from datature.nexus.cli.deploy.local.types.prediction_response import (
    BitmaskCOCORLE,
    BitmaskNiiGz,
    Prediction,
    Tag,
)
from datature.nexus.cli.deploy.local.types.skeleton import (
    Connection,
    Keypoint,
    Skeleton,
)
from datature.nexus.cli.deploy.local.utils.inference import PredictionTaskType
from datature.nexus.cli.deploy.local.utils.label_map import LabelMap
from datature.nexus.cli.deploy.local.utils.postprocess import (
    get_minimum_bounding_box,
    get_minimum_bounding_cube,
    numpy_to_rle,
)
from datature.nexus.error import Error


class PredictionFormatter:
    """Prediction formatter class."""

    def run(
        self,
        task_type: PredictionTaskType,
        response_format: ResponseFormat,
        image: np.ndarray,
        predictions: Dict[str, np.ndarray],
        label_map: LabelMap,
        skeletons: Optional[Dict[str, Skeleton]] = None,
        affine: Optional[np.ndarray] = None,
    ) -> List[Prediction]:
        """Format predictions in Datature JSON Lines format.

        Args:
            task_type: Task type.
            response_format: Response format.
            image: Image.
            predictions: Dictionary of predictions.
            label_map: Label map object.
            skeletons: Skeletons object.
            affine: Affine matrix.

        Returns:
            Formatted predictions in Datature JSON Lines format
            and optionally NiiGz encoded prediction as base64 string.
        """

        if task_type == PredictionTaskType.IMAGE_CLASSIFICATION:
            return self._format_class_predictions(predictions, label_map)

        if task_type == PredictionTaskType.OBJECT_DETECTION:
            return self._format_boxes(predictions, label_map)

        if task_type == PredictionTaskType.INSTANCE_SEGMENTATION:
            return self._format_instance_masks(image, predictions, label_map)

        if task_type == PredictionTaskType.SEMANTIC_SEGMENTATION:
            if response_format == ResponseFormat.BITMASK:
                return self._format_semantic_masks_to_bitmask(predictions, label_map)

            return self._format_semantic_masks_to_polygons(
                image, predictions, label_map
            )

        if task_type == PredictionTaskType.SEMANTIC_3D_SEGMENTATION:
            return self._format_semantic_3d_masks(image, predictions, label_map, affine)

        if task_type == PredictionTaskType.KEYPOINT_DETECTION:
            return self._format_keypoints(predictions, label_map, skeletons)

        raise Error(f"Unsupported task type: {task_type}")

    def _format_class_predictions(
        self, predictions: Dict[str, np.ndarray], label_map: LabelMap
    ) -> List[Prediction]:
        """Format class predictions in Datature JSON Lines format.

        Args:
            predictions: Dictionary of predictions.
            label_map: Label map object.

        Returns:
            Formatted predictions in Datature JSON Lines format.
        """
        prediction_id = 0
        formatted_predictions = []

        for each_class, each_score in zip(
            predictions["classes"], predictions["scores"]
        ):
            formatted_prediction = Prediction(
                annotation_id=0,
                confidence=float(each_score),
                tag=Tag(
                    id=int(each_class),
                    name=label_map[int(each_class)].name,
                ),
                bound_type="classification",
                contour_type=None,
                bound=None,
            )
            formatted_predictions.append(formatted_prediction)
            prediction_id += 1

        return formatted_predictions

    def _format_boxes(
        self, predictions: Dict[str, np.ndarray], label_map: LabelMap
    ) -> List[Prediction]:
        """Format boxes in Datature JSON Lines format.

        Args:
            predictions: Dictionary of predictions.
            label_map: Label map object.

        Returns:
            Formatted predictions in Datature JSON Lines format.
        """
        prediction_id = 0
        formatted_predictions = []

        for each_box, each_class, each_score in zip(
            predictions["boxes"], predictions["classes"], predictions["scores"]
        ):
            formatted_prediction = Prediction(
                annotation_id=prediction_id,
                confidence=float(each_score),
                tag=Tag(
                    id=int(each_class),
                    name=label_map[int(each_class)].name,
                ),
                bound_type="rectangle",
                contour_type=None,
                bound=[
                    [float(each_box[1]), float(each_box[0])],  # xmin, ymin
                    [float(each_box[1]), float(each_box[2])],  # xmin, ymax
                    [float(each_box[3]), float(each_box[2])],  # xmax, ymax
                    [float(each_box[3]), float(each_box[0])],  # xmax, ymin
                ],
            )
            formatted_predictions.append(formatted_prediction)
            prediction_id += 1

        return formatted_predictions

    def _format_instance_masks(
        self,
        image: np.ndarray,
        predictions: Dict[str, np.ndarray],
        label_map: LabelMap,
    ) -> List[Prediction]:
        """Format instance masks in Datature JSON Lines format.

        Args:
            image: Image.
            predictions: Dictionary of predictions.
            label_map: Label map object.

        Returns:
            Formatted predictions in Datature JSON Lines format.
        """
        prediction_id = 0
        formatted_predictions = []

        for each_box, each_mask, each_class, each_score in zip(
            predictions["boxes"],
            predictions["masks"],
            predictions["classes"],
            predictions["scores"],
        ):
            mask_height, mask_width = each_mask.shape

            xmin, ymin, xmax, ymax = each_box
            ymin = int(ymin * mask_height)
            ymax = int(ymax * mask_height)
            xmin = int(xmin * mask_width)
            xmax = int(xmax * mask_width)

            row = np.expand_dims(np.arange(mask_width), 0)
            col = np.expand_dims(np.arange(mask_height), -1)
            each_mask *= (row >= xmin) * (row <= xmax) * (col >= ymin) * (col <= ymax)

            each_mask = cv2.resize(
                each_mask,
                (image.shape[1], image.shape[0]),
                interpolation=cv2.INTER_LINEAR,
            )
            binary_mask = np.where(each_mask > 0, 255, 0).astype(np.uint8)

            # convert masks to polygon
            contours, _ = cv2.findContours(
                binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            for contour in contours:
                normalized_contour = contour.squeeze().tolist()
                normalized_contour = [
                    [
                        float(normalized_contour[i][0]) / image.shape[1],
                        float(normalized_contour[i][1]) / image.shape[0],
                    ]
                    for i in range(len(normalized_contour))
                ]

                formatted_prediction = Prediction(
                    annotation_id=prediction_id,
                    confidence=float(each_score),
                    tag=Tag(
                        id=int(each_class),
                        name=label_map[int(each_class)].name,
                    ),
                    bound_type="polygon",
                    contour_type="polygon",
                    bound=normalized_contour,
                )
                formatted_predictions.append(formatted_prediction)
                prediction_id += 1

        return formatted_predictions

    def _format_semantic_masks_to_polygons(
        self,
        image: np.ndarray,
        predictions: Dict[str, np.ndarray],
        label_map: LabelMap,
    ) -> List[Prediction]:
        """Format semantic masks in Datature JSON Lines format.

        Args:
            image: Image.
            predictions: Dictionary of predictions.
            label_map: Label map object.

        Returns:
            Formatted predictions in Datature JSON Lines format.
        """
        prediction_id = 0
        formatted_predictions = []

        mask = predictions["masks"]
        scores = predictions["scores"]

        if mask is None:
            return []

        unique_classes = np.unique(mask)
        if 0 in unique_classes:
            unique_classes = unique_classes[unique_classes != 0]

        resized_mask = cv2.resize(
            mask,
            (image.shape[1], image.shape[0]),
            interpolation=cv2.INTER_LINEAR,
        )

        # Process each class
        for class_id in unique_classes:
            if class_id not in label_map.ids.keys():
                continue

            # Create binary mask for this class
            binary_mask = (resized_mask == class_id).astype(np.uint8)

            # Find contours for this class
            contours, _ = cv2.findContours(
                binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            # Get average confidence score for pixels of this class
            class_indices = np.where(mask == class_id)[0]
            if len(class_indices) > 0:
                # Use the scores from the filtered indices that also match this class
                filtered_indices = class_indices
                score = float(np.mean(scores[filtered_indices]))
            else:
                score = 1.0

            # Process each contour
            for contour in contours:
                if len(contour) < 3:
                    continue

                normalized_contour = contour.squeeze().tolist()
                normalized_contour = [
                    [
                        float(normalized_contour[i][0]) / image.shape[1],
                        float(normalized_contour[i][1]) / image.shape[0],
                    ]
                    for i in range(len(normalized_contour))
                ]

                # Format contour into required structure
                formatted_prediction = Prediction(
                    annotation_id=prediction_id,
                    confidence=float(score),
                    tag=Tag(
                        id=int(class_id),
                        name=label_map[int(class_id)].name,
                    ),
                    bound_type="polygon",
                    contour_type="polygon",
                    bound=normalized_contour,
                )

                formatted_predictions.append(formatted_prediction)
                prediction_id += 1
        return formatted_predictions

    def _format_semantic_masks_to_bitmask(
        self,
        predictions: Dict[str, np.ndarray],
        label_map: LabelMap,
    ) -> List[Prediction]:
        """Format semantic masks to COCO-RLE encoded bitmask in Datature JSON Lines format.

        Args:
            predictions: Dictionary of predictions.
            label_map: Label map object.

        Returns:
            Formatted predictions in Datature JSON Lines format.
        """
        prediction_id = 0
        formatted_predictions = []

        mask = predictions["masks"]
        scores = predictions["scores"]

        if mask is None:
            return []

        unique_classes = np.unique(mask)

        if 0 in unique_classes:
            unique_classes = unique_classes[unique_classes != 0]

        # Process each class
        for class_id in unique_classes:
            if class_id not in label_map.ids.keys():
                continue

            # Create binary mask for this class
            binary_mask = (mask == class_id).astype(np.uint8)

            # Get bounding box 2D for this class
            bounding_box = get_minimum_bounding_box(binary_mask)

            rle_string = numpy_to_rle(binary_mask)

            # Get average confidence score for pixels of this class
            class_indices = np.where(mask == class_id)[0]
            if len(class_indices) > 0:
                # Use the scores from the filtered indices that also match this class
                filtered_indices = class_indices
                score = float(np.mean(scores[filtered_indices]))
            else:
                score = 1.0

            formatted_prediction = Prediction(
                annotation_id=prediction_id,
                confidence=float(score),
                tag=Tag(
                    id=int(class_id),
                    name=label_map[int(class_id)].name,
                ),
                bound_type="masks",
                contour_type="bitmask",
                bound=bounding_box,
                bitmask=BitmaskCOCORLE(
                    height=int(mask.shape[0]),
                    width=int(mask.shape[1]),
                    counts=rle_string["counts"],
                ),
            )

            formatted_predictions.append(formatted_prediction)
            prediction_id += 1
        return formatted_predictions

    def _format_semantic_3d_masks(
        self,
        image: np.ndarray,
        predictions: Dict[str, np.ndarray],
        label_map: LabelMap,
        affine: Optional[np.ndarray] = None,
    ) -> List[Prediction]:
        """Format semantic 3D masks in Datature JSON Lines format.

        Args:
            image: Image.
            predictions: Dictionary of predictions.
            label_map: Label map object.
            affine: Affine matrix.

        Returns:
            Formatted predictions in Datature JSON Lines format.
            NiiGz encoded prediction as base64 string.
        """
        prediction_id = 0
        formatted_predictions = []

        mask = predictions["masks"]
        scores = predictions["scores"]

        if mask is None:
            return []

        unique_classes = np.unique(mask)
        if 0 in unique_classes:
            unique_classes = unique_classes[unique_classes != 0]

        zoom_factors = [image.shape[i] / mask.shape[i] for i in range(3)]
        zoomed_mask = np.array(zoom(mask, zoom_factors, order=0))

        for class_id in unique_classes:
            if class_id not in label_map.ids.keys():
                continue

            binary_mask = (zoomed_mask == class_id).astype(np.uint8)

            # get minimum bounding cube
            bounding_cube = get_minimum_bounding_cube(binary_mask)

            # Get all indices where mask equals class_id across all dimensions
            class_indices = np.where(mask == class_id)[0]
            if len(class_indices) > 0:
                # Get scores for all matching voxels
                score = float(np.mean(scores[class_indices]))
            else:
                score = 1.0

            with tempfile.NamedTemporaryFile(
                suffix=".nii.gz", delete=False
            ) as temp_file:
                temp_path = temp_file.name

            try:
                nifti_mask = nib.Nifti1Image(binary_mask, affine)
                nib.save(nifti_mask, temp_path)

                with open(temp_path, "rb") as f:
                    nifti_bytes = f.read()

                base64_encoded_prediction = base64.b64encode(nifti_bytes).decode(
                    "utf-8"
                )

            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

            formatted_prediction = Prediction(
                annotation_id=prediction_id,
                confidence=float(score),
                tag=Tag(id=int(class_id), name=label_map[int(class_id)].name),
                bound_type="masks3d",
                bound=bounding_cube,
                contour_type="bitmask",
                bitmask=BitmaskNiiGz(file=base64_encoded_prediction),
            )
            formatted_predictions.append(formatted_prediction)
            prediction_id += 1

        return formatted_predictions

    def _format_keypoints(
        self,
        predictions: Dict[str, np.ndarray],
        label_map: LabelMap,
        skeletons: Optional[Dict[str, Skeleton]] = None,
    ) -> List[Prediction]:
        """Format keypoints in Datature JSON Lines format.

        Args:
            predictions: Dictionary of predictions.
            label_map: Label map object.
            skeletons: Skeletons object.

        Returns:
            Formatted predictions in Datature JSON Lines format.
        """
        prediction_id = 0
        formatted_predictions = []

        for (
            each_box,
            each_keypoint,
            keypoint_confidences,
            each_class,
            each_score,
        ) in zip(
            predictions["boxes"],
            predictions["keypoints"],
            predictions["keypoint_confidences"],
            predictions["classes"],
            predictions["scores"],
        ):
            class_name = label_map[int(each_class)].name

            keypoints = each_keypoint.reshape(-1, 3)
            keypoints = keypoints[keypoints[:, 2] > 0.5]

            formatted_prediction = Prediction(
                annotation_id=prediction_id,
                confidence=float(each_score),
                tag=Tag(
                    id=int(each_class),
                    name=class_name,
                ),
                bound_type="keypoints",
                contour_type=None,
                bound=[
                    [float(each_box[0]), float(each_box[1])],
                    [float(each_box[2]), float(each_box[1])],
                    [float(each_box[2]), float(each_box[3])],
                    [float(each_box[0]), float(each_box[3])],
                ],
                skeleton=(
                    Skeleton(
                        name=skeletons[class_name].name,
                        keypoints=[
                            Keypoint(name=keypoint.name, category=keypoint.category)
                            for keypoint in skeletons[class_name].keypoints
                        ],
                        connections=[
                            Connection(pair=connection.pair)
                            for connection in skeletons[class_name].connections
                        ],
                    ).to_json()
                    if skeletons
                    else None
                ),
                keypoint_confidences=keypoint_confidences.tolist(),
                keypoints=keypoints.tolist(),
            )
            formatted_predictions.append(formatted_prediction)
            prediction_id += 1

        return formatted_predictions
