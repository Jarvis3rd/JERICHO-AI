#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   nii_processor.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Nii Processor
"""

import shutil
import tempfile
from os import makedirs, path
from pathlib import Path
from typing import List

import cv2
import matplotlib.image as mpImage
import nibabel as nib
import numpy as np

from datature.nexus import error

from .base_processor import BaseProcessor


class NiiProcessor(BaseProcessor):
    """Nii processor class"""

    def valid(self, request_data):
        """Valid the input

        :param request_data: The request data, include file path.
        :return: None.
        """
        file_path = request_data.get("file")

        if not file_path:
            raise error.BadRequestError("Required field, must include file path")

    def process(self, request_data) -> List[str]:
        """Start process file to asset video

        :param request_data: The request data, include file path.
        :return: str: The generate video path.
        """
        out_path = tempfile.mkdtemp()

        file_path = request_data.get("file")
        orientation = request_data.get("options", {}).get("nifti_orientation", None)

        file_name = Path(file_path).stem

        video_output = path.join(out_path, file_name)

        if not path.exists(video_output):
            makedirs(video_output)

        scan = nib.load(file_path)

        # Read data and get scan's shape
        scan_array = scan.get_fdata()

        # Get image pixel
        scan_headers = scan.header
        pix_dim = scan_headers["pixdim"][1:4]

        # Calculate new image dimensions from aspect ratio
        new_scan_dims = np.multiply(scan_array.shape, pix_dim)
        new_scan_dims = (
            round(new_scan_dims[0]),
            round(new_scan_dims[1]),
            round(new_scan_dims[2]),
        )

        # if client provide the orientation
        if orientation and orientation in ["x", "y", "z"]:
            output_file_path = f"{video_output}/{file_name}-{orientation}.mp4"

            self.__write_video(scan_array, new_scan_dims, orientation, output_file_path)

            return [output_file_path]

        # if not then save all orientations
        output_file_paths = []
        for orientation in ["x", "y", "z"]:
            output_file_path = f"{video_output}/{file_name}-{orientation}.mp4"

            self.__write_video(scan_array, new_scan_dims, orientation, output_file_path)

            output_file_paths.append(output_file_path)
        return output_file_paths

    def __write_video(self, scan_array, scan_dims, orientation, saved_path):
        """Write video to file

        :param scan_array: The NIfTI scan array data.
        :param scan_dims: The image dimensions of the file.
        :param orientation: The orientation of the pics.
        :param saved_path: The saved file path.
        """
        axis = {"x": 0, "y": 1, "z": 2}[orientation]
        size = {
            "x": [scan_dims[2], scan_dims[1]],
            "y": [scan_dims[2], scan_dims[0]],
            "z": [scan_dims[1], scan_dims[0]],
        }[orientation]

        four_cc = cv2.VideoWriter_fourcc(*"mp4v")
        video_writer = cv2.VideoWriter(saved_path, four_cc, 30.0, size)

        cache_path = tempfile.mkdtemp()

        for i in range(scan_array.shape[axis]):
            # Get slice along the correct axis and resize
            slice_axis = scan_array.take(i, axis=axis)

            # Convert to Grayscale and write to video file
            mpImage.imsave(
                f"{cache_path}/{orientation}-{str(i)}.png", slice_axis, cmap="gray"
            )
            new_image = cv2.imread(f"{cache_path}/{orientation}-{str(i)}.png")

            new_image = cv2.resize(new_image, size)
            video_writer.write(new_image)
        shutil.rmtree(cache_path)
        video_writer.release()
