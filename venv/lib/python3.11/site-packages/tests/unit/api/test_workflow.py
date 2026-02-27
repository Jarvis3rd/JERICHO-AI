#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   test_workflow.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Datature Workflow API Test Cases
"""

import unittest
from unittest.mock import ANY, MagicMock

from datature.nexus.api.workflow import Workflow
from datature.nexus.client_context import ClientContext

# pylint: disable=W0212


class TestWorkflow(unittest.TestCase):
    """Datature Workflow API Resource Test Cases."""

    def __init__(self, *args, **kwargs):
        """init global variables."""
        unittest.TestCase.__init__(self, *args, **kwargs)

        context = ClientContext("secret_key", endpoint="http://localhost:8080")
        context.project_id = "project_id"
        context.requester._request = MagicMock()

        self.workflow = Workflow(context)

    def test_list(self):
        """Test list all workflows."""
        self.workflow.list()

        self.workflow._context.requester._request.assert_called_once_with(
            "GET",
            "/projects/project_id/workflows",
            ANY,
            query=None,
            request_params=None,
        )

    def test_retrieve(self):
        """Test retrieve a workflow."""
        self.workflow.get("flow_id")

        self.workflow._context.requester._request.assert_called_once_with(
            "GET",
            "/projects/project_id/workflows/flow_id",
            ANY,
            query=None,
            request_params=None,
        )

    def test_modify(self):
        """Test update a workflow."""
        self.workflow.update("flow_id", {"title": "New Workflow Title"})

        self.workflow._context.requester._request.assert_called_once_with(
            "PATCH",
            "/projects/project_id/workflows/flow_id",
            ANY,
            request_body={"title": "New Workflow Title"},
            query=None,
            request_params=None,
        )

    def test_delete(self):
        """Test delete a workflow."""
        self.workflow.delete("flow_id")

        self.workflow._context.requester._request.assert_called_once_with(
            "DELETE", "/projects/project_id/workflows/flow_id", ANY
        )
