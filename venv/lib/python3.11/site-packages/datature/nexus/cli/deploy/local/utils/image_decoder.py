#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   image_decoder.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Image decoder.
"""

import base64
import os
import tempfile
from typing import Any, Dict, Optional

import cv2
import nibabel as nib
import numpy as np

from datature.nexus.cli.deploy.local.types.prediction_request import ResponseFormat


def decode_image_from_base64(
    data: str, response_format: Optional[ResponseFormat] = None
) -> Dict[str, Any]:
    """Decode image from base64 string.

    Args:
        data: The base64 encoded string.
        response_format: The response format.

    Returns:
        Dictionary containing the image and optionally the affine matrix for NIFTI files.
    """
    parts = data.split(",")
    if len(parts) > 1:
        image = parts[1]
    else:
        image = data

    decoded_image = base64.b64decode(image)

    if response_format == ResponseFormat.NIFTI:
        with tempfile.NamedTemporaryFile(suffix=".nii.gz", delete=False) as temp_file:
            temp_file.write(decoded_image)
            temp_path = temp_file.name

        try:
            nii_image = nib.nifti1.load(temp_path)
            return {
                "image": nii_image.get_fdata(),
                "affine": nii_image.affine,
            }

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    bgr_image = cv2.imdecode(np.frombuffer(decoded_image, np.uint8), cv2.IMREAD_COLOR)
    rgb_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)

    return {"image": rgb_image}


def decode_image_from_path(data: str) -> Dict[str, Any]:
    """Decode image from path.

    Args:
        data: The path to the image.

    Returns:
        Dictionary containing the image and optionally the affine matrix for NIFTI files.
    """
    if data.endswith(".nii.gz"):
        nii_image = nib.nifti1.load(data)

        return {
            "image": nii_image.get_fdata(),
            "affine": nii_image.affine,
        }

    bgr_image = cv2.imread(data)
    rgb_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)

    return {"image": rgb_image}


def decode_image_from_bytes(
    data: bytes, response_format: Optional[ResponseFormat] = None
) -> Dict[str, Any]:
    """Decode image from bytes.

    Args:
        data: The bytes of the image.
        response_format: The response format.

    Returns:
        Dictionary containing the image and optionally the affine matrix for NIFTI files.
    """
    if response_format == ResponseFormat.NIFTI:
        with tempfile.NamedTemporaryFile(suffix=".nii.gz", delete=False) as temp_file:
            temp_file.write(data)
            temp_path = temp_file.name

        try:
            nii_image = nib.nifti1.load(temp_path)
            return {
                "image": nii_image.get_fdata(),
                "affine": nii_image.affine,
            }

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    bgr_image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    rgb_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)

    return {"image": rgb_image}
