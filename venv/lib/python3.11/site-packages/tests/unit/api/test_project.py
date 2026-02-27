#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   test_project.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Datature Project API Test Cases
"""

import unittest
from unittest.mock import ANY, MagicMock

from datature.nexus.api.project import Project
from datature.nexus.client_context import ClientContext

# pylint: disable=W0212


class TestProject(unittest.TestCase):
    """Datature Project API Resource Test Cases."""

    def __init__(self, *args, **kwargs):
        """init global variables."""
        unittest.TestCase.__init__(self, *args, **kwargs)

        context = ClientContext("secret_key", endpoint="http://localhost:8080")
        context.project_id = "project_id"
        context.requester._request = MagicMock()

        self.project = Project(context)

    def test_retrieve(self):
        """Test retrieve a project."""
        self.project.get_info()

        self.project._context.requester._request.assert_called_once_with(
            "GET", "/projects/project_id", ANY, query=None, request_params=None
        )

    def test_modify(self):
        """Test update a project."""

        self.project.update({"name": "New Project Name"})

        self.project._context.requester._request.assert_called_once_with(
            "PATCH",
            "/projects/project_id",
            ANY,
            request_body={"name": "New Project Name"},
            query=None,
            request_params=None,
        )

    def test_insight(self):
        """Test retrieve a project insight."""
        self.project.list_insights()

        self.project._context.requester._request.assert_called_once_with(
            "GET", "/projects/project_id/insights", ANY, query=None, request_params=None
        )

    def test_users(self):
        """Test retrieve project users."""
        self.project.list_users()

        self.project._context.requester._request.assert_called_once_with(
            "GET", "/projects/project_id/users", ANY, query=None, request_params=None
        )
