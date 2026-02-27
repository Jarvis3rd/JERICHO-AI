#!/usr/env/bin python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   prediction_utils.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   TensorRT predictor util functions.
"""

# pylint: disable=R0912,R0913,R0914,R0915

import copy
import json
from typing import Dict, Tuple

import cv2
import numpy as np
import requests
from PIL import Image

# Triton Inference Server API endpoint
# default port is 8000 since Triton Inference Server uses 8000 as default
TRITON_MODEL_CONFIG_URL = "http://localhost:8000/v2/models/{}/config"


def get_model_config(model_name: str) -> Dict:
    """
    Get model configuration from Triton Inference Server.

    Args:
        model_name (str): Model name.

    Returns:
        model_config (dict): Model configuration.
    """
    model_config = requests.get(
        TRITON_MODEL_CONFIG_URL.format(model_name), timeout=(3, 10)
    ).json()
    return model_config


def load_label_map(label_map_path: str) -> Dict:
    """
    Reads label map in the format of .pbtxt and parse into dictionary

    Args:
      label_map_path: File path to the label_map

    Returns:
      Dictionary with the format of {label_index: {'id': label_index, 'name': label_name}}
    """
    label_map = {}

    with open(label_map_path, "r", encoding="utf-8") as label_file:
        for line in label_file:
            if "id" in line:
                label_index = int(line.split(":")[-1])
                label_name = next(label_file).split(":")[-1].strip().strip('"')
                label_map[label_index] = {
                    "id": label_index,
                    "name": label_name,
                }

    return label_map


def load_skeleton(skeleton_path: str) -> Dict:
    """Load skeletons from JSON file.

    Args:
        skeleton_path (str): Path to skeleton JSON file.

    Returns:
        Dictionary of skeleton with name as key and connections by position.
    """

    def _keypoint_positions(skeleton):
        keypoint_name_list = [keypoint["name"] for keypoint in skeleton["keypoints"]]
        return {
            "keypoint_names": keypoint_name_list,
            "connections": [
                [
                    keypoint_name_list.index(con["pair"][0]),
                    keypoint_name_list.index(con["pair"][1]),
                ]
                for con in skeleton["connections"]
            ],
        }

    with open(skeleton_path, "r", encoding="utf-8") as skeleton_file:
        skeletons = json.load(skeleton_file)["skeletons"]
    skeleton_dict = {
        skeleton["name"]: _keypoint_positions(skeleton) for skeleton in skeletons
    }

    return skeleton_dict


def draw_bboxes(
    image: np.ndarray,
    box: np.ndarray,
    class_id: int,
    score: float,
    color_map: dict,
    category_index: dict,
) -> np.ndarray:
    """
    Draws bounding boxes and labels on the input image based on the detected objects.

    Args:
        image (np.ndarray): The input image to draw detections on.
        box (np.ndarray): Bounding box coordinates in the format of [ymin, xmin, ymax, xmax].
        class_id (int): Class id of the detected object.
        score (float): Confidence score of the detected object.
        color_map (dict): Dictionary containing color map for each class.
        category_index (dict): Dictionary containing class index and name.

    Returns:
        img (np.ndarray): The input image with drawn detections.
    """
    origi_shape = image.shape
    color = color_map.get(category_index[class_id]["id"]).tolist()
    cv2.rectangle(
        image,
        (
            int(box[1] * origi_shape[1]),  # x1
            int(box[0] * origi_shape[0]),  # y1
        ),
        (
            int(box[3] * origi_shape[1]),  # x2
            int(box[2] * origi_shape[0]),  # y2
        ),
        color,
        2,
    )
    cv2.rectangle(
        image,
        (
            int(box[1] * origi_shape[1]),
            int(box[2] * origi_shape[0]),
        ),
        (
            int(box[3] * origi_shape[1]),
            int(box[2] * origi_shape[0] + 15),
        ),
        color,
        -1,
    )
    cv2.putText(
        image,
        f"{str(category_index[class_id]['name'])}, {str(round(score, 2))}",
        (
            int(box[1] * origi_shape[1]),
            int(box[2] * origi_shape[0] + 10),
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.3,
        (0, 0, 0),
        1,
        cv2.LINE_AA,
    )
    return image


def draw_instance_masks(
    image: np.ndarray,
    box: np.ndarray,
    mask: np.ndarray,
    class_id: int,
    color_map: dict,
    category_index: dict,
):
    """Draw instance masks on image.

    Args:
        image (np.ndarray): Image to draw masks on.
        box (np.ndarray): Bounding box coordinates in the format of [ymin, xmin, ymax, xmax].
        mask (np.ndarray): Instance mask.
        class_id (int): Class id.
        color_map (dict): Dictionary containing color map for each class.
        category_index (dict): Dictionary containing class index and name.

    Returns:
        image (np.ndarray): Image with masks drawn on.
    """
    color = color_map.get(category_index[class_id]["id"]).tolist()

    mask = np.expand_dims(mask, -1)
    mask = np.tile(mask, 3)
    mask[..., :] *= np.array(color, dtype=np.uint8)
    mask = np.clip(mask, 0, 255).astype(np.uint8)
    xmin, ymin, xmax, ymax = box
    ymin = int(ymin * image.shape[1])
    ymax = int(ymax * image.shape[1])
    xmin = int(xmin * image.shape[0])
    xmax = int(xmax * image.shape[0])
    mask_height = ymax - ymin
    mask_width = xmax - xmin
    mask = cv2.resize(mask, (mask_height, mask_width))
    resized_mask = np.zeros(image.shape)
    resized_mask[xmin:xmax, ymin:ymax, :] = mask
    image = image.astype(np.int64)
    image += resized_mask.astype(np.int64)
    image = np.clip(image, 0, 255).astype(np.uint8)
    return image


def draw_yolov8_instance_masks(
    image: np.ndarray,
    box: np.ndarray,
    mask: np.ndarray,
    class_id: int,
    color_map: dict,
    category_index: dict,
):
    """Draw YOLOv8 instance masks on image.

    Args:
        image (np.ndarray): Image to draw masks on.
        box (np.ndarray): Bounding box coordinates in the format of [ymin, xmin, ymax, xmax].
        mask (np.ndarray): Instance mask.
        class_id (int): Class id.
        color_map (dict): Dictionary containing color map for each class.
        category_index (dict): Dictionary containing class index and name.

    Returns:
        image (np.ndarray): Image with masks drawn on.
    """
    color = color_map.get(category_index[class_id]["id"]).tolist()

    ymin, xmin, ymax, xmax = box
    mask_height, mask_width = mask.shape
    ymin = int(ymin * mask_height)
    xmin = int(xmin * mask_width)
    ymax = int(ymax * mask_height)
    xmax = int(xmax * mask_width)
    row = np.expand_dims(np.arange(mask_width), 0)
    col = np.expand_dims(np.arange(mask_height), -1)
    mask *= (row >= xmin) * (row <= xmax) * (col >= ymin) * (col <= ymax)
    mask = mask.astype(np.uint8)
    mask = np.expand_dims(mask, -1)
    mask = np.tile(mask, 3)
    mask = cv2.resize(
        mask, (image.shape[1], image.shape[0]), interpolation=cv2.INTER_LINEAR
    )
    mask = np.where(mask > 0, np.uint8(1), np.uint8(0))
    masked_image = image.copy()
    masked_image = np.where(mask, np.array(color, dtype=np.uint8), masked_image)
    image = cv2.addWeighted(image, 0.3, masked_image, 0.7, 0)
    return image


def draw_semantic_masks(image: np.ndarray, mask: np.ndarray, color_map: dict):
    """Draw semantic masks on image.

    Args:
        image (np.ndarray): Image to draw masks on.
        mask (np.ndarray): Semantic mask.

    Returns:
        image (np.ndarray): Image with masks drawn on.
    """
    mask = np.expand_dims(mask, -1)
    mask = np.tile(mask, 3)
    unique = np.unique(mask)
    output_mask = np.zeros_like(mask, dtype=np.uint8)
    for item in unique:
        output_mask = np.where(mask != item, output_mask, color_map[int(item)])
    output_mask = cv2.resize(output_mask, (image.shape[1], image.shape[0]))
    image = image.astype(np.uint8)
    pil_image = Image.fromarray(image)
    pil_mask = Image.fromarray(output_mask)
    pil_image = Image.blend(pil_image, pil_mask, 0.7)
    return np.array(pil_image)


def draw_keypoints(
    image: np.ndarray,
    keypoints,
    scores,
    class_id,
    color_map: dict,
    category_index: dict,
    skeletons: dict,
):
    """Draw keypoints and skeleton on image.

    Args:
        image (np.ndarray): Image to draw keypoints on.
        keypoints (np.ndarray): Array of keypoints.
        scores (np.ndarray): Array of keypoint confidences.
        class_id (int): Class id.
        color_map (dict): Dictionary containing color map for each class.
        category_index (dict): Dictionary containing class index and name.
        skeletons (dict): Dictionary containing skeleton information.

    Returns:
        image (np.ndarray): Image with keypoints and skeleton drawn on.
    """
    height, width, _ = image.shape
    _, ndim = keypoints.shape
    skeleton = skeletons.get(category_index[int(class_id)]["name"])
    if skeleton is None:
        return image

    for ske in skeleton["connections"]:
        pos1 = (
            int(keypoints[(int(ske[0])), 0] * width),
            int(keypoints[(int(ske[0])), 1] * height),
        )
        pos2 = (
            int(keypoints[(int(ske[1])), 0] * width),
            int(keypoints[(int(ske[1])), 1] * height),
        )
        if ndim == 3:
            conf1 = keypoints[(ske[0]), 2]
            conf2 = keypoints[(ske[1]), 2]
            if conf1 < 0.5 or conf2 < 0.5:
                continue
        if pos1[0] % width == 0 or pos1[1] % height == 0 or pos1[0] < 0 or pos1[1] < 0:
            continue
        if pos2[0] % width == 0 or pos2[1] % height == 0 or pos2[0] < 0 or pos2[1] < 0:
            continue
        cv2.line(
            image,
            pos1,
            pos2,
            color_map[class_id].tolist(),
            thickness=2,
            lineType=cv2.LINE_AA,
        )
    for kpi, (each_kp, each_score) in enumerate(zip(keypoints, scores)):
        x_coord, y_coord = each_kp[0] * width, each_kp[1] * height
        if x_coord % width != 0 and y_coord % height != 0:
            if len(each_kp) == 3:
                conf = each_kp[2]
                if conf < 0.5:
                    continue
            cv2.circle(
                image,
                (int(x_coord), int(y_coord)),
                2,
                (0, 0, 0),
                -1,
                lineType=cv2.LINE_AA,
            )
            cv2.rectangle(
                image,
                (int(x_coord) - 10, int(y_coord) - 15),
                (
                    int(x_coord)
                    + len(
                        f"{skeleton['keypoint_names'][kpi]} "
                        f"{str(round(each_score, 2))}"
                    )
                    * 5,
                    int(y_coord),
                ),
                (0, 0, 0),
                -1,
            )
            cv2.putText(
                image,
                f"{skeleton['keypoint_names'][kpi]} " f"{str(round(each_score, 2))}",
                (int(x_coord) - 10, int(y_coord) - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.3,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )
    return image


def draw_class_labels(
    image: np.ndarray,
    class_id: int,
    score: float,
    color_map: dict,
    category_index: dict,
):
    """Draw class labels on image.

    Args:
        image (np.ndarray): Image to draw class labels on.
        class_id (int): Class id.
        score (float): Confidence score.
        color_map (dict): Dictionary containing color map for each class.
        category_index (dict): Dictionary containing class index and name.

    Returns:
        image (np.ndarray): Image with class labels drawn on.
    """
    height, width, _ = image.shape
    color = color_map.get(class_id - 1).tolist()
    cv2.rectangle(
        image,
        (0, 0),
        (width, height),
        color,
        4,
    )
    cv2.rectangle(
        image,
        (0, 0),
        (width, 15),
        color,
        -1,
    )
    cv2.putText(
        image,
        f"{str(category_index[class_id]['name'])}, {str(round(score, 2))}",
        (10, 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.3,
        (0, 0, 0),
        1,
        cv2.LINE_AA,
    )
    return image


def postprocess_predictions(pred: np.array, num_classes: int) -> Tuple[np.ndarray]:
    """Postprocess predictions from model output.

    Args:
        pred (np.array): Model output.
        num_classes (int): Number of classes.

    Returns:
        scores (np.ndarray): Array of scores.
        classes (np.ndarray): Array of classes.
        boxes_xywh (np.ndarray): Array of bounding boxes in xywh format.
        extras (np.ndarray): Array of extra predictions.
    """
    num_extras = pred.shape[1] - num_classes - 4
    boxes_xywh = pred[..., :4]
    class_end = 4 + num_classes
    score_classes = pred[..., 4:class_end]
    extras = pred[..., class_end : class_end + num_extras]

    scores = np.max(score_classes, axis=1)
    classes = np.argmax(score_classes, axis=1).astype(np.int32)

    return scores, classes, boxes_xywh, extras


def xywh2xyxy(boxes_xywh: np.ndarray, height: int, width: int) -> np.ndarray:
    """Convert boxes from xywh to xyxy format.

    Args:
        boxes_xywh (np.ndarray): Array of bounding boxes in xywh format.
        height (int): Height of the image.
        width (int): Width of the image.

    Returns:
        boxes_xyxy (np.ndarray): Array of bounding boxes in xyxy format.
    """
    boxes_xyxy = np.copy(boxes_xywh)
    boxes_xyxy[..., 0] = (
        boxes_xywh[..., 0] - boxes_xywh[..., 2] / 2
    ) / width  # top left x
    boxes_xyxy[..., 1] = (
        boxes_xywh[..., 1] - boxes_xywh[..., 3] / 2
    ) / height  # top left y
    boxes_xyxy[..., 2] = (
        boxes_xywh[..., 0] + boxes_xywh[..., 2] / 2
    ) / width  # bottom right x
    boxes_xyxy[..., 3] = (
        boxes_xywh[..., 1] + boxes_xywh[..., 3] / 2
    ) / height  # bottom right y
    boxes_xyxy = np.clip(boxes_xyxy, 0, 1)
    return boxes_xyxy


def nms_boxes(
    boxes: np.ndarray,
    classes: np.ndarray,
    scores: np.ndarray,
    iou_threshold: float,
    dtype: str,
    masks: np.ndarray = None,
    keypoints: np.ndarray = None,
    keypoint_confs: np.ndarray = None,
    confidence: float = 0.5,
    sigma: float = 0.5,
) -> Tuple[np.ndarray]:
    """Carry out non-max suppression on the detected bboxes.

    Args:
        boxes (np.ndarray): Array of bounding boxes in xyxy format.
        classes (np.ndarray): Array of classes.
        scores (np.ndarray): Array of scores.
        iou_threshold (float): IoU threshold for NMS.
        dtype (str): Data type of the model output.
        masks (np.ndarray): Array of masks.
        keypoints (np.ndarray): Array of keypoints.
        keypoint_confs (np.ndarray): Array of keypoint confidences.
        confidence (float): Confidence threshold for NMS.
        sigma (float): Sigma value for Soft-NMS.

    Returns:
        nboxes (np.ndarray): Array of non-max suppressed bounding boxes.
        nclasses (np.ndarray): Array of non-max suppressed classes.
        nscores (np.ndarray): Array of non-max suppressed scores.
        nmasks (np.ndarray): Array of non-max suppressed masks.
        nkpts (np.ndarray): Array of non-max suppressed keypoints.
        nkptcnfs (np.ndarray): Array of non-max suppressed keypoint confidences.
    """
    is_soft = False
    use_exp = False

    nboxes, nclasses, nscores, nmasks, nkpts, nkptcnfs = [], [], [], [], [], []
    for cls in set(classes):
        # handle data for one class
        inds = np.where(classes == cls)
        bbx = boxes[inds]
        cls = classes[inds]
        sco = scores[inds]
        if masks is not None:
            msk = masks[inds]
        if keypoints is not None and keypoint_confs is not None:
            kpt = keypoints[inds]
            kptcnf = keypoint_confs[inds]

        # make a data copy to avoid breaking
        # during nms operation
        b_nms = copy.deepcopy(bbx)
        c_nms = copy.deepcopy(cls)
        s_nms = copy.deepcopy(sco)
        if masks is not None:
            m_nms = copy.deepcopy(msk)
        if keypoints is not None and keypoint_confs is not None:
            k_nms = copy.deepcopy(kpt)
            kc_nms = copy.deepcopy(kptcnf)

        while len(s_nms) > 0:
            # pick the max box and store, here
            # we also use copy to persist result
            i = np.argmax(s_nms, axis=-1)
            nboxes.append(copy.deepcopy(b_nms[i]))
            nclasses.append(copy.deepcopy(c_nms[i]))
            nscores.append(copy.deepcopy(s_nms[i]))
            if masks is not None:
                nmasks.append(copy.deepcopy(m_nms[i]))
            if keypoints is not None and keypoint_confs is not None:
                nkpts.append(copy.deepcopy(k_nms[i]))
                nkptcnfs.append(copy.deepcopy(kc_nms[i]))

            # swap the max line and first line
            b_nms[[i, 0], :] = b_nms[[0, i], :]
            c_nms[[i, 0]] = c_nms[[0, i]]
            s_nms[[i, 0]] = s_nms[[0, i]]
            if masks is not None:
                m_nms[[i, 0]] = m_nms[[0, i]]
            if keypoints is not None and keypoint_confs is not None:
                k_nms[[i, 0], :] = k_nms[[0, i], :]
                kc_nms[[i, 0]] = kc_nms[[0, i]]

            iou = box_diou(b_nms, dtype)

            # drop the last line since it has been record
            b_nms = b_nms[1:]
            c_nms = c_nms[1:]
            s_nms = s_nms[1:]
            if masks is not None:
                m_nms = m_nms[1:]
            if keypoints is not None and keypoint_confs is not None:
                k_nms = k_nms[1:]
                kc_nms = kc_nms[1:]

            if is_soft:
                # Soft-NMS
                if use_exp:
                    # score refresh formula:
                    # score = score * exp(-(iou^2)/sigma)
                    s_nms = s_nms * np.exp(-(iou * iou) / sigma)
                else:
                    # score refresh formula:
                    # score = score * (1 - iou) if iou > threshold
                    depress_mask = np.where(iou > iou_threshold)[0]
                    s_nms[depress_mask] = s_nms[depress_mask] * (1 - iou[depress_mask])
                keep_mask = np.where(s_nms >= confidence)[0]
            else:
                # normal Hard-NMS
                keep_mask = np.where(iou <= iou_threshold)[0]

            # keep needed box for next loop
            b_nms = b_nms[keep_mask]
            c_nms = c_nms[keep_mask]
            s_nms = s_nms[keep_mask]
            if masks is not None:
                m_nms = m_nms[keep_mask]
            if keypoints is not None and keypoint_confs is not None:
                k_nms = k_nms[keep_mask]
                kc_nms = kc_nms[keep_mask]

    # reformat result for output
    nboxes = np.array(nboxes)
    nclasses = np.array(nclasses)
    nscores = np.array(nscores)
    nmasks = np.array(nmasks)
    nkpts = np.array(nkpts)
    nkptcnfs = np.array(nkptcnfs)
    return nboxes, nclasses, nscores, nmasks, nkpts, nkptcnfs


def box_diou(boxes: np.ndarray, dtype: str) -> np.ndarray:
    """
    Calculate DIoU value of 1st box with other boxes of a box array
    Reference Paper:
        "Distance-IoU Loss: Faster and Better Learning for
        Bounding Box Regression"
        https://arxiv.org/abs/1911.08287

    Args:
        boxes (np.ndarray): Array of bounding boxes in xyxy format.
        dtype (str): Data type of the model output.

    Returns:
        diou (np.ndarray): Array of DIoU values.
    """
    # get box coordinate and area
    x_pos = boxes[:, 0]
    y_pos = boxes[:, 1]
    wid = boxes[:, 2]
    hei = boxes[:, 3]
    areas = wid * hei
    areas[areas == np.inf] = np.finfo(dtype).max  # account for possible overflow

    # check IoU
    inter_xmin = np.maximum(x_pos[1:], x_pos[0])
    inter_ymin = np.maximum(y_pos[1:], y_pos[0])
    inter_xmax = np.minimum(x_pos[1:] + wid[1:], x_pos[0] + wid[0])
    inter_ymax = np.minimum(y_pos[1:] + hei[1:], y_pos[0] + hei[0])

    inter_w = np.maximum(0.0, inter_xmax - inter_xmin + 1)
    inter_h = np.maximum(0.0, inter_ymax - inter_ymin + 1)

    inter = inter_w * inter_h
    iou = inter / (areas[1:] + areas[0] - inter)
    iou[iou == np.inf] = np.finfo(dtype).max  # account for possible overflow

    # box center distance
    x_center = x_pos + wid / 2
    y_center = y_pos + hei / 2
    center_distance = np.power(x_center[1:] - x_center[0], 2) + np.power(
        y_center[1:] - y_center[0], 2
    )
    center_distance[center_distance == np.inf] = np.finfo(
        dtype
    ).max  # account for possible overflow

    # get enclosed area
    enclose_xmin = np.minimum(x_pos[1:], x_pos[0])
    enclose_ymin = np.minimum(y_pos[1:], y_pos[0])
    enclose_xmax = np.maximum(x_pos[1:] + wid[1:], x_pos[0] + wid[0])
    enclose_ymax = np.maximum(y_pos[1:] + wid[1:], y_pos[0] + wid[0])
    enclose_w = np.maximum(0.0, enclose_xmax - enclose_xmin + 1)
    enclose_h = np.maximum(0.0, enclose_ymax - enclose_ymin + 1)
    # get enclosed diagonal distance
    enclose_diagonal = np.power(enclose_w, 2) + np.power(enclose_h, 2)
    enclose_diagonal[enclose_diagonal == np.inf] = np.finfo(
        dtype
    ).max  # account for possible overflow
    # calculate DIoU, add epsilon in denominator to avoid dividing by 0
    diou = iou - 1.0 * (center_distance) / (enclose_diagonal + np.finfo(float).eps)

    return diou


def clamp(val: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    """Clamp a value between a minimum and maximum value.

    Args:
        x (float): The value to be clamped.
        minimum (float): The minimum value, defaults to 0.0.
        maximum (float): The maximum value, defaults to 1.0.

    Returns:
        float: The clamped value.
    """
    return max(minimum, min(val, maximum))
