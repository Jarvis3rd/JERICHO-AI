#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   requester.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   A wrapper to make HTTP requests
"""

import json
import logging
import platform
import time
from functools import wraps
from http.client import IncompleteRead
from typing import List, Optional, Tuple, Type
from urllib.parse import urljoin

import msgspec
from requests import Response, Session
from requests.exceptions import ChunkedEncodingError
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import Timeout as RequestsTimeout

from datature.nexus import config, error
from datature.nexus.version import __version__

system = platform.system()
machine = platform.machine()
python_version = platform.python_version()

logger = logging.getLogger("datature-nexus")

# pylint: disable=C0103,,R0912,R0913,R0914,R0917


def retry_with_exponential_backoff(
    max_retries: int = config.REQUEST_MAX_RETRIES,
    base_delay: float = config.REQUEST_RETRY_DELAY_SECONDS,
    backoff_multiplier: float = config.REQUEST_RETRY_BACKOFF_MULTIPLIER,
    max_delay: float = config.REQUEST_RETRY_MAX_DELAY_SECONDS,
    retryable_exceptions: Tuple[Type[Exception], ...] = (
        RequestsConnectionError,
        RequestsTimeout,
        ChunkedEncodingError,
        IncompleteRead,
        error.NetworkConnectionError,
        error.RequestTimeoutError,
        error.ServiceUnavailableError,
        error.GatewayTimeoutError,
        error.InternalServerError,
    ),
):
    """Retry decorator with exponential backoff.

    :param max_retries: Maximum number of retry attempts
    :param base_delay: Base delay in seconds for the first retry
    :param backoff_multiplier: Multiplier for exponential backoff
    :param max_delay: Maximum delay between retries
    :param retryable_exceptions: Tuple of exception types that should trigger a retry
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        logger.debug(
                            "Max retries (%d) exceeded for %s. Last error: %s",
                            max_retries,
                            func.__name__,
                            str(e),
                        )
                        raise e

                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (backoff_multiplier**attempt), max_delay)

                    logger.debug(
                        "Attempt %d/%d failed for %s: %s. Retrying in %.2f seconds...",
                        attempt + 1,
                        max_retries + 1,
                        func.__name__,
                        str(e),
                        delay,
                    )

                    time.sleep(delay)
                except Exception as e:
                    # For non-retryable exceptions, re-raise immediately
                    raise e

            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
            return None

        return wrapper

    return decorator


def is_retryable_http_status(status_code: int) -> bool:
    """Check if an HTTP status code is retryable.

    :param status_code: HTTP status code
    :return: True if the status code indicates a retryable error
    """
    return status_code in [500, 502, 503, 504, 520, 521, 522, 523, 524]


