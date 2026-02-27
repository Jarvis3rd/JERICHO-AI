#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   dicom_processor.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Dicom Processor
"""

import tempfile
from os import makedirs, path
from pathlib import Path
from typing import List

import cv2
from pydicom import config, dcmread

from datature.nexus import error

from .base_processor import BaseProcessor

# Enforcing Valid DICOM
config.settings.reading_validation_mode = config.RAISE


class DicomProcessor(BaseProcessor):
    """DICOM processor class"""

    def valid(self, request_data):
        """Valid the input

        :param request_data: The request data, include file path.
        :return: None.
        """
        file_path = request_data.get("file")

        if not file_path:
            raise error.BadRequestError("Required field")

    def process(self, request_data) -> List[str]:
        """Start process file to asset video

        :param request_data: The request data, include file path.
        :return: str: The generate video path.
        """
        out_path = tempfile.mkdtemp()
        file_path = request_data.get("file")

        file_name = Path(file_path).stem

        video_output = path.join(out_path, file_name)

        if not path.exists(video_output):
            makedirs(video_output)

        dicom_data = dcmread(file_path)

        four_cc = cv2.VideoWriter_fourcc(*"mp4v")

        number_of_frames = int(dicom_data.get("NumberOfFrames", 1))

        # if only contain one image, convert to image.
        if number_of_frames == 1:
            cv2.imwrite(f"{video_output}/{file_name}.png", dicom_data.pixel_array)

            return [f"{video_output}/{file_name}.png"]

        video_writer = cv2.VideoWriter(
            f"{video_output}/{file_name}.mp4",
            four_cc,
            30.0,
            (dicom_data.Rows, dicom_data.Columns),
        )

        for _, image in enumerate(dicom_data.pixel_array):
            new_image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            video_writer.write(new_image)

        video_writer.release()

        return [f"{video_output}/{file_name}.mp4"]
