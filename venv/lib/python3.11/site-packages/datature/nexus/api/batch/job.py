#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   job.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Datature Job API
"""
# pylint: disable=E1102

import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Generator, Optional, Union

import numpy as np
import requests
from alive_progress import alive_bar

from datature.nexus import config, error, models
from datature.nexus.api.batch import models as batch_models
from datature.nexus.api.batch.types import (
    JobMetadata,
    JobOptions,
    JobStatusOverview,
    LogsFilter,
)
from datature.nexus.api.operation import Operation
from datature.nexus.api.types import DEFAULT_INSTANCES, Pagination
from datature.nexus.client_context import ClientContext, RestContext

logger = logging.getLogger("datature-nexus")


class Job(RestContext):
    """Datature Job API Resource."""

    def __init__(self, client_context: ClientContext):
        """Initialize the API Resource."""
        super().__init__(client_context)
        self.operation = Operation(client_context)

    def cancel(self, job_id: str) -> batch_models.Job:
        """Cancel a running or pending job.

        :param job_id: The job ID.
        :return: A msgspec struct containing the job metadata with the following structure:

            .. code-block:: python

                Job(
                    id='batchjob_4e5566d0-6538-441a-9fa5-f3495516646a',
                    object='batch_job',
                    name='cli-test',
                    project_id='proj_ca5fe71e7592bbcf7705ea36e4f29ed4',
                    spec=JobSpec(
                        start_at_time=1723734419985,
                        stop_at_time=1723993619985,
                        dataset_id='dataset_652ef566-af5c-4d52-b1e4-ec8ec6dc4b8e',
                        result_delivery=ResultDelivery(
                            destinations=[Webhook(
                                webhook_id='webhook_ed981529-0160-4704-8794-e7702a8de470'
                            )]
                        ),
                        deployment=ExistingDeployment(
                            deployment_id='deploy_3286bd71-9a8b-42bb-8ba6-c07549b81367'
                        ),
                    ),
                    status=JobStatus(
                        overview='Reached',
                        message='Finished',
                        update_date=1723734509417,
                        items=JobItemStatus(
                            gathered=50,
                            failed_gather=0,
                            preprocessed=50,
                            failed_process=0,
                            predicted=50,
                            failed_predict=0,
                            delivered=50,
                            failed_deliver=0
                        ),
                        reason=None
                    ),
                    create_date=1723734419985,
                    update_date=1723734509434
                )

        :example:
            .. code-block:: python

                from datature.nexus import Client
                project = Client("5aa41e8ba........").get_project("proj_b705a........")

                project.batch.jobs.cancel("batchjob_4e5566d0-6538-441a-9fa5-f3495516646a")
        """
        assert isinstance(job_id, str)
        return self.requester.PATCH(
            f"/projects/{self.project_id}/batch/jobs/{job_id}",
            request_body={"spec": {"stopAtTime": int(time.time() * 1000)}},
            response_type=batch_models.Job,
        )

    def create(self, name: str, job_options: dict) -> batch_models.Job:
        """Create a new batch job.

        :param name: The name of the job.
        :param job_options: The job options.
        :returns: A msgspec struct containing the job metadata with the following structure:

            .. code-block:: python

                Job(
                    id='batchjob_4e5566d0-6538-441a-9fa5-f3495516646a',
                    object='batch_job',
                    name='cli-test',
                    project_id='proj_ca5fe71e7592bbcf7705ea36e4f29ed4',
                    spec=JobSpec(
                        start_at_time=1723734419985,
                        stop_at_time=1723993619985,
                        dataset_id='dataset_652ef566-af5c-4d52-b1e4-ec8ec6dc4b8e',
                        result_delivery=ResultDelivery(
                            destinations=[Webhook(
                                webhook_id='webhook_ed981529-0160-4704-8794-e7702a8de470'
                            )]
                        ),
                        deployment=ExistingDeployment(
                            deployment_id='deploy_3286bd71-9a8b-42bb-8ba6-c07549b81367'
                        ),
                    ),
                    status=JobStatus(
                        overview='Reached',
                        message='Finished',
                        update_date=1723734509417,
                        items=JobItemStatus(
                            gathered=50,
                            failed_gather=0,
                            preprocessed=50,
                            failed_process=0,
                            predicted=50,
                            failed_predict=0,
                            delivered=50,
                            failed_deliver=0
                        ),
                        reason=None
                    ),
                    create_date=1723734419985,
                    update_date=1723734509434
                )

        :example:
            .. code-block:: python

                from datature.nexus import Client
                project = Client("5aa41e8ba........").get_project("proj_b705a........")

                project.batch.jobs.create(
                    "my-batch-job-08-15",
                    {
                        "dataset_id": "dataset_652ef566-af5c-4d52-b1e4-ec8ec6dc4b8e",
                        "webhook_id"="webhook_ed981529-0160-4704-8794-e7702a8de470",
                        "deployment_id": "deploy_3286bd71-9a8b-42bb-8ba6-c07549b81367",
                        "start_at_time": 1723734419985,
                        "stop_at_time": 1723993619985,
                    }
                )
        """
        assert isinstance(job_options, dict)

        if job_options.get("accumulate_results"):
            return self._create_job_with_accumulated_results(job_options)

        deployment_metadata = job_options.get("deployment_metadata")
        if deployment_metadata:
            if not deployment_metadata.get(
                "instance_id"
            ) and not deployment_metadata.get("resources"):
                logger.warning(
                    "WARNING: The `instance_id` field is not set. A random default instance will be selected. "
                    "To view the list of default instances, refer to our documentation: "
                    "https://developers.datature.io/docs/deployment-configuration#instance-types"
                )

                region = job_options.get("deployment_metadata").get("region") or "*"
                available_instances = self.requester.GET(
                    f"/projects/{self.project_id}/artifacts/{job_options.get('artifact_id')}"
                    f"/availableInstances/regions/{region}",
                    response_type=models.AvailableInstances,
                ).instances

                default_instances = [
                    instance.id
                    for instance in available_instances
                    if instance.id in DEFAULT_INSTANCES
                ]

                job_options["deployment_metadata"]["instance_id"] = np.random.choice(
                    default_instances
                )

        job_metadata = JobMetadata(
            name=name, spec=JobOptions(**job_options).parse_to_spec()
        )

        return self.requester.POST(
            f"/projects/{self.project_id}/batch/jobs",
            request_body=job_metadata.to_json(),
            response_type=batch_models.Job,
        )

    def _create_job_with_accumulated_results(
        self, job_options: dict
    ) -> batch_models.Job:
        """Create a new batch job with accumulated results.

        :param job_options: The job options.
        :returns: A dictionary containing the batch job ID.
        """
        batch_job_accumulator_url = os.getenv(
            "DATATURE_API_BATCH_JOB_ACCUMULATOR_URL",
            "https://monopod-prod-384071953537.asia-southeast1.run.app",
        )

        data = {
            "dt_project_key": self.project_id.split("_")[-1],
            "dt_secret_key": self._context.secret_key,
            "ndjson_url": job_options.get("ndjson_url"),
            "artifact_ids": job_options.get("artifact_ids"),
        }

        try:
            job_response = requests.request(
                "POST",
                f"{batch_job_accumulator_url}/create-batchjob",
                headers={"Content-Type": "application/json"},
                data=json.dumps(data),
                timeout=config.REQUEST_TIME_OUT_SECONDS,
            )
        except requests.exceptions.RequestException as exc:
            logger.error("Failed to create job with accumulated results: %s", exc)
            raise error.BadRequestError(
                "Failed to create job with accumulated results."
            )

        return job_response.json()

    def delete(self, job_id: str) -> models.DeleteResponse:
        """Delete a batch job.

        :param job_id: The job ID.
        :returns: A msgspec struct containing the delete response with the following structure:

            .. code-block:: python

                DeleteResponse(
                    id='batchjob_4e5566d0-6538-441a-9fa5-f3495516646a',
                    deleted=True
                )

        :example:
            .. code-block:: python

                from datature.nexus import Client
                project = Client("5aa41e8ba........").get_project("proj_b705a........")

                project.batch.jobs.delete("batchjob_4e5566d0-6538-441a-9fa5-f3495516646a")
        """
        assert isinstance(job_id, str)
        return self.requester.DELETE(
            f"/projects/{self.project_id}/batch/jobs/{job_id}",
            response_type=models.DeleteResponse,
        )

    def get(self, job_id: str) -> batch_models.Job:
        """Get a batch job.

        :param job_id: The job ID.
        :returns: A msgspec struct containing the job metadata with the following structure:

            .. code-block:: python

                Job(
                    id='batchjob_4e5566d0-6538-441a-9fa5-f3495516646a',
                    object='batch_job',
                    name='my-batch-job-08-15',
                    project_id='proj_ca5fe71e7592bbcf7705ea36e4f29ed4',
                    spec=JobSpec(
                        start_at_time=1723734419985,
                        stop_at_time=1723993619985,
                        dataset_id='dataset_652ef566-af5c-4d52-b1e4-ec8ec6dc4b8e',
                        result_delivery=ResultDelivery(
                            destinations=[Webhook(
                                webhook_id='webhook_ed981529-0160-4704-8794-e7702a8de470'
                            )]
                        ),
                        deployment=ExistingDeployment(
                            deployment_id='deploy_3286bd71-9a8b-42bb-8ba6-c07549b81367'
                        ),
                    ),
                    status=JobStatus(
                        overview='Reached',
                        message='Finished',
                        update_date=1723734509417,
                        items=JobItemStatus(
                            gathered=50,
                            failed_gather=0,
                            preprocessed=50,
                            failed_process=0,
                            predicted=50,
                            failed_predict=0,
                            delivered=50,
                            failed_deliver=0
                        ),
                        reason=None
                    ),
                    create_date=1723734419985,
                    update_date=1723734509434
                )

        :example:
            .. code-block:: python

                from datature.nexus import Client
                project = Client("5aa41e8ba........").get_project("proj_b705a........")

                project.batch.jobs.get("batchjob_4e5566d0-6538-441a-9fa5-f3495516646a")
        """
        assert isinstance(job_id, str)
        return self.requester.GET(
            f"/projects/{self.project_id}/batch/jobs/{job_id}",
            response_type=batch_models.Job,
        )

    def list(
        self,
        pagination: Union[Pagination, dict, None] = None,
    ) -> models.PaginationResponse[batch_models.Job]:
        """List all batch jobs.

        :param pagination: The pagination options.
        :returns: A msgspec struct containing the pagination response with the following structure:

            .. code-block:: python

                PaginationResponse(
                    next_page=None,
                    prev_page=None,
                    data=[
                        Job(
                            id='batchjob_4e5566d0-6538-441a-9fa5-f3495516646a',
                            object='batch_job',
                            name='my-batch-job-08-15',
                            project_id='proj_ca5fe71e7592bbcf7705ea36e4f29ed4',
                            spec=JobSpec(
                                start_at_time=1723734419985,
                                stop_at_time=1723993619985,
                                dataset_id='dataset_652ef566-af5c-4d52-b1e4-ec8ec6dc4b8e',
                                result_delivery=ResultDelivery(
                                    destinations=[Webhook(
                                        webhook_id='webhook_ed981529-0160-4704-8794-e7702a8de470'
                                    )]
                                ),
                                deployment=ExistingDeployment(
                                    deployment_id='deploy_3286bd71-9a8b-42bb-8ba6-c07549b81367'
                                ),
                            ),
                            status=JobStatus(
                                overview='Reached',
                                message='Finished',
                                update_date=1723734509417,
                                items=JobItemStatus(
                                    gathered=50,
                                    failed_gather=0,
                                    preprocessed=50,
                                    failed_process=0,
                                    predicted=50,
                                    failed_predict=0,
                                    delivered=50,
                                    failed_deliver=0
                                ),
                                reason=None
                            ),
                            create_date=1723734419985,
                            update_date=1723734509434
                        )
                    ],
                )

        :example:
            .. code-block:: python

                from datature.nexus import Client
                project = Client("5aa41e8ba........").get_project("proj_b705a........")

                project.batch.jobs.list()
        """
        assert isinstance(pagination, (Pagination, dict, type(None)))

        if isinstance(pagination, dict):
            pagination = Pagination(**pagination)
        if pagination is None:
            pagination = Pagination()

        return self.requester.GET(
            f"/projects/{self.project_id}/batch/jobs",
            query={**pagination.to_json()},
            response_type=models.PaginationResponse[batch_models.Job],
        )

    def get_logs(
        self, job_id: str, logs_filter: Union[LogsFilter, dict, None] = None
    ) -> batch_models.JobLogs:
        """Get the logs for a batch job. This query is limited to a maximum of 1000 entries.
        To get more logs, use the `get_all_log_entries` method.

        :param job_id: The job ID.
        :param logs_filter: The logs filter.
        :returns: A msgspec struct containing the job logs with the following structure:

            .. code-block:: python

                JobLogs(
                    id='batchjoblog_3d561cfa-9a53-4eb3-81c1-4193ae27f4fc',
                    object='batch_job_log',
                    project_id='proj_ca5fe71e7592bbcf7705ea36e4f29ed4',
                    entries=[
                        JobLogEntry(
                            kind='ItemPredicted',
                            create_time=1723080300011,
                            id='1e0ad7896a4aa2dd47eda727',
                            level='Info',
                            item='https://my-endpoint.url/blood_cell/36.jpg',
                            status='Delivered',
                            time_ms=9819.226,
                            reason=''
                        )
                    ]
                )

        :example:
            .. code-block:: python

                from datature.nexus import Client
                project = Client("5aa41e8ba........").get_project("proj_b705a........")

                project.batch.jobs.get_logs("batchjob_4e5566d0-6538-441a-9fa5-f3495516646a")
        """
        assert isinstance(logs_filter, (LogsFilter, dict, type(None)))

        if isinstance(logs_filter, dict):
            logs_filter = LogsFilter(**logs_filter)
        if logs_filter is None:
            logs_filter = LogsFilter()

        return self.requester.GET(
            f"/projects/{self.project_id}/batch/jobs/{job_id}/logs",
            query={**logs_filter.to_json()},
            response_type=batch_models.JobLogs,
        )

    def get_all_log_entries(
        self, job_id: str, logs_filter: Union[LogsFilter, dict, None] = None
    ) -> Generator[batch_models.JobLogEntry, None, None]:
        """Get all the logs for a batch job in batches of 1000 entries and return a generator.

        :param job_id: The job ID.
        :param logs_filter: The logs filter.
        :returns: A generator of msgspec struct containing the
                  job log entries with the following structure:

            .. code-block:: python

                JobLogEntry(
                    kind='ItemPredicted',
                    create_time=1723080300011,
                    id='1e0ad7896a4aa2dd47eda727',
                    level='Info',
                    item='https://my-endpoint.url/blood_cell/36.jpg',
                    status='Delivered',
                    time_ms=9819.226,
                    reason=''
                )

        :example:
            .. code-block:: python

                from datature.nexus import Client
                project = Client("5aa41e8ba........").get_project("proj_b705a........")

                count = 0
                for entry in project.batch.jobs.get_all_log_entries(
                    "batchjob_4e5566d0-6538-441a-9fa5-f3495516646a"
                ):
                    count += 1
                print(f"Total log entries: {count}")
        """
        with alive_bar(
            title="Fetching Logs",
            length=15,
            unit=" entries",
            force_tty=True,
            enrich_print=False,
        ) as progress_bar:
            seen_ids = set()
            while entries := self.get_logs(job_id, logs_filter).entries:
                if not entries:
                    break

                for entry in entries:
                    if entry.id not in seen_ids:
                        progress_bar()
                        yield entry
                seen_ids.update(entry.id for entry in entries)

                if len(entries) < 1000:
                    break

                if isinstance(logs_filter, dict):
                    logs_filter = LogsFilter(**logs_filter)
                elif logs_filter is None:
                    logs_filter = LogsFilter()
                logs_filter.before_time = entries[-1].create_time

    def wait_until_done(
        self,
        job_id: str,
        interval: int = config.OPERATION_LOOPING_DELAY_SECONDS,
        timeout: int = config.OPERATION_LOOPING_TIMEOUT_SECONDS,
        raise_exception_if: Union[JobStatusOverview, str] = JobStatusOverview.FAILED,
    ) -> batch_models.Job:
        """Wait until a batch job is done.

        :param job_id: The job ID.
        :param interval: The interval to check the job status.
        :param timeout: The timeout to wait for the job to be completed.
        :param raise_exception_if: The status to raise an exception if reached.
        :returns: A msgspec struct containing the job metadata with the following structure:

            .. code-block:: python

                Job(
                    id='batchjob_4e5566d0-6538-441a-9fa5-f3495516646a',
                    object='batch_job',
                    name='my-batch-job-08-15',
                    project_id='proj_ca5fe71e7592bbcf7705ea36e4f29ed4',
                    spec=JobSpec(
                        start_at_time=1723734419985,
                        stop_at_time=1723993619985,
                        dataset_id='dataset_652ef566-af5c-4d52-b1e4-ec8ec6dc4b8e',
                        result_delivery=ResultDelivery(
                            destinations=[Webhook(
                                webhook_id='webhook_ed981529-0160-4704-8794-e7702a8de470'
                            )]
                        ),
                        deployment=ExistingDeployment(
                            deployment_id='deploy_3286bd71-9a8b-42bb-8ba6-c07549b81367'
                        ),
                    ),
                    status=JobStatus(
                        overview='Reached',
                        message='Finished',
                        update_date=1723734509417,
                        items=JobItemStatus(
                            gathered=50,
                            failed_gather=0,
                            preprocessed=50,
                            failed_process=0,
                            predicted=50,
                            failed_predict=0,
                            delivered=50,
                            failed_deliver=0
                        ),
                        reason=None
                    ),
                    create_date=1723734419985,
                    update_date=1723734509434
                )

        :example:
            .. code-block:: python

                from datature.nexus import Client
                project = Client("5aa41e8ba........").get_project("proj_b705a........")

                project.batch.jobs.wait_until_done(
                    "batchjob_4e5566d0-6538-441a-9fa5-f3495516646a"
                )
        """
        assert isinstance(interval, int) and interval > 0
        assert isinstance(timeout, int) and timeout > 0
        assert isinstance(raise_exception_if, (JobStatusOverview, str))

        if isinstance(raise_exception_if, str):
            raise_exception_if = JobStatusOverview(raise_exception_if)

        elapsed_time = datetime.now() + timedelta(seconds=timeout)
        response = self.get(job_id)
        delivered_and_failed_count = (
            response.status.items.delivered + response.status.items.failed_deliver
        )

        dataset_id = response.spec.dataset_id
        dataset_count = self.requester.GET(
            f"/projects/{self.project_id}/batch/datasets/{dataset_id}",
            response_type=batch_models.Dataset,
        ).status.item_count

        with alive_bar(
            dataset_count,
            title="Processing Batch Job",
            length=20,
            force_tty=True,
            enrich_print=False,
        ) as progress_bar:
            cumulative_item_count = 0
            while delivered_and_failed_count != dataset_count:
                if (
                    response.status.overview == raise_exception_if.value
                    and delivered_and_failed_count != dataset_count
                ):
                    raise error.BadRequestError(
                        f"Error processing Job {job_id}, "
                        f"run `project.batch.jobs.get({job_id})` in Python or "
                        f"`datature batch jobs get {job_id}` in your terminal to get more detailed "
                        "status messages, or contact support at support@datature.io",
                    )

                if elapsed_time < datetime.now():
                    logger.warning(
                        "Operation timeout: please use `project.batch.jobs.get(%s)` in Python or "
                        "`datature batch jobs get %s` in your terminal to get the status instead.",
                        job_id,
                        job_id,
                    )
                    return response

                new_progress_count = delivered_and_failed_count - cumulative_item_count
                if new_progress_count > 0:
                    progress_bar(new_progress_count)
                    cumulative_item_count = delivered_and_failed_count
                time.sleep(interval)

                response = self.get(job_id)
                delivered_and_failed_count = (
                    response.status.items.delivered
                    + response.status.items.failed_deliver
                )
            if progress_bar.current != dataset_count:
                progress_bar(dataset_count - progress_bar.current)

        # Final sleep to allow a small buffer for the status to be updated
        time.sleep(interval)
        response = self.get(job_id)
        if response.status.items.delivered != dataset_count:
            logger.warning(
                "Job has completed but not all items have been successful. "
                "Run `project.batch.jobs.get_logs(%s)` in Python or "
                "`datature batch jobs logs %s` in your terminal to check the logs "
                "for more details, or contact support at support@datature.io",
                job_id,
                job_id,
            )
        return response

    def get_accumulated_results(self, job_id: str) -> Optional[Dict[str, str]]:
        """Get the accumulated results for a batch job.

        :param job_id: The job ID.
        :returns: The accumulated results.

        :example:
            .. code-block:: python

                from datature.nexus import Client
                project = Client("5aa41e8ba........").get_project("proj_b705a........")

                project.batch.jobs.get_accumulated_results("batchjob_4e5566d0-6538-441a-9fa5-f3495516646a")
        """
        batch_job_accumulator_url = os.getenv(
            "DATATURE_API_BATCH_JOB_ACCUMULATOR_URL",
            "https://monopod-prod-384071953537.asia-southeast1.run.app",
        )
        response = requests.request(
            "GET",
            f"{batch_job_accumulator_url}/retrieve-result",
            headers={"Content-Type": "application/json"},
            params={"batch_job_id": job_id},
            timeout=config.REQUEST_TIME_OUT_SECONDS,
        )
        return response.json()
