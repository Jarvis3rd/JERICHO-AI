#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   batch.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Datature Batch API
"""

from collections import ChainMap
from inspect import isclass

from datature.nexus.api.batch.dataset import Dataset
from datature.nexus.api.batch.job import Job
from datature.nexus.api.batch.webhook import Webhook
from datature.nexus.client_context import ClientContext, RestContext


class Batch(RestContext):
    """Datature Batch API Resource."""

    datasets: Dataset
    jobs: Job
    webhooks: Webhook

    def __init__(self, client_context: ClientContext):
        """Initialize the Batch API Resource."""
        super().__init__(client_context)

        # Init sub resources
        self._auto_init_resources()

    def _get_all_annotations(self):
        """Get annotations for this class and all superclasses."""
        # This expression correctly handles cases where multiple superclasses
        # provide different annotations for the same attribute name.
        # See https://stackoverflow.com/a/72037059.
        return ChainMap(
            *(
                c.__annotations__
                for c in self.__class__.__mro__
                if "__annotations__" in c.__dict__
            )
        )

    def _auto_init_resources(self):
        for name, type_annot in self._get_all_annotations().items():
            # Don't overwrite existing fields
            if hasattr(self, name):
                continue

            # Only initialize if the type is a class and a subclass of RestContext
            if not isclass(type_annot) or not issubclass(type_annot, RestContext):
                continue

            setattr(self, name, type_annot(self._context))
