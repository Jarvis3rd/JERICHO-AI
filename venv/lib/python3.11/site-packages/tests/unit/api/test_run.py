#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   test_run.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Datature Run API Test Cases
"""

import unittest
from unittest.mock import ANY, MagicMock

from datature.nexus.api.run import Run
from datature.nexus.client_context import ClientContext

# pylint: disable=W0212


class TestRun(unittest.TestCase):
    """Datature Run API Resource Test Cases."""

    def __init__(self, *args, **kwargs):
        """init global variables."""
        unittest.TestCase.__init__(self, *args, **kwargs)

        context = ClientContext("secret_key", endpoint="http://localhost:8080")
        context.project_id = "project_id"
        context.requester._request = MagicMock()

        self.runs = Run(context)

    def test_list(self):
        """Test list training."""
        self.runs.list()

        self.runs._context.requester._request.assert_called_once_with(
            "GET", "/projects/project_id/runs", ANY, query=None, request_params=None
        )

    def test_retrieve(self):
        """Test retrieve a training."""
        self.runs.get("run_id")

        self.runs._context.requester._request.assert_called_once_with(
            "GET",
            "/projects/project_id/runs/run_id",
            ANY,
            query=None,
            request_params=None,
        )

    def test_kill(self):
        """Test kill a training."""
        self.runs.kill("run_id")

        self.runs._context.requester._request.assert_called_once_with(
            "PATCH",
            "/projects/project_id/runs/run_id",
            ANY,
            request_body={"status": "Cancelled"},
            query=None,
            request_params=None,
        )

    def test_start(self):
        """Test start a training."""
        self.runs.start(
            "flow_id",
            {
                "accelerator": {"name": "GPU_T4", "count": 1},
                "checkpoint": {
                    "strategy": "STRAT_LOWEST_VALIDATION_LOSS",
                    "evaluation_interval": 250,
                    "metric": "Loss/total_loss",
                },
                "limit": {"metric": "LIM_MINUTE", "value": 260},
                "preview": True,
                "matrix": True,
            },
        )

        self.runs._context.requester._request.assert_called_once_with(
            "POST",
            "/projects/project_id/runs",
            ANY,
            request_body={
                "flowId": "flow_id",
                "execution": {
                    "accelerator": {"name": "GPU_T4", "count": 1},
                    "checkpoint": {
                        "strategy": "STRAT_LOWEST_VALIDATION_LOSS",
                        "evaluationInterval": 250,
                        "metric": "Loss/total_loss",
                    },
                    "limit": {"metric": "LIM_MINUTE", "value": 260},
                    "debug": False,
                },
                "features": {"preview": True, "matrix": True},
            },
            query=None,
            request_params=None,
        )

    def test_log(self):
        """Test retrieve a training log."""
        self.runs.get_logs("runlog_id")

        self.runs._context.requester._request.assert_called_once_with(
            "GET",
            "/projects/project_id/runs/logs/runlog_id",
            ANY,
            query=None,
            request_params=None,
        )

    def test_get_confusion_matrix(self):
        """Test retrieve a training log."""
        self.runs.get_confusion_matrix("run_id")

        self.runs._context.requester._request.assert_called_once_with(
            "GET",
            "/projects/project_id/runs/run_id/confusionMatrix",
            ANY,
            query=None,
            request_params=None,
        )
