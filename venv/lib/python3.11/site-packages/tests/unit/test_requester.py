#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   test_requester.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Datature HTTP Resource Test Cases
"""

import unittest
from unittest.mock import MagicMock

from datature.nexus import models
from datature.nexus.error import (
    BadRequestError,
    ForbiddenError,
    InternalServerError,
    NotFoundError,
    TooManyRequestsError,
    UnauthorizedError,
)
from datature.nexus.requester import Requester
from tests.unit.fixture.data import error_fixture, operation_fixture
from tests.unit.fixture.mock import MockResponse

# pylint: disable=W0703,W0012,W0212


class TestRequester(unittest.TestCase):
    """Datature HTTP Resource Test Cases."""

    def test_request_with_no_project_key(self):
        """Test resource request."""

        try:
            Requester(secret_key=None, endpoint="")._request(
                "GET",
                "test_end_point",
                response_type=models.Artifacts,
                request_body={"test": "test"},
            )

        except Exception as exception:
            assert isinstance(exception, UnauthorizedError)

    def test_request_with_request_body(self):
        """Test resource request."""
        requester = Requester("secret-key", endpoint="")
        requester._session.request = MagicMock()

        requester._session.request.side_effect = [
            MockResponse(operation_fixture.pending_operation_response, 200)
        ]
        requester._interpret_response = MagicMock()

        requester._request(
            "POST",
            "test_end_point",
            response_type=models.Operation,
            request_body={"test": "test"},
        )

    def test_request_with_query(self):
        """Test resource request."""
        requester = Requester("secret-key", endpoint="")

        requester._session.request = MagicMock()
        requester._session.request.side_effect = [
            MockResponse(operation_fixture.pending_operation_response, 200)
        ]

        response = requester.GET(
            "test_end_poimt", query={"limit": 5}, response_type=models.Operation
        )

        assert response.id == "op_c26ea31d-599c-4a03-8b0d-b2bc9995fa8a"

    def test_make_headers_with_get_method(self):
        """Test make headers."""

        headers = Requester("project_secret", endpoint="")._make_headers("GET", {})

        assert headers["Secret-Key"] == "project_secret"

    def test_make_headers_with_post_method(self):
        """Test make headers with post method."""

        headers = Requester("project_secret", endpoint="")._make_headers("POST", {})

        assert headers["Secret-Key"] == "project_secret"
        assert headers["Content-Type"] == "application/json"

    def test_make_headers_with_supplied_headers(self):
        """Test make headers with supplied headers."""

        headers = Requester("project_secret", endpoint="")._make_headers(
            "GET", {"Connection": "keep-alive", "Accept": "*/*"}
        )

        assert headers["Secret-Key"] == "project_secret"
        assert headers["Accept"] == "*/*"

    def test_interpret_response_with_400(self):
        """Test interpret response with 400 code."""

        try:
            Requester("secret-key", endpoint="")._interpret_response(
                MockResponse(error_fixture.forbidden_error_response, 400)
            )

        except Exception as exception:
            assert isinstance(exception, BadRequestError)

    def test_interpret_response_with_403(self):
        """Test interpret response with 403 code."""

        try:
            Requester("secret-key", endpoint="")._interpret_response(
                MockResponse(error_fixture.forbidden_error_response, 403)
            )

        except Exception as exception:
            assert isinstance(exception, ForbiddenError)

    def test_interpret_response_with_404(self):
        """Test interpret response with 404 code."""

        try:
            Requester("secret-key", endpoint="")._interpret_response(
                MockResponse(error_fixture.not_found_error_response, 404)
            )

        except Exception as exception:
            assert isinstance(exception, NotFoundError)

    def test_interpret_response_with_429(self):
        """Test interpret response with 429 code."""

        try:
            Requester("secret-key", endpoint="")._interpret_response(
                MockResponse(error_fixture.too_many_requests_error_response, 429)
            )

        except Exception as exception:
            assert isinstance(exception, TooManyRequestsError)

    def test_interpret_response_with_500(self):
        """Test interpret response with 500 code."""

        try:
            Requester("secret-key", endpoint="")._interpret_response(
                MockResponse(error_fixture.internal_server_error_response, 500)
            )

        except Exception as exception:
            assert isinstance(exception, InternalServerError)

    def test_make_query_string(self):
        """Test make querystring."""

        none_res = Requester("secret-key", endpoint="")._make_query_string(None)

        assert none_res == ""

        res = Requester("secret-key", endpoint="")._make_query_string(
            {
                "limit": 5,
                "offset": 0,
                "group": ["group1", "group2"],
                "includeExports": True,
            }
        )

        assert (
            res == "limit=5&offset=0&group[]=group1&group[]=group2&includeExports=true&"
        )
