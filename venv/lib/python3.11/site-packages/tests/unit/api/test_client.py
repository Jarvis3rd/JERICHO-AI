#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   test_client.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Datature Project API Test Cases
"""

import json
import unittest
from unittest.mock import ANY, MagicMock

import msgspec

from datature.nexus import Client, models
from datature.nexus.api.project import Project
from tests.unit.fixture.data import projects_fixture

# pylint: disable=W0212


class TestClient(unittest.TestCase):
    """Datature Client Test Cases."""

    def __init__(self, *args, **kwargs):
        """init global variables."""
        unittest.TestCase.__init__(self, *args, **kwargs)

        client = Client("secret_key")
        client._context.requester._request = MagicMock()

        self.client = client

    def test_info(self):
        """Test retrieve workspace info."""
        self.client.get_info()

        self.client._context.requester._request.assert_called_once_with(
            "GET", "/workspace", ANY, query=None, request_params=None
        )

    def test_list_projects(self):
        """Test retrieve workspace projects."""
        self.client._context.requester._request.return_value = msgspec.json.decode(
            json.dumps(projects_fixture.list_projects_response),
            type=models.Projects,
        )

        self.client.list_projects()

    def test_get_project(self):
        """Test retrieve project ."""
        project = self.client.get_project("project")

        assert isinstance(project, Project)
