#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   test_ontology.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Datature Ontology API Test Cases
"""
# pylint: disable=W0212

import unittest
from unittest.mock import ANY, MagicMock

from datature.nexus.api.ontology import Ontology
from datature.nexus.client_context import ClientContext


class TestOntology(unittest.TestCase):
    """Datature Ontology API Resource Test Cases."""

    def __init__(self, *args, **kwargs):
        """init global variables."""
        unittest.TestCase.__init__(self, *args, **kwargs)

        context = ClientContext("secret_key", endpoint="http://localhost:8080")
        context.project_id = "project_id"
        context.requester._request = MagicMock()

        self.ontology = Ontology(context)

    def test_list_schemas(self):
        """Test list ontology schemas."""
        self.ontology.list_schemas()

        self.ontology._context.requester._request.assert_called_once_with(
            "GET",
            "/projects/project_id/ontologies",
            ANY,
            query=None,
            request_params=None,
        )
