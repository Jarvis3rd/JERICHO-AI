#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   test_operation.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Datature Operation API Test Cases
"""

import json
import unittest
from unittest.mock import ANY, MagicMock, patch

import msgspec

from datature.nexus import models
from datature.nexus.api.operation import Operation
from datature.nexus.client_context import ClientContext
from datature.nexus.error import Error
from tests.unit.fixture.data import operation_fixture

# pylint: disable=W0212


class TestOperation(unittest.TestCase):
    """Datature Operation API Resource Test Cases."""

    def __init__(self, *args, **kwargs):
        """init global variables."""
        unittest.TestCase.__init__(self, *args, **kwargs)

        context = ClientContext("secret_key", endpoint="http://localhost:8080")
        context.project_id = "project_id"
        context.requester._request = MagicMock()

        self.operation = Operation(context)

    def test_retrieve(self):
        """Test retrieve an operation."""
        self.operation.get("op_id")

        self.operation._context.requester._request.assert_called_once_with(
            "GET",
            "/projects/project_id/operations/op_id",
            ANY,
            query=None,
            request_params=None,
        )

    @patch("datature.nexus.api.operation.config")
    def test_wait_until_done(self, patch_config):
        """Test looping an operation."""
        patch_config.OPERATION_LOOPING_DELAY_SECONDS = 1

        self.operation._context.requester._request.side_effect = [
            msgspec.json.decode(
                json.dumps(operation_fixture.pending_operation_response),
                type=models.Operation,
            ),
            msgspec.json.decode(
                json.dumps(operation_fixture.finished_operation_response),
                type=models.Operation,
            ),
        ]

        self.operation.wait_until_done("op_id", raise_exception_if="Errored")

    @patch("datature.nexus.api.operation.config")
    def test_wait_until_done_with_status_error(self, patch_config):
        """Test looping an operation with error."""
        patch_config.OPERATION_LOOPING_DELAY_SECONDS = 1
        self.operation._context.requester._request.side_effect = [
            msgspec.json.decode(
                json.dumps(operation_fixture.errored_operation_response),
                type=models.Operation,
            ),
        ]

        try:
            self.operation.wait_until_done("op_id")
        # pylint: disable=W0703
        except Exception as exception:
            assert isinstance(exception, Error)

    @patch("datature.nexus.api.operation.config")
    def test_wait_until_done_with_timeout(self, patch_config):
        """Test looping an operation with timeout."""
        patch_config.OPERATION_LOOPING_DELAY_SECONDS = 1
        self.operation._context.requester._request.return_value = msgspec.json.decode(
            json.dumps(operation_fixture.pending_operation_response),
            type=models.Operation,
        )

        op = self.operation.wait_until_done("op_id", timeout=6)

        assert op.status.overview == "Running"
