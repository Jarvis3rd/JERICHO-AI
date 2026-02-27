#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   prediction_response.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Prediction response type.
"""

from typing import Any, Dict, List, Optional, Union

from msgspec import Struct


class Tag(Struct, kw_only=True, omit_defaults=True, rename="camel"):
    """
    Tag object.

    Attributes:
        name: The name of the tag.
        id: The id of the tag.
        color: The color of the tag.
    """

    name: str
    id: Optional[int] = None
    color: Optional[str] = None


class Medical3DImage(Struct, kw_only=True, rename="camel"):
    """
    Image object.

    Attributes:
        encoding: The base64 encoding of the image.
        file: The file name of the image.
    """

    encoding: str = "NiiGz"
    file: str


class BitmaskCOCORLE(Struct, kw_only=True, rename="camel"):
    """
    COCORLE mask object.

    Attributes:
        encoding: The encoding of the mask.
        height: The height of the mask.
        width: The width of the mask.
        counts: The counts of the mask.
    """

    encoding: str = "CocoRleMask"
    height: int
    width: int
    counts: Union[List[int], str]


class BitmaskNiiGz(Struct, kw_only=True, rename="camel"):
    """
    Bitmask 3D object.
    """

    encoding: str = "NiiGz"
    file: str


Bitmask2D = BitmaskCOCORLE
Bitmask3D = BitmaskNiiGz


class Prediction(Struct, kw_only=True, omit_defaults=True, rename="camel"):
    """
    Prediction object.

    Attributes:
        annotation_id: The id of the annotation.
        confidence: The confidence of the prediction.
        tag: The tag of the prediction.
        bound: The bound of the prediction.
        bound_type: The type of the bound.
        contour: The contour of the prediction.
        contour_type: The type of the contour.
        skeleton: The skeleton of the prediction.
        keypoints: The keypoints of the prediction.
        keypoint_confidences: The keypoint confidences of the prediction.
        bitmask: The bitmask of the prediction.
    """

    annotation_id: int
    confidence: float
    tag: Tag
    bound: Optional[List[List[float]]] = None
    bound_type: Optional[str] = None
    contour: Optional[List[List[float]]] = None
    contour_type: Optional[str] = None
    skeleton: Optional[Dict[str, Any]] = None
    keypoints: Optional[List[List[float]]] = None
    keypoint_confidences: Optional[List[float]] = None
    bitmask: Optional[Union[Bitmask2D, Bitmask3D]] = None


class PredictionResponse(Struct, kw_only=True, omit_defaults=True, rename="camel"):
    """
    Prediction response object.

    Attributes:
        predictions: The predictions of the response.
        avg_entropy: The average entropy of the response.
        avg_entropy_for_class: The average entropy for each class of the response.
        image: The image of the response.
        warnings: The warnings of the response.
    """

    predictions: Optional[List[Prediction]] = None
    avg_entropy: Optional[float] = None
    avg_entropy_for_class: Optional[Dict[str, float]] = None
    image: Optional[Medical3DImage] = None
    warnings: Optional[List[str]] = None


class APIDeploymentPredictionResponse(
    Struct, kw_only=True, omit_defaults=True, rename="camel"
):
    """
    API deployment prediction response object.

    Attributes:
        tags: The tags of the response.
        response: The response of the prediction.
    """

    tags: Dict[str, Tag]
    response: PredictionResponse
