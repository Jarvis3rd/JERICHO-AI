#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   client_context.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   SDK Client module
"""
# pylint: disable=R0903

from typing import Optional

from datature.nexus.requester import Requester


class ClientContext:
    """
    Client context for Datature SDK.
    """

    secret_key: str
    mtls_certificate_file_path: str
    mtls_private_key_file_path: str
    requester: Requester
    _project_id: str = None

    def __init__(
        self,
        secret_key: str,
        mtls_certificate_file_path: Optional[str] = None,
        mtls_private_key_file_path: Optional[str] = None,
        endpoint: str = "https://api.datature.io",
    ):
        self.secret_key = secret_key
        self.mtls_certificate_file_path = mtls_certificate_file_path
        self.mtls_private_key_file_path = mtls_private_key_file_path
        self.requester = Requester(
            secret_key, mtls_certificate_file_path, mtls_private_key_file_path, endpoint
        )

    @property
    def project_id(self):
        """The project id.

        :param value: The project id.
        :type: str
        """
        return self._project_id

    @project_id.setter
    def project_id(self, value):
        """The project id.

        :param value: The project id.
        :type: str
        """
        self._project_id = value


class RestContext:
    """Datature REST Context."""

    _context: ClientContext

    def __init__(self, context: ClientContext):
        """Create a REST Context.

        :param context: REST context used to make REST calls.
        """
        self.requester = context.requester
        self.project_id = context.project_id
        self._context = context
