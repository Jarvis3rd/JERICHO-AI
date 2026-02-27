#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   postprocess.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Postprocess utility functions.
"""
# pylint: disable=R0913,R0914,R0915,R0917

import copy
from typing import Any, List, Optional, Tuple

import numpy as np
import pycocotools.mask
from numpy.typing import NDArray


def nms(
    boxes: np.ndarray,
    classes: np.ndarray,
    scores: np.ndarray,
    masks: Optional[np.ndarray] = None,
    keypoints: Optional[np.ndarray] = None,
    keypoint_confidences: Optional[np.ndarray] = None,
    iou_threshold: float = 0.1,
    confidence: float = 0.1,
    sigma: float = 0.5,
) -> Tuple[
    NDArray[Any],
    NDArray[Any],
    NDArray[Any],
    Optional[NDArray[Any]],
    Optional[NDArray[Any]],
    Optional[NDArray[Any]],
]:
    """Carry out non-max supression on the predictions.

    Args:
        boxes: Bounding boxes.
        classes: Classes.
        scores: Scores.
        masks: Masks.
        keypoints: Keypoints.
        keypoint_confidences: Keypoint confidences.
        iou_threshold: IoU threshold.
        confidence: Confidence threshold.
        sigma: Sigma for soft-NMS.

    Returns:
        Filtered boxes, classes, scores, optional masks,
        optional keypoints, and optional keypoint confidences.
    """
    is_soft = False
    use_exp = False

    (
        nms_boxes,
        nms_classes,
        nms_scores,
        nms_masks,
        nms_keypoints,
        nms_keypoint_confidences,
    ) = ([], [], [], [], [], [])

    for each_class in set(classes):
        # handle data for one class
        indices = np.where(classes == each_class)
        filtered_boxes = boxes[indices]
        filtered_classes = classes[indices]
        filtered_scores = scores[indices]
        filtered_masks = masks[indices] if masks is not None else None
        filtered_keypoints = keypoints[indices] if keypoints is not None else None
        filtered_keypoint_confidences = (
            keypoint_confidences[indices] if keypoint_confidences is not None else None
        )

        # make a data copy to avoid breaking
        # during nms operation
        boxes_nms = copy.deepcopy(filtered_boxes)
        classes_nms = copy.deepcopy(filtered_classes)
        scores_nms = copy.deepcopy(filtered_scores)
        masks_nms = (
            copy.deepcopy(filtered_masks) if filtered_masks is not None else None
        )
        keypoints_nms = (
            copy.deepcopy(filtered_keypoints)
            if filtered_keypoints is not None
            else None
        )
        keypoint_confidences_nms = (
            copy.deepcopy(filtered_keypoint_confidences)
            if filtered_keypoint_confidences is not None
            else None
        )

        while len(scores_nms) > 0:
            # pick the max box and store, here
            # we also use copy to persist result
            i = np.argmax(scores_nms, axis=-1)
            nms_boxes.append(copy.deepcopy(boxes_nms[i]))
            nms_classes.append(copy.deepcopy(classes_nms[i]))
            nms_scores.append(copy.deepcopy(scores_nms[i]))

            if masks_nms is not None:
                nms_masks.append(copy.deepcopy(masks_nms[i]))

            if keypoints_nms is not None and keypoint_confidences_nms is not None:
                nms_keypoints.append(copy.deepcopy(keypoints_nms[i]))
                nms_keypoint_confidences.append(
                    copy.deepcopy(keypoint_confidences_nms[i])
                )

            # swap the max line and first line
            boxes_nms[[i, 0], :] = boxes_nms[[0, i], :]
            classes_nms[[i, 0]] = classes_nms[[0, i]]
            scores_nms[[i, 0]] = scores_nms[[0, i]]

            if masks_nms is not None:
                masks_nms[[i, 0]] = masks_nms[[0, i]]

            if keypoints_nms is not None and keypoint_confidences_nms is not None:
                keypoints_nms[[i, 0]] = keypoints_nms[[0, i]]
                keypoint_confidences_nms[[i, 0]] = keypoint_confidences_nms[[0, i]]

            iou = box_diou(boxes_nms)

            # drop the last line since it has been record
            boxes_nms = boxes_nms[1:]
            classes_nms = classes_nms[1:]
            scores_nms = scores_nms[1:]
            masks_nms = masks_nms[1:] if masks_nms is not None else None
            keypoints_nms = keypoints_nms[1:] if keypoints_nms is not None else None
            keypoint_confidences_nms = (
                keypoint_confidences_nms[1:]
                if keypoint_confidences_nms is not None
                else None
            )

            if is_soft:
                # Soft-NMS
                if use_exp:
                    # score refresh formula:
                    # score = score * exp(-(iou^2)/sigma)
                    scores_nms = scores_nms * np.exp(-(iou * iou) / sigma)
                else:
                    # score refresh formula:
                    # score = score * (1 - iou) if iou > threshold
                    depress_mask = np.where(iou > iou_threshold)[0]
                    scores_nms[depress_mask] = scores_nms[depress_mask] * (
                        1 - iou[depress_mask]
                    )
                keep_mask = np.where(scores_nms >= confidence)[0]
            else:
                # normal Hard-NMS
                keep_mask = np.where(iou <= iou_threshold)[0]

            # keep needed box for next loop
            boxes_nms = boxes_nms[keep_mask]
            classes_nms = classes_nms[keep_mask]
            scores_nms = scores_nms[keep_mask]
            masks_nms = masks_nms[keep_mask] if masks_nms is not None else None
            keypoints_nms = (
                keypoints_nms[keep_mask] if keypoints_nms is not None else None
            )
            keypoint_confidences_nms = (
                keypoint_confidences_nms[keep_mask]
                if keypoint_confidences_nms is not None
                else None
            )

    # reformat result for output
    nms_boxes_np = np.array(nms_boxes)
    nms_classes_np = np.array(nms_classes)
    nms_scores_np = np.array(nms_scores)
    nms_masks_np = np.array(nms_masks) if nms_masks else None
    nms_keypoints_np = np.array(nms_keypoints) if nms_keypoints else None
    nms_keypoint_confidences_np = (
        np.array(nms_keypoint_confidences) if nms_keypoint_confidences else None
    )

    return (
        nms_boxes_np,
        nms_classes_np,
        nms_scores_np,
        nms_masks_np,
        nms_keypoints_np,
        nms_keypoint_confidences_np,
    )


def box_diou(boxes):
    """
    Calculate DIoU value of 1st box with other boxes of a box array
    Reference Paper:
        "Distance-IoU Loss: Faster and Better Learning for
        Bounding Box Regression"
        https://arxiv.org/abs/1911.08287

    Args:
      boxes: bbox numpy array, shape=(N, 4), xywh
             x,y are top left coordinates

    Returns:
      diou: numpy array, shape=(N-1,)
            IoU value of boxes[1:] with boxes[0]
    """
    # get box coordinate and area
    x_pos = boxes[:, 0]
    y_pos = boxes[:, 1]
    wid = boxes[:, 2]
    hei = boxes[:, 3]
    areas = wid * hei

    # check IoU
    inter_xmin = np.maximum(x_pos[1:], x_pos[0])
    inter_ymin = np.maximum(y_pos[1:], y_pos[0])
    inter_xmax = np.minimum(x_pos[1:] + wid[1:], x_pos[0] + wid[0])
    inter_ymax = np.minimum(y_pos[1:] + hei[1:], y_pos[0] + hei[0])

    inter_w = np.maximum(0.0, inter_xmax - inter_xmin + 1)
    inter_h = np.maximum(0.0, inter_ymax - inter_ymin + 1)

    inter = inter_w * inter_h
    iou = inter / (areas[1:] + areas[0] - inter)

    # box center distance
    x_center = x_pos + wid / 2
    y_center = y_pos + hei / 2
    center_distance = np.power(x_center[1:] - x_center[0], 2) + np.power(
        y_center[1:] - y_center[0], 2
    )

    # get enclosed area
    enclose_xmin = np.minimum(x_pos[1:], x_pos[0])
    enclose_ymin = np.minimum(y_pos[1:], y_pos[0])
    enclose_xmax = np.maximum(x_pos[1:] + wid[1:], x_pos[0] + wid[0])
    enclose_ymax = np.maximum(y_pos[1:] + wid[1:], y_pos[0] + wid[0])
    enclose_w = np.maximum(0.0, enclose_xmax - enclose_xmin + 1)
    enclose_h = np.maximum(0.0, enclose_ymax - enclose_ymin + 1)
    # get enclosed diagonal distance
    enclose_diagonal = np.power(enclose_w, 2) + np.power(enclose_h, 2)
    # calculate DIoU, add epsilon in denominator to avoid dividing by 0
    diou = iou - 1.0 * (center_distance) / (enclose_diagonal + np.finfo(float).eps)

    return diou


def box_xywh2xyxyn(boxes_xywh: NDArray[Any], height: int, width: int):
    """Convert boxes from xywh to xyxyn format"""
    boxes_xyxyn = np.copy(boxes_xywh)
    boxes_xyxyn[..., 0] = (
        boxes_xywh[..., 0] - boxes_xywh[..., 2] / 2
    ) / width  # top left x
    boxes_xyxyn[..., 1] = (
        boxes_xywh[..., 1] - boxes_xywh[..., 3] / 2
    ) / height  # top left y
    boxes_xyxyn[..., 2] = (
        boxes_xywh[..., 0] + boxes_xywh[..., 2] / 2
    ) / width  # bottom right x
    boxes_xyxyn[..., 3] = (
        boxes_xywh[..., 1] + boxes_xywh[..., 3] / 2
    ) / height  # bottom right y
    boxes_xyxyn = np.clip(boxes_xyxyn, 0, 1)
    return boxes_xyxyn


def clamp(value: float, minimum=0.0, maximum=1.0) -> float:
    """Clamp a value between a minimum and maximum value.

    :param x: Value to clamp.
    :param minimum: Minimum value to clamp to.
    :param maximum: Maximum value to clamp to.
    :return: Clamped value.
    """
    return max(minimum, min(value, maximum))


def get_instance_mask(mask: np.ndarray, threshold: int) -> np.ndarray:
    """Convert class mask to instaance mask"""
    instance_mask = np.zeros_like(mask, np.uint8)
    instance_mask[np.where(mask > threshold)] = 1
    return instance_mask


def get_minimum_bounding_box(mask: np.ndarray) -> List[List[float]]:
    """Get minimum bounding box of a mask and return its 4 normalized vertices.

    Args:
        mask: 2D binary mask array

    Returns:
        List of 4 vertices coordinates in order:
        (v1_top_left, v2_top_right, v3_bottom_right, v4_bottom_left)
    """
    xmin, ymin = np.min(np.where(mask > 0), axis=1)
    xmax, ymax = np.max(np.where(mask > 0), axis=1)

    # Get dimensions for normalization
    height, width = mask.shape

    # Normalize coordinates between 0 and 1
    xmin, xmax = float(xmin) / width, float(xmax) / width
    ymin, ymax = float(ymin) / height, float(ymax) / height

    return [[xmin, ymin], [xmax, ymin], [xmax, ymax], [xmin, ymax]]


def get_minimum_bounding_cube(
    mask: np.ndarray,
) -> List[List[float]]:
    """Get minimum bounding cube of a mask and return its 8 normalized vertices.

    Args:
        mask: 3D binary mask array

    Returns:
        Tuple of 8 vertices coordinates in order:
        (v1_front_top_left, v2_front_top_right, v3_front_bottom_right, v4_front_bottom_left,
         v5_back_top_left, v6_back_top_right, v7_back_bottom_right, v8_back_bottom_left)
    """
    # Get min/max coordinates
    xmin, ymin, zmin = np.min(np.where(mask > 0), axis=1)
    xmax, ymax, zmax = np.max(np.where(mask > 0), axis=1)

    # Get dimensions for normalization
    x_dim, y_dim, z_dim = mask.shape

    # Normalize coordinates between 0 and 1
    xmin, xmax = float(xmin) / x_dim, float(xmax) / x_dim
    ymin, ymax = float(ymin) / y_dim, float(ymax) / y_dim
    zmin, zmax = float(zmin) / z_dim, float(zmax) / z_dim

    # Calculate 8 vertices as lists
    v1 = [xmin, ymin, zmin]  # Front top left
    v2 = [xmax, ymin, zmin]  # Front top right
    v3 = [xmax, ymax, zmin]  # Front bottom right
    v4 = [xmin, ymax, zmin]  # Front bottom left
    v5 = [xmin, ymin, zmax]  # Back top left
    v6 = [xmax, ymin, zmax]  # Back top right
    v7 = [xmax, ymax, zmax]  # Back bottom right
    v8 = [xmin, ymax, zmax]  # Back bottom left

    return [v1, v2, v3, v4, v5, v6, v7, v8]


def numpy_to_rle(binary_mask: np.ndarray) -> Any:
    """
    Convert a numpy binary mask to RLE encoded string.

    Args:
        binary_mask: numpy array of shape (height, width) with values 0 and 1
                    or boolean values

    Returns:
        dict: RLE encoded mask in COCO format
    """
    # Ensure the mask is in the correct format (uint8 with values 0 and 1)
    if binary_mask.dtype == bool:
        binary_mask = binary_mask.astype(np.uint8)
    elif binary_mask.dtype != np.uint8:
        binary_mask = (binary_mask > 0).astype(np.uint8)

    # pycocotools expects Fortran order (column-major)
    binary_mask = np.asfortranarray(binary_mask)

    # Encode to RLE
    rle = pycocotools.mask.encode(binary_mask)

    # Convert counts to string if it's bytes (for JSON serialization)
    if isinstance(rle["counts"], bytes):
        rle["counts"] = rle["counts"].decode("utf-8")

    return rle
