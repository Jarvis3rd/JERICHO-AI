# !/usr/env/bin python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   models.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Custom model msgspec response.
"""

from datature.nexus.models import NexusStruct, UploadSignedUrl


class UploadSessionModelMetadata(NexusStruct):
    """
    Describes the metadata for an custom model to be uploaded in a session.

    Attributes:
        filename (str): Name of the file.
    """

    filename: str


class UploadSession(NexusStruct):
    """
    Represents an upload session, including its identifier and the custom model to be uploaded.

    Attributes:
        id (str): Unique identifier of the upload session.
        metadata (UploadSessionModelMetadata): Metadata of the custom model to be uploaded.
        upload (UploadSignedUrl): Signed URL for uploading the custom model.
    """

    id: str
    metadata: UploadSessionModelMetadata
    upload: UploadSignedUrl
