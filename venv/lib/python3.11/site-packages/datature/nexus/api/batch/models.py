#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   models.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   SDK response msgspec model
"""

from typing import Dict, List, Optional, Union

import msgspec

from datature.nexus.models import Deployment, NexusStruct


class WebhookTestResponse(NexusStruct):
    """
    Represents the response of a webhook test.

    Attributes:
        status (str): The status of the webhook test.
        response_code (int): The response code of the webhook test.
        latency_ms (int): The latency of the webhook test in milliseconds.
        attempt_count (int): The number of attempts made to test the webhook.
        body (Optional[str]): The body of the webhook test response.
        reason (Optional[str]): The reason for the error in the webhook test response, if any.
    """

    status: str
    response_code: int = msgspec.field(name="responseCode")
    latency_ms: int = msgspec.field(name="latencyMs")
    attempt_count: int = msgspec.field(name="attemptCount")
    body: Optional[str] = None
    reason: Optional[str] = None


class WebhookRetries(NexusStruct):
    """
    Represents the retry configuration for a webhook.

    Attributes:
        max_retries (int): The maximum number of retries.
        max_retry_delay (int): The maximum retry delay time in milliseconds.
    """

    max_retries: int = msgspec.field(name="maxRetries")
    max_retry_delay: int = msgspec.field(name="maxBackoffMs")


class WebhookModel(NexusStruct):
    """
    Represents a webhook within a project, detailing its configuration and status.

    Attributes:
        id (str): Unique identifier of the webhook.
        object (str): The object type of the webhook.
        project_id (str): Identifier of the project associated with the webhook.
        name (str): The name of the webhook.
        endpoint (str): The URL endpoint of the webhook.
        retries (WebhookRetries): The retry configuration for the webhook.
        create_date (int): Creation timestamp of the webhook (in milliseconds).
        update_date (int): Last updated timestamp of the webhook (in milliseconds).
    """

    id: str
    object: str
    project_id: str = msgspec.field(name="projectId")
    name: str
    endpoint: str
    retries: WebhookRetries
    create_date: int = msgspec.field(name="createDate")
    update_date: int = msgspec.field(name="updateDate")


class DatasetUploadUrl(NexusStruct):
    """
    Represents a signed URL for uploading a dataset.

    Attributes:
        method (str): HTTP method to be used with the URL (e.g., PUT).
        url (str): The signed URL for uploading the dataset.
        headers (Dict[str, str]): Headers required for accessing the URL.
        expires_at_time (int): Expiration date of the signed URL as an integer timestamp.
    """

    method: str
    url: str
    headers: Dict[str, str]
    expires_at_time: int = msgspec.field(name="expiresAtTime")


class DatasetSource(NexusStruct):
    """
    Represents the source of a dataset.

    Attributes:
        kind (str): The kind or type of the dataset source.
        upload_url (DatasetUploadUrl): The signed URL for uploading the dataset.
    """

    kind: str
    upload_url: DatasetUploadUrl = msgspec.field(name="uploadUrl")


class DatasetStatus(NexusStruct):
    """
    Represents the status of a dataset.

    Attributes:
        overview (str): An overview of the dataset status.
        message (str): A status message providing additional information.
        update_time (int):
            The timestamp of the last update to the dataset status (in milliseconds).
        source (DatasetSource): The source of the dataset.
        item_count (int): The total number of items in the dataset.
    """

    overview: str
    message: str
    update_time: int = msgspec.field(name="updateTime")
    source: DatasetSource
    item_count: int = msgspec.field(name="itemCount")


class Dataset(NexusStruct):
    """
    Represents a dataset within a project, including its configuration and status.

    Attributes:
        id (str): Unique identifier of the dataset.
        object (str): The object type of the dataset.
        name (str): The name of the dataset.
        project_id (str): Identifier of the project associated with the dataset.
        expiry_time (int): Expiration timestamp of the dataset (in milliseconds).
        status (DatasetStatus): The status of the dataset.
        create_date (int): Creation timestamp of the dataset (in milliseconds).
        update_date (int): Last updated timestamp of the dataset (in milliseconds).
    """

    id: str
    object: str
    name: str
    project_id: str = msgspec.field(name="projectId")
    expiry_time: int = msgspec.field(name="expiryTime")
    status: DatasetStatus
    create_date: int = msgspec.field(name="createDate")
    update_date: int = msgspec.field(name="updateDate")


class Webhook(NexusStruct, tag_field="kind"):
    """
    Represents the webhook destination for a job result.

    Attributes:
        webhook_id (Optional[str]): Identifier of the webhook associated with the destination.
    """

    webhook_id: Optional[str] = msgspec.field(name="webhookId", default=None)


ResultDestinations = Union[Webhook]


class ResultDelivery(NexusStruct):
    """
    Represents the result delivery configuration for a job.

    Attributes:
        destinations (List[ResultDestinations]): A list of result destinations.
    """

    destinations: List[ResultDestinations]


class NewEphemeralDeployment(NexusStruct, tag_field="kind"):
    """
    Represents a new ephemeral deployment configuration for a job.

    Attributes:
        template (Deployment): The deployment template for the job.
    """

    template: Deployment


class ExistingDeployment(NexusStruct, tag_field="kind"):
    """
    Represents an existing deployment configuration for a job.

    Attributes:
        deployment_id (str): Identifier of the deployment.
    """

    deployment_id: str = msgspec.field(name="deploymentId")


class JobSpec(NexusStruct):
    """
    Represents the specification of a job.

    Attributes:
        start_at_time (int): The start time of the job as an integer timestamp.
        stop_at_time (int): The stop time of the job as an integer timestamp.
        dataset_id (str): Identifier of the dataset associated with the job.
        result_delivery (ResultDelivery): The result delivery configuration for the job.
        deployment (Union[NewEphemeralDeployment, ExistingDeployment]):
            The deployment configuration for the job.
    """

    deployment: Union[NewEphemeralDeployment, ExistingDeployment]
    result_delivery: ResultDelivery = msgspec.field(name="resultDelivery")
    start_at_time: Optional[int] = msgspec.field(name="startAtTime", default=None)
    stop_at_time: Optional[int] = msgspec.field(name="stopAtTime", default=None)
    dataset_id: Optional[str] = msgspec.field(name="datasetId", default=None)


class JobItemStatuses(NexusStruct):
    """
    Represents the status of the items in a job.

    Attributes:
        gathered (Tuple[str, int]): The number of items successfully retrieved from the Dataset.
        failed_gather (Tuple[str, int]):
            The number of items that failed to be retrieved from the Dataset.
        preprocessed (Tuple[str, int]): The number of items successfully preprocessed.
        failed_process (Tuple[str, int]): The number of items that failed to be preprocessed.
        predicted (Tuple[str, int]): The number of items successfully predicted.
        failed_predict (Tuple[str, int]): The number of items that failed to be predicted.
        delivered (Tuple[str, int]):
            The number of items successfully delivered to the ResultDestination.
        failed_deliver (Tuple[str, int]):
            The number of items that failed to be delivered to the ResultDestination.
    """

    gathered: int = msgspec.field(name="Gathered", default=0)
    failed_gather: int = msgspec.field(name="FailedGather", default=0)
    preprocessed: int = msgspec.field(name="Preprocessed", default=0)
    failed_preprocess: int = msgspec.field(name="FailedProcess", default=0)
    predicted: int = msgspec.field(name="Predicted", default=0)
    failed_predict: int = msgspec.field(name="FailedPredict", default=0)
    delivered: int = msgspec.field(name="Delivered", default=0)
    failed_deliver: int = msgspec.field(name="FailedDeliver", default=0)

    _descriptions = {
        "gathered": "Items successfully retrieved from the Dataset.",
        "failed_gather": "Items failed to be retrieved from the Dataset.",
        "preprocessed": "Items successfully preprocessed.",
        "failed_preprocess": "Items failed to be preprocessed.",
        "predicted": "Items successfully predicted.",
        "failed_predict": "Items failed to be predicted.",
        "delivered": "Prediction results successfully delivered to the ResultDestination.",
        "failed_deliver": "Prediction results failed to be delivered to the ResultDestination.",
    }

    def get_description(self, key: str) -> str:
        """
        Get the description of the item status.

        :param key: The key of the item status.
        :return: The description of the item status.
        """
        return self._descriptions.get(key, "No description available.")


class JobStatus(NexusStruct):
    """
    Represents the status of a job.

    Attributes:
        overview (str): An overview of the job status.
        message (str): A status message providing additional information.
        update_date (int): The date of the last update to the job status.
        items (JobItemStatus): The status of the job items.
        reason (Optional[str]): The reason for the error in the job status, if any.
        cancelled_at (Optional[int]): The timestamp when the job was cancelled, if any.
    """

    overview: str
    message: str
    update_date: int = msgspec.field(name="updateDate")
    items: JobItemStatuses
    reason: Optional[str] = None
    cancelled_at: Optional[int] = msgspec.field(name="cancelledAt", default=None)


class Job(NexusStruct):
    """
    Represents a job within a project, including its configuration and status.

    Attributes:
        id (str): Unique identifier of the job.
        object (str): The object type of the job.
        name (str): The name of the job.
        project_id (str): Identifier of the project associated with the job.
        spec (JobSpec): The specification of the job.
        status (JobStatus): The status of the job.
        create_date (int): Creation date of the job.
        update_date (int): The date when the job was last updated.
    """

    id: str
    object: str
    name: str
    project_id: str = msgspec.field(name="projectId")
    spec: JobSpec
    status: JobStatus
    create_date: int = msgspec.field(name="createDate")
    update_date: int = msgspec.field(name="updateDate")


class JobLogEntry(NexusStruct):
    """
    Represents a log entry for a job.

    Attributes:
        kind (str): The kind or type of the log entry.
        create_time (int): The creation time of the log entry as an integer timestamp.
        id (str): Unique identifier of the log entry.
        level (str): The severity level of the log entry.
        item (str): The item or object associated with the log entry.
        status (str): The status of the log entry.
        time_ms (float): The time of the log entry in milliseconds.
        reason (str): The reason for the error in the log entry, if any.
    """

    kind: str
    create_time: int = msgspec.field(name="createTime")
    id: str
    level: str
    item: str
    status: str
    time_ms: float = msgspec.field(name="timeMs")
    reason: str = ""


class JobLogs(NexusStruct):
    """
    Represents the logs associated with a batch job.

    Attributes:

        id (str): Unique identifier of the batch job.
        object (str): The object type of the batch job.
        project_id (str): Identifier of the project associated with the batch job.
        entries (List[JobLogEntry]): A list of log entries for the batch job.
    """

    id: str
    object: str
    project_id: str = msgspec.field(name="projectId")
    entries: List[JobLogEntry]
