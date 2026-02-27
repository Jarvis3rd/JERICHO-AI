#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   multipart.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Datature Asset Multipart Handler
"""

import os
from typing import List

from datature.nexus.api.types import AssetFilePart


class MultipartHandler:
    """Handles splitting files for multipart upload."""

    def __init__(self, file_path: str, part_count: int = 1) -> None:
        """
        Initialize the MultipartHandler.

        :param file_path: Path to the file to upload
        :param part_count: Number of parts to split the file into
        """
        self.file_path = file_path
        self.file_size = os.path.getsize(file_path)
        self.part_count = part_count
        self.parts = self._split_file_into_parts()

    def _split_file_into_parts(self) -> List[AssetFilePart]:
        """Split the file into parts for multipart upload."""
        parts = []
        part_size = self.file_size // self.part_count

        for i in range(self.part_count):
            start_byte = i * part_size
            end_byte = (
                start_byte + part_size if i < self.part_count - 1 else self.file_size
            )

            parts.append(
                AssetFilePart(
                    part_number=i + 1,
                    start_byte=start_byte,
                    end_byte=end_byte,
                )
            )

        return parts

    def read_part_data(self, part: AssetFilePart) -> bytes:
        """
        Read the data for a specific part.

        :param part: The part to read
        :return: Bytes data of the part
        """
        with open(self.file_path, "rb") as f:
            f.seek(part.start_byte)
            return f.read(part.end_byte - part.start_byte)
