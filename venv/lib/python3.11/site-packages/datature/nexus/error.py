#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   error.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Error Class module
"""


class Error(Exception):
    """Error Class."""

    def __init__(
        self,
        message,
        detail=None,
    ):
        super()
        self.message = message
        self.detail = detail


class ErrorWithCode(Error):
    """HTTP Error Class."""

    def __repr__(self):
        return (
            f"{self.__class__.__name__}"
            f"(message={self.message}, "
            f"detail={self.detail})"
        )


class BadRequestError(ErrorWithCode):
    """BadRequestError http_code: 400"""


class UnauthorizedError(ErrorWithCode):
    """UnauthorizedError http_code: 401"""


class ForbiddenError(ErrorWithCode):
    """ForbiddenError http_code: 403"""


class NotFoundError(ErrorWithCode):
    """NotFoundError http_code: 404"""


class TooManyRequestsError(ErrorWithCode):
    """TooManyRequestsError http_code: 429"""


class InternalServerError(ErrorWithCode):
    """InternalServerError http_code: 500"""


class RetryableError(ErrorWithCode):
    """Base class for retryable errors."""


class NetworkConnectionError(RetryableError):
    """NetworkConnectionError - network connection issues."""


class RequestTimeoutError(RetryableError):
    """RequestTimeoutError - request timeout."""


class ServiceUnavailableError(RetryableError):
    """ServiceUnavailableError http_code: 503"""


class GatewayTimeoutError(RetryableError):
    """GatewayTimeoutError http_code: 504"""
