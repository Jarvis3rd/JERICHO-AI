#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   test_deploy.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Datature Deploy API Test Cases
"""

import unittest
from unittest.mock import ANY, MagicMock

from datature.nexus.api.deployment import Deployment
from datature.nexus.client_context import ClientContext

# pylint: disable=W0212


class TestDeploy(unittest.TestCase):
    """Datature Deploy API Resource Test Cases."""

    def __init__(self, *args, **kwargs):
        """init global variables."""
        unittest.TestCase.__init__(self, *args, **kwargs)

        context = ClientContext("secret_key", endpoint="http://localhost:8080")
        context.project_id = "project_id"
        context.requester._request = MagicMock()

        self.deployment = Deployment(context)

    def test_list(self):
        """Test list all deployments."""
        self.deployment.list()

        self.deployment._context.requester._request.assert_called_once_with(
            "GET",
            "/projects/project_id/deployments",
            ANY,
            query=None,
            request_params=None,
        )

    def test_get(self):
        """Test get a deployment."""
        self.deployment.get("deploy_id")

        self.deployment._context.requester._request.assert_called_once_with(
            "GET",
            "/projects/project_id/deployments/deploy_id",
            ANY,
            query=None,
            request_params=None,
        )

    def test_delete(self):
        """Test delete a deployment."""
        self.deployment.delete("deploy_id")

        self.deployment._context.requester._request.assert_called_once_with(
            "DELETE", "/projects/project_id/deployments/deploy_id", ANY
        )

    def test_create(self):
        """Test create a deployment."""
        self.deployment.create(
            {
                "name": "name",
                "model_id": "model_id",
                "replicas": 1,
                "resources": {"GPU_T4": 1},
                "options": {"evaluation_strategy": "evaluation_strategy"},
            }
        )

        self.deployment._context.requester._request.assert_called_once_with(
            "POST",
            "/projects/project_id/deployments",
            ANY,
            request_body={
                "name": "name",
                "modelId": "model_id",
                "replicas": 1,
                "resources": {"GPU_T4": 1},
                "options": {"evaluationStrategy": "evaluation_strategy"},
            },
            query=None,
            request_params=None,
        )

    def test_update(self):
        """Test update a deployment."""
        self.deployment.update("deploy_id", {"name": "name", "replicas": 2})

        self.deployment._context.requester._request.assert_called_once_with(
            "PATCH",
            "/projects/project_id/deployments/deploy_id",
            ANY,
            request_body={"name": "name", "replicas": 2},
            query=None,
            request_params=None,
        )

    def test_create_version(self):
        """Test create a deployment version."""
        self.deployment.create_version("deploy_id", "name", "artifact_id")

        self.deployment._context.requester._request.assert_called_once_with(
            "POST",
            "/projects/project_id/deployments/deploy_id/versions",
            ANY,
            request_body={
                "versionTag": "name",
                "artifactId": "artifact_id",
            },
            query=None,
            request_params=None,
        )