class Requester:
    """An HTTP requester."""

    _timeout: int
    _base_url: str
    _session: Session
    _cert: Optional[Tuple[str, str]]
    secret_key: Optional[str]

    def __init__(
        self,
        secret_key: Optional[str],
        mtls_certificate_file_path: Optional[str],
        mtls_private_key_file_path: Optional[str],
        endpoint: str,
    ):
        """Create an HTTP requester.

        :param secret_key: The secret key
        :param mtls_certificate_file_path: The path to the mTLS certificate file
        :param mtls_private_key_file_path: The path to the mTLS private key file
        :param endpoint: The base URL for all requests
        """
        self._timeout = config.REQUEST_TIME_OUT_SECONDS
        self._base_url = endpoint

        self._session = Session()

        self._cert = (
            (mtls_certificate_file_path, mtls_private_key_file_path)
            if mtls_certificate_file_path and mtls_private_key_file_path
            else None
        )

        self.secret_key = secret_key

        # Check Secret
        if not secret_key and not self._cert:
            raise AttributeError(
                "Either the secret key or mTLS certificate files are required"
            )

    @retry_with_exponential_backoff()
    def _request(
        self,
        method,
        path,
        response_type,
        query=None,
        request_body=None,
        request_headers=None,
        request_params=None,
        ignore_errno=None,
    ):
        """Create an HTTP requester with retry mechanism.

        :param method: The request method
        :param path: The request path
        :param query: The query object
        :param request_body: The request body
        :param request_headers: If have custom request headers
        :param request_params: The request parameters
        :param ignore_errno: The error codes to ignore
        """
        method = method.upper()
        assert method in ["GET", "HEAD", "DELETE", "POST", "PUT", "PATCH", "OPTIONS"]

        # Assemble queries and request body.
        post_data = None
        post_files = None

        absolute_url = urljoin(self._base_url, path)

        if query:
            encoded_params = self._make_query_string(query)
            absolute_url = f"{absolute_url}?{encoded_params}"

        if request_body:
            post_data = json.dumps(request_body)

        logger.debug("API request: %s %s Body %s", method, absolute_url, post_data)

        try:
            if self._cert:
                response = self._session.request(
                    method,
                    absolute_url,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": f"DatatureSDK/{__version__} "
                        f"(Python/{python_version}; {system}/{machine})",
                    },
                    cert=self._cert,
                    data=post_data,
                    files=post_files,
                    params=request_params,
                    verify=True,
                    timeout=self._timeout,
                )
            else:
                # Assemble request headers
                headers = self._make_headers(method, request_headers)

                # Call request to do a real HTTP call, default timeout 120s
                response = self._session.request(
                    method,
                    absolute_url,
                    headers=headers,
                    cert=None,
                    data=post_data,
                    files=post_files,
                    params=request_params,
                    timeout=self._timeout,
                )

            # Check for retryable HTTP status codes
            if not 200 <= response.status_code < 300 and is_retryable_http_status(
                response.status_code
            ):
                # Convert to appropriate error for retry mechanism
                try:
                    response_data = response.json()
                    error_message = response_data.get(
                        "message", f"HTTP {response.status_code}"
                    )
                except json.JSONDecodeError:
                    response_data = {
                        "message": response.text or f"HTTP {response.status_code}"
                    }
                    error_message = response_data["message"]

                if response.status_code == 503:
                    raise error.ServiceUnavailableError(error_message, response_data)
                if response.status_code == 504:
                    raise error.GatewayTimeoutError(error_message, response_data)

                raise error.InternalServerError(error_message, response_data)

            if not self._interpret_response(response, ignore_errno):
                return None

            logger.debug(
                "API response: %s %s Body %s", method, absolute_url, response.json()
            )

            return msgspec.json.decode(
                json.dumps(response.json()),
                type=response_type,
            )

        except (
            RequestsConnectionError,
            RequestsTimeout,
            ChunkedEncodingError,
            IncompleteRead,
        ) as e:
            # Convert requests exceptions to our custom exceptions for retry mechanism
            if isinstance(e, RequestsConnectionError):
                raise error.NetworkConnectionError(f"Connection error: {str(e)}")
            if isinstance(e, RequestsTimeout):
                raise error.RequestTimeoutError(f"Request timeout: {str(e)}")
            if isinstance(e, (ChunkedEncodingError, IncompleteRead)):
                raise error.NetworkConnectionError(f"Incomplete response: {str(e)}")
            raise

    def GET(
        self, path, response_type, query=None, request_params=None, ignore_errno=None
    ):
        """GET Call."""
        return self._request(
            "GET",
            path,
            response_type,
            query=query,
            request_params=request_params,
            ignore_errno=ignore_errno,
        )

    def POST(
        self,
        path,
        response_type,
        query=None,
        request_body=None,
        request_params=None,
        ignore_errno=None,
    ):
        """POST Call."""
        return self._request(
            "POST",
            path,
            response_type,
            query=query,
            request_body=request_body,
            request_params=request_params,
            ignore_errno=ignore_errno,
        )

    def PUT(
        self,
        path,
        response_type,
        query=None,
        request_body=None,
        request_params=None,
        ignore_errno=None,
    ):
        """PUT Call."""
        return self._request(
            "PUT",
            path,
            response_type,
            query=query,
            request_body=request_body,
            request_params=request_params,
            ignore_errno=ignore_errno,
        )

    def PATCH(
        self,
        path,
        response_type,
        query=None,
        request_body=None,
        request_params=None,
        ignore_errno=None,
    ):
        """PATCH Call."""
        return self._request(
            "PATCH",
            path,
            response_type,
            query=query,
            request_body=request_body,
            request_params=request_params,
            ignore_errno=ignore_errno,
        )

    def DELETE(self, path, response_type, ignore_errno=None):
        """DELETE Call."""
        return self._request("DELETE", path, response_type, ignore_errno=ignore_errno)

    def _make_headers(self, method, request_headers):
        """Make request headers

        :param method: The request method
        :param request_headers: The custom request headers
        """
        headers = {
            "Secret-Key": self.secret_key,
            "User-Agent": f"DatatureSDK/{__version__} "
            f"(Python/{python_version}; {system}/{machine})",
        }

        if method in ["POST", "PUT", "PATCH", "GET"]:
            headers["Content-Type"] = "application/json"

        if request_headers is not None:
            for key, value in request_headers.items():
                headers[key] = value

        return headers

    def _make_query_string(self, query):
        """Make query string

        :param query: The query object
        """
        if query is None:
            return ""

        query_string = ""
        for key, value in query.items():
            if isinstance(value, bool):
                query_string += f"{key}={str(value).lower()}&"
            elif isinstance(value, list):
                for item in value:
                    query_string += f"{key}[]={item}&"
            else:
                if value is not None:
                    query_string += f"{key}={value}&"

        return query_string

    def _interpret_response(
        self, response: Response, ignore_errno: Optional[List[int]] = None
    ) -> Optional[bool]:
        """Check if need throw Error

        :param response: The request response
        :param ignore_errno: The error code(s) to ignore, if any
        """
        try:
            response_code = response.status_code
            response_data = response.json()
        except json.JSONDecodeError:
            response_data = response.text

        if not 200 <= response_code < 300:
            if isinstance(response_data, str):
                error_message = response_data
            else:
                error_message = response_data.get("message", str(response_data))

            if ignore_errno is not None and response_code in ignore_errno:
                logger.debug(
                    "API response errored: %s %s, but ignoring error",
                    response_code,
                    error_message,
                )
                return None

            logger.debug("API response errored: %s %s", response_code, error_message)

            if response_code == 400:
                raise error.BadRequestError(error_message, response_data)
            if response_code == 403:
                raise error.ForbiddenError(error_message, response_data)
            if response_code == 404:
                raise error.NotFoundError(
                    error_message,
                    response_data,
                )
            if response_code == 429:
                raise error.TooManyRequestsError(error_message, response_data)
            if response_code == 503:
                raise error.ServiceUnavailableError(error_message, response_data)
            if response_code == 504:
                raise error.GatewayTimeoutError(error_message, response_data)

            # For other 5xx errors, raise InternalServerError
            if 500 <= response_code < 600:
                raise error.InternalServerError(error_message, response_data)

            # For other client errors (4xx), raise BadRequestError
            raise error.BadRequestError(error_message, response_data)

        return True
