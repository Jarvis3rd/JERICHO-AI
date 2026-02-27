#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   operation.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Datature Operation API
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Union

from datature.nexus import config, error, models
from datature.nexus.api.types import OperationStatusOverview
from datature.nexus.client_context import RestContext

logger = logging.getLogger("datature-nexus")


class Operation(RestContext):
    """Datature Operation API Resource."""

    def get(self, op_id: str) -> models.Operation:
        """Retrieves an executed operation status using the operation link.

        :param op_id: The id of the operation as a string.
        :return: A msgspec struct containing the operation metadata with the following structure.

                .. code-block:: python

                        Operation(
                            id='op_d52ab4e6-7760-4d12-9c43-7fc1b8ce1616',
                            kind='nexus.annotations.export',
                            status=OperationStatus(
                                overview='Finished',
                                message='Operation finished',
                                progress=OperationProgress(
                                    unit='whole operation',
                                    with_status=OperationProgressWithStatus(
                                        Queued=0,
                                        Running=0,
                                        Finished=1,
                                        Cancelled=0,
                                        Errored=0
                                    )
                                )
                            ),
                            create_date=1701927649302,
                            update_date=1701927649302
                        )

        :example:
                .. code-block:: python

                        from datature.nexus import Client

                        project = Client("5aa41e8ba........").get_project("proj_b705a........")

                        project.operations.get("op_508fc5d1-e908-486d-9e7b-1dca99b80024")
        """
        assert isinstance(op_id, str)
        return self.requester.GET(
            f"/projects/{self.project_id}/operations/{op_id}",
            response_type=models.Operation,
        )

    def wait_until_done(
        self,
        op_id: str,
        timeout: int = config.OPERATION_LOOPING_TIMEOUT_SECONDS,
        raise_exception_if: Union[
            OperationStatusOverview, str
        ] = OperationStatusOverview.ERRORED,
        abort_event: threading.Event = threading.Event(),
    ) -> models.Operation:
        """Continuously retrieves an executed operation status for a
        specified number of times at a specified delay interval.

        Can be used to poll a running operation to monitor execution status.

        :param op_id: The id of the operation as a string.
        :param timeout: The maximum number of times to loop the operation retrieval.
        :param raise_exception_if: The condition to raise error.
        :return: The operation status metadata if the operation has finished,
            a BadRequestError if the operation has errored out,
            or None if the operation is still running.

                .. code-block:: python

                    Operation(
                        id='op_d52ab4e6-7760-4d12-9c43-7fc1b8ce1616',
                        kind='nexus.annotations.export',
                        status=OperationStatus(
                            overview='Finished',
                            message='Operation finished',
                            progress=OperationProgress(
                                unit='whole operation',
                                with_status=OperationProgressWithStatus(
                                    Queued=0,
                                    Running=0,
                                    Finished=1,
                                    Cancelled=0,
                                    Errored=0
                                )
                            )
                        ),
                        create_date=1701927649302,
                        update_date=1701927649302
                    )

        :example:
                .. code-block:: python

                        from datature.nexus import Client

                        project = Client("5aa41e8ba........").get_project("proj_b705a........")

                        project.operations.wait_until_done(
                            "op_508fc5d1-e908-486d-9e7b-1dca99b80024"
                        )
        """
        assert isinstance(op_id, str)
        assert isinstance(raise_exception_if, (str, OperationStatusOverview))

        if isinstance(raise_exception_if, str):
            raise_exception_if = OperationStatusOverview(raise_exception_if)

        timeout = timeout or config.OPERATION_LOOPING_TIMEOUT_SECONDS
        response = None
        elapsed_time = datetime.now() + timedelta(seconds=timeout)

        while True:
            response = self.requester.GET(
                f"/projects/{self.project_id}/operations/{op_id}",
                response_type=models.Operation,
            )

            logger.debug("Operation status: %s ", response.status)

            if response.status.overview == OperationStatusOverview.FINISHED.value:
                return response

            if response.status.overview == raise_exception_if.value:
                logger.warning(
                    "Operation %s %s: please contact support at support@datature.io",
                    raise_exception_if.value,
                    op_id,
                )

                raise error.BadRequestError(
                    f"Operation {raise_exception_if.value} {op_id}: "
                    "please contact support at support@datature.io"
                )

            # if the operation has not finished when the timeouts
            if elapsed_time < datetime.now():
                logger.warning(
                    "Operation timeout: please use operation.get(%s) to get the status",
                    op_id,
                )
                return response

            if abort_event.is_set():
                return response

            time.sleep(config.OPERATION_LOOPING_DELAY_SECONDS)
