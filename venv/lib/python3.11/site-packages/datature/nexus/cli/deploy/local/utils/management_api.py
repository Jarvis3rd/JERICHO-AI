#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   management_api.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Management API client.
"""

import os

from datature.nexus import Client
from datature.nexus.api.project import Project


class ManagementAPIClient:
    """Management API client."""

    _endpoint: str
    _secret_key: str
    _project_id: str
    _client: Client

    def __init__(self, secret_key: str, project_id: str) -> None:
        self._endpoint = os.getenv("DATATURE_API_BASE_URL", "https://api.datature.io")
        self._secret_key = secret_key
        self._project_id = project_id

        self._client = Client(secret_key=self._secret_key, endpoint=self._endpoint)

    @property
    def project(self) -> Project:
        """Get the project."""
        return self.client.get_project(self._project_id)

    @property
    def project_id(self) -> str:
        """Get the project ID."""
        return self._project_id

    @project_id.setter
    def project_id(self, project_id: str) -> None:
        """Set the project ID."""
        self._project_id = project_id

    @property
    def client(self) -> Client:
        """Get the client."""
        return self._client
