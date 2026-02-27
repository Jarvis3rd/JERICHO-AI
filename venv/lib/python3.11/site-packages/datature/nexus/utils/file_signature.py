#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   file_signature.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   File Utils module
"""

from typing import List, Optional

# https://en.wikipedia.org/wiki/List_of_file_signatures
signatures = [
    {
        "description": "JPEG raw or in theJFIF orExif file format",
        "file_mime": "image/jpeg",
        "hex": "FF D8 FF DB",
        "offset": 0,
    },
    {
        "description": "JPEG raw or in theJFIF orExif file format",
        "file_mime": "image/jpeg",
        "hex": "FF D8 FF E0 nn nn 4A 46 49 46 00 01",
        "offset": 0,
    },
    {
        "description": "JPEG raw or in theJFIF orExif file format",
        "file_mime": "image/jpeg",
        "hex": "FF D8 FF EE",
        "offset": 0,
    },
    {
        "description": "JPEG raw or in theJFIF orExif file format",
        "file_mime": "image/jpeg",
        "hex": "FF D8 FF E1 nn nn 45 78 69 66 00 00",
        "offset": 0,
    },
    {
        "description": "JPEG raw or in theJFIF orExif file format",
        "file_mime": "image/jpeg",
        "hex": "FF D8 FF E0",
        "offset": 0,
    },
    {
        "description": "JImage encoded in the Portable Network Graphics format",
        "file_mime": "image/png",
        "hex": "89 50 4E 47 0D 0A 1A 0A",
        "offset": 0,
    },
    {
        "description": "ISO Base Media file (MPEG-4)",
        "file_mime": "video/mp4",
        "hex": "66 74 79 70 69 73 6F 6D",
        "offset": 4,
    },
    {
        "description": "MPEG-4 video file",
        "file_mime": "video/mp4",
        "hex": "66 74 79 70 4D 53 4E 56",
        "offset": 4,
    },
    {
        "description": "MPEG-4 video file (ftypmp42)",
        "file_mime": "video/mp4",
        "hex": "66 74 79 70 6D 70 34 32",
        "offset": 4,
    },
    {
        "description": "DICOM Medical File Format",
        "file_mime": "application/dicom",
        "hex": "44 49 43 4D",
        "offset": 128,
    },
    {
        "description": "Single file NIfTI format",
        "file_mime": "application/x-nifti",
        "hex": "6E 2B 31 00",
        "offset": 344,
    },
    {
        "description": "GZip compressed NIfTI",
        "file_mime": "application/x-nifti-gz",
        "hex": "1F 8B 08",
        "offset": 0,
    },
    {
        "description": "ZIP archive containing DICOM 3D data",
        "file_mime": "application/x-dicom-3d-zip",
        "hex": "50 4B 03 04",
        "offset": 0,
    },
]


def compare_sig(file_header: bytes, signature) -> bool:
    """Compare file header with signature.

    :param file_header: file bytes header
    :return: bool
    """
    file_header = list(file_header)

    test_hex: List[Optional[int]] = []
    for _byte in signature["hex"].strip().split(" "):
        if _byte != "nn":
            test_hex.append(ord(bytes.fromhex(_byte)))
        else:
            test_hex.append(None)

    for _loc, _byte in enumerate(test_hex):
        if _byte is None:
            continue
        if _byte != file_header[_loc + signature["offset"]]:
            return False
    return True


def get_file_mime_by_signature(file_bytes: bytes):
    """Get file mime type by signature.

    :param file_bytes: file bytes object
    :return: file mime type
    """
    # get file type by signature
    file_header = file_bytes[:400]

    for signature in signatures:
        if compare_sig(file_header, signature):
            return signature["file_mime"]

    return None
