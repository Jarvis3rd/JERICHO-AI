#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   prediction_request.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Prediction request types.
"""

from enum import Enum
from typing import Optional

from msgspec import Struct


class ResponseFormat(Enum):
    """
    Response format enum.
    """

    CLASSIFICATION = "classification"
    RECTANGLE = "rectangle"
    POLYGON = "polygon"
    BITMASK = "bitmask"
    KEYPOINT = "keypoint"
    NIFTI = "nifti"


class PredictRequest(Struct, kw_only=True, rename="camel"):
    """
    Predict request object.

    Attributes:
        project: The project of the request.
        data: The data of the request.
        encoding: The encoding of the request.
        mime_type: The mime type of the request.
    """

    project: Optional[str] = None
    data: Optional[str] = None
    encoding: Optional[str] = None
    mime_type: Optional[str] = None
    response_format: Optional[ResponseFormat] = None
