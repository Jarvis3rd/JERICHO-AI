#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   test_tag.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Datature Project API Test Cases.
"""

import unittest
from unittest.mock import ANY, MagicMock

from datature.nexus.api.tag import Tag
from datature.nexus.client_context import ClientContext

# pylint: disable=W0212


class TestTag(unittest.TestCase):
    """Datature Tag API Resource Test Cases."""

    def __init__(self, *args, **kwargs):
        """init global variables."""
        unittest.TestCase.__init__(self, *args, **kwargs)

        context = ClientContext("secret_key", endpoint="http://localhost:8080")
        context.project_id = "project_id"
        context.requester._request = MagicMock()

        self.tags = Tag(context)

    def test_list(self):
        """Test list tags."""
        self.tags.list()

        self.tags._context.requester._request.assert_called_once_with(
            "GET", "/projects/project_id/tags", ANY, query=None, request_params=None
        )

    def test_create(self):
        """Test create a tag."""
        self.tags.create({"name": "New Tag Name"})

        self.tags._context.requester._request.assert_called_once_with(
            "POST",
            "/projects/project_id/tags",
            ANY,
            request_body={"name": "New Tag Name"},
            query=None,
            request_params=None,
        )

    def test_create_with_metadata(self):
        """Test create a tag with metadata."""
        self.tags.create({"name": "New Tag Name", "color": "#000000"})

        self.tags._context.requester._request.assert_called_once_with(
            "POST",
            "/projects/project_id/tags",
            ANY,
            request_body={"name": "New Tag Name", "color": "#000000"},
            query=None,
            request_params=None,
        )

    def test_update(self):
        """Test update a tag."""
        self.tags.update(1, {"name": "New Tag Name"})

        self.tags._context.requester._request.assert_called_once_with(
            "PATCH",
            "/projects/project_id/tags/1",
            ANY,
            request_body={"name": "New Tag Name"},
            query=None,
            request_params=None,
        )

    def test_update_with_metadata(self):
        """Test update a tag with metadata."""
        self.tags.update(1, {"name": "New Tag Name", "color": "#000000"})

        self.tags._context.requester._request.assert_called_once_with(
            "PATCH",
            "/projects/project_id/tags/1",
            ANY,
            request_body={"name": "New Tag Name", "color": "#000000"},
            query=None,
            request_params=None,
        )

    def test_delete(self):
        """Test delete a tag."""
        self.tags.delete(1)

        self.tags._context.requester._request.assert_called_once_with(
            "DELETE", "/projects/project_id/tags/1", ANY
        )

    def test_merge(self):
        """Test merge a tag."""
        self.tags.merge(1, 0)

        self.tags._context.requester._request.assert_called_once_with(
            "POST",
            "/projects/project_id/tags/1-0:merge",
            ANY,
            query=None,
            request_body=None,
            request_params=None,
        )
