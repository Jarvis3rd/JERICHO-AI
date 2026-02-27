#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   types.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Types for Datature Job API resources.
"""
# pylint: disable=R0902,C0103,W0212,E1134

import logging
from dataclasses import dataclass, field
from enum import Enum, unique
from typing import List, Optional, Union

from colorama import Fore

from datature.nexus.api.types import DeploymentMetadata, add_mapping
from datature.nexus.utils import utils

logger = logging.getLogger("datature-nexus")


@dataclass
class WebhookRetries:
    """Webhook Retries.

    :param max_retries: Maximum number of retries. Default is 3.
    :param max_retry_delay: Maximum delay between retries in milliseconds. Default is 15000.
    """

    max_retries: int = 3
    max_retry_delay: int = 15000

    def __post_init__(self):
        assert isinstance(self.max_retries, int)
        assert isinstance(self.max_retry_delay, int)

        if self.max_retries > 3:
            print(
                f"{Fore.CYAN}●{Fore.RESET} Non-default value for `max_retries` "
                f"{Fore.GREEN}[default: 3]{Fore.RESET} may result in increased load "
                "on the server. Note that this may affect the performance of the batch job."
            )
        if self.max_retry_delay < 15000:
            print(
                f"{Fore.CYAN}●{Fore.RESET} Non-default value for `max_retry_delay` "
                f"{Fore.GREEN}[default: 15000ms]{Fore.RESET} may result in increased load "
                "on the server. Note that this may affect the performance of the batch job."
            )

    def to_json(self):
        """Function to convert dataclass to dict"""
        return {"maxRetries": self.max_retries, "maxBackoffMs": self.max_retry_delay}


@dataclass
class WebhookSecret:
    """Webhook Secret.

    :param contents: Webhook secret contents in base64 encoded format.
    """

    contents: str = utils.generate_webhook_secret()

    def __post_init__(self):
        assert isinstance(self.contents, str)

    def to_json(self):
        """Function to convert dataclass to dict"""
        return {"contents": self.contents}


@dataclass
class WebhookSpec:
    """Webhook Spec.

    :param endpoint: Webhook endpoint URL.
    :param secret: Webhook secret configuration.
    :param retries: Webhook retries configuration.
    """

    endpoint: Optional[str] = None
    secret: Optional[WebhookSecret] = field(default_factory=WebhookSecret)
    retries: WebhookRetries = field(default_factory=WebhookRetries)

    def __post_init__(self):
        assert isinstance(self.endpoint, (str, type(None)))
        if isinstance(self.secret, dict):
            self.secret = WebhookSecret(**self.secret)
        if isinstance(self.retries, dict):
            self.retries = WebhookRetries(**self.retries)

    def to_json(self):
        """Function to convert dataclass to dict"""
        webhook_specs = {
            "endpoint": self.endpoint,
            "secret": self.secret.to_json() if self.secret is not None else None,
            "retries": self.retries.to_json() if self.retries is not None else None,
        }
        return {k: v for k, v in webhook_specs.items() if v is not None and v != {}}


@dataclass
class WebhookMetadata:
    """Webhook Metadata.

    :param name: Webhook name.
    :param spec: Webhook configuration.
    """

    name: Optional[str] = None
    spec: WebhookSpec = field(default_factory=WebhookSpec)

    def __post_init__(self):
        assert isinstance(self.name, (str, type(None)))
        if isinstance(self.spec, dict):
            self.spec = WebhookSpec(**self.spec)

    def to_json(self):
        """Function to convert dataclass to dict"""
        webhook_metadata = {
            "name": self.name,
            "spec": (self.spec.to_json() if self.spec is not None else None),
        }
        return {k: v for k, v in webhook_metadata.items() if v is not None and v != {}}


@add_mapping
@unique
class DataSourceKind(str, Enum):
    """Data Source Kind."""

    UPLOADED_NEW_LINE_DELIM_JSON_FILE = "UploadedNewlineDelimitedJsonFile"

    __MAPPING__ = {
        "UploadedNewlineDelimitedJsonFile": UPLOADED_NEW_LINE_DELIM_JSON_FILE,
    }


@dataclass
class DatasetSourceSpec:
    """Dataset Source Spec.

    :param kind: Data source kind. Default is UPLOADED_NEW_LINE_DELIM_JSON_FILE.
    :param size_bytes: Size of the data source in bytes.
    :param crc32c: CRC32C checksum of the data source.
    """

    size_bytes: int
    crc32c: str
    kind: DataSourceKind = DataSourceKind.UPLOADED_NEW_LINE_DELIM_JSON_FILE

    def __post_init__(self):
        if isinstance(self.kind, str):
            self.kind = DataSourceKind(self.kind)
        assert isinstance(self.size_bytes, int)
        assert isinstance(self.crc32c, str)

    def to_json(self):
        """Function to convert dataclass to dict"""
        return {
            "kind": self.kind,
            "sizeBytes": self.size_bytes,
            "crc32c": self.crc32c,
        }


@dataclass
class DatasetSpec:
    """Dataset Spec.

    :param source: Dataset source configuration.
    """

    source: DatasetSourceSpec

    def __post_init__(self):
        if isinstance(self.source, dict):
            self.source = DatasetSourceSpec(**self.source)

    def to_json(self):
        """Function to convert dataclass to dict"""
        dataset_spec = {
            "source": self.source.to_json(),
        }
        return {k: v for k, v in dataset_spec.items() if v}


@dataclass
class DatasetMetadata:
    """Dataset Metadata.

    :param name: Dataset name.
    :param spec: Dataset configuration.
    """

    name: str
    spec: DatasetSpec = field(default_factory=DatasetSpec)

    def __post_init__(self):
        assert isinstance(self.name, str)
        if isinstance(self.spec, dict):
            self.spec = DatasetSpec(**self.spec)

    def to_json(self):
        """Function to convert dataclass to dict"""
        return {
            "name": self.name,
            "spec": self.spec.to_json(),
        }


@dataclass
class NewEphemeralDeployment:
    """New Deployment Reference.

    :param template: Deployment metadata.
    """

    template: DeploymentMetadata = field(default_factory=DeploymentMetadata)

    def __post_init__(self):
        if isinstance(self.template, dict):
            self.template = DeploymentMetadata(**self.template)

    def to_json(self):
        """Function to convert dataclass to dict"""
        new_deployment = {
            "kind": self.__class__.__name__,
            "template": self.template.to_json(),
        }
        return {k: v for k, v in new_deployment.items() if v is not None and v != {}}


@dataclass
class ExistingDeployment:
    """Existing Deployment Reference.

    :param deployment_id: Deployment ID.
    """

    deployment_id: str

    def __post_init__(self):
        assert isinstance(self.deployment_id, str)

    def to_json(self):
        """Function to convert dataclass to dict"""
        existing_deployment = {
            "kind": self.__class__.__name__,
            "deploymentId": self.deployment_id,
        }
        return {k: v for k, v in existing_deployment.items() if v is not None and v}


DeploymentRef = Union[NewEphemeralDeployment, ExistingDeployment]


@dataclass
class ResultDestination:
    """Result Destination.

    :param webhook: Webhook ID.
    :param kind: Destination kind. Default is Webhook.
    """

    webhook_id: str
    kind: str = "Webhook"

    def __post_init__(self):
        assert isinstance(self.kind, str)
        assert isinstance(self.webhook_id, str)

    def to_json(self):
        """Function to convert dataclass to dict"""
        result_destination = {
            "kind": self.kind,
            "webhookId": self.webhook_id,
        }
        return {k: v for k, v in result_destination.items() if v is not None and v}


@dataclass
class ResultDelivery:
    """Result Delivery.

    :param destinations: List of result destinations.
    """

    destinations: List[ResultDestination]

    def __post_init__(self):
        assert isinstance(self.destinations, list)
        self.destinations = [
            (
                ResultDestination(**destination)
                if isinstance(destination, dict)
                else destination
            )
            for destination in self.destinations
        ]

    def to_json(self):
        """Function to convert dataclass to dict"""
        return {
            "destinations": [
                destination.to_json() for destination in self.destinations
            ],
        }


@dataclass
class JobSpec:
    """Job Spec.

    :param dataset_id: Dataset ID.
    :param deployment: Deployment configuration.
    :param result_delivery: Result delivery configuration.
    :param start_at_time: Start time of the job in milliseconds.
    :param stop_at_time: Stop time of the job in milliseconds.
    """

    dataset_id: str = None
    deployment: DeploymentRef = None
    result_delivery: ResultDelivery = None
    start_at_time: Optional[int] = None
    stop_at_time: Optional[int] = None

    def __post_init__(self):
        assert isinstance(self.start_at_time, (int, type(None)))
        assert isinstance(self.stop_at_time, (int, type(None)))
        assert isinstance(self.dataset_id, str)
        if isinstance(self.deployment, dict):
            self.deployment = DeploymentRef(**self.deployment)
        if isinstance(self.result_delivery, dict):
            self.result_delivery = ResultDelivery(**self.result_delivery)

    def to_json(self):
        """Function to convert dataclass to dict"""
        batchjob_spec = {
            "startAtTime": self.start_at_time,
            "stopAtTime": self.stop_at_time,
            "datasetId": self.dataset_id,
            "deployment": self.deployment.to_json(),
            "resultDelivery": self.result_delivery.to_json(),
        }
        return {k: v for k, v in batchjob_spec.items() if v is not None and v}


@dataclass
class JobMetadata:
    """Job Metadata.

    :param name: Job name.
    :param spec: Job configuration.
    """

    name: str
    spec: JobSpec

    def __post_init__(self):
        assert isinstance(self.name, str)
        if isinstance(self.spec, dict):
            self.spec = JobSpec(**self.spec)

    def to_json(self):
        """Function to convert dataclass to dict"""
        batchjob_metadata = {"name": self.name, "spec": self.spec.to_json()}
        return {k: v for k, v in batchjob_metadata.items() if v is not None and v}


@dataclass
class JobOptions:
    """Job Options.

    :param dataset_id: Dataset ID.
    :param webhook_id: Webhook ID.
    :param artifact_id: Artifact ID.
    :param deployment_id: Deployment ID.
    :param deployment_metadata: Deployment configuration.
    :param start_at_time: Start time of the job in milliseconds.
    :param stop_at_time: Stop time of the job in milliseconds.
    """

    dataset_id: str
    webhook_id: str
    artifact_id: Optional[str] = None
    deployment_id: Optional[str] = None
    deployment_metadata: Optional[dict] = None
    start_at_time: Optional[int] = None
    stop_at_time: Optional[int] = None

    def parse_to_spec(self) -> JobSpec:
        """Parse JobOptions to JobSpec.

        :return: JobSpec
        """
        if self.deployment_id:
            deployment = ExistingDeployment(deployment_id=self.deployment_id)
        elif self.artifact_id:
            self.deployment_metadata.pop("artifact_id", None)

            deployment = NewEphemeralDeployment(
                DeploymentMetadata(
                    artifact_id=self.artifact_id, **self.deployment_metadata or {}
                )
            )
        else:
            raise ValueError(
                "Either `artifact_id` or `deployment_id` must be provided."
            )
        result_delivery = ResultDelivery(
            [ResultDestination(webhook_id=self.webhook_id)]
        )
        return JobSpec(
            dataset_id=self.dataset_id,
            deployment=deployment,
            result_delivery=result_delivery,
            start_at_time=self.start_at_time,
            stop_at_time=self.stop_at_time,
        )


@dataclass
class LogsFilter:
    """Logs Filter.

    :param before_time: Filter logs before the specified time in milliseconds.
    :param after_time: Filter logs after the specified time in milliseconds.
    :param min_level: Filter logs with minimum level, e.g. Info or Error.
    :param max_entries: Maximum number of log entries to return.
    """

    before_time: Optional[int] = None
    after_time: Optional[int] = None
    min_level: Optional[str] = None
    max_entries: Optional[int] = None

    def to_json(self):
        """Function to convert dataclass to dict"""
        logs_filter = {
            "beforeTime": self.before_time,
            "afterTime": self.after_time,
            "minLevel": self.min_level,
            "maxEntries": self.max_entries,
        }
        return {k: v for k, v in logs_filter.items() if v is not None}


@add_mapping
@unique
class JobStatusOverview(Enum):
    """Batch Job Status."""

    WAITING = "Waiting"
    REACHED = "Reached"
    FAILED = "Failed"

    __MAPPING__ = {
        "Waiting": WAITING,
        "Reached": REACHED,
        "Failed": FAILED,
    }


@add_mapping
@unique
class DatasetStatusOverview(Enum):
    """Dataset Status."""

    WAITING = "Waiting"
    PROCESSING = "Processing"
    PROCESSED = "Processed"
    FAILEDPROCESSING = "FailedProcessing"
    UPLOADING = "Uploading"
    UPLOADED = "Uploaded"
    FAILEDUPLOAD = "FailedUpload"

    __MAPPING__ = {
        "Waiting": WAITING,
        "Processing": PROCESSING,
        "Processed": PROCESSED,
        "FailedProcessing": FAILEDPROCESSING,
        "Uploading": UPLOADING,
        "Uploaded": UPLOADED,
        "FailedUpload": FAILEDUPLOAD,
    }
