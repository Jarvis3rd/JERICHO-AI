#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   error_fixture.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Datature Error Response Test Data
"""

forbidden_error_response = {
    "code": "ForbiddenError",
    "message": "No Access Rights to Requested Resources",
}

not_found_error_response = {
    "code": "ResourceNotFoundError",
    "message": "Requested Project Resource Not Found",
}

too_many_requests_error_response = {
    "code": "TooManyRequestsError",
    "message": "Too Many Requests",
}

internal_server_error_response = {
    "code": "InternalServerError",
    "message": "Internal Server Error",
}
