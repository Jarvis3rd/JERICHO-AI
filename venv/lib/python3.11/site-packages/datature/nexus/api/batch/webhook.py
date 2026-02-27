#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   webhook.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Datature Webhook API
"""

from typing import Union

from datature.nexus import models
from datature.nexus.api.batch import models as batch_models
from datature.nexus.api.batch.types import WebhookMetadata, WebhookSpec
from datature.nexus.api.types import Pagination
from datature.nexus.client_context import RestContext


class Webhook(RestContext):
    """Datature Webhook API Resource."""

    def create(
        self, name: str, webhook_spec: Union[WebhookSpec, dict, None] = None
    ) -> batch_models.WebhookModel:
        """Create a new webhook.

        :param name: The name of the webhook.
        :param webhook_spec: The webhook specification.
        :return: A msgspec struct containing the webhook metadata with the following structure:

            .. code-block:: python

                WebhookModel(
                    id='webhook_f7d8aec2-7e2b-4d2c-a103-c8dd575c29c7',
                    object='webhook',
                    project_id='proj_ca5fe71e7592bbcf7705ea36e4f29ed4',
                    name='aws-lambda',
                    endpoint='https://lambda-url.ap-southeast-1.on.aws/',
                    retries=WebhookRetries(
                        max_retries=3,
                        max_retry_delay=15000
                    ),
                    create_date=1723633671620,
                    update_date=1723736909980
                )

        :example:
            .. code-block:: python

                from datature.nexus import Client
                from datature.nexus.utils import utils
                project = Client("5aa41e8ba........").get_project("proj_b705a........")

                webhook_secret = utils.generate_webhook_secret()

                project.batch.webhooks.create(
                    name="aws-lambda",
                    webhook_spec={
                        "endpoint": "https://lambda-url.ap-southeast-1.on.aws/",
                        "retries": {
                            "max_retries": 3,
                            "max_retry_delay": 15000
                        },
                        "secret": {
                            "contents": webhook_secret,
                        },
                    }
                )
        """
        assert isinstance(webhook_spec, (WebhookSpec, dict, type(None)))
        if isinstance(WebhookSpec, dict):
            webhook_spec = WebhookSpec(**webhook_spec)
        webhook_options = WebhookMetadata(name=name, spec=webhook_spec)

        return self.requester.POST(
            f"/projects/{self.project_id}/batch/webhooks",
            request_body=webhook_options.to_json(),
            response_type=batch_models.WebhookModel,
        )

    def delete(self, webhook_id: str) -> models.DeleteResponse:
        """Delete a webhook.

        :param webhook_id: The webhook ID.
        :return: A msgspec struct containing the delete response with the following structure:

            .. code-block:: python

                DeleteResponse(
                    id='webhook_f7d8aec2-7e2b-4d2c-a103-c8dd575c29c7',
                    deleted=True
                )

        :example:
            .. code-block:: python

                from datature.nexus import Client
                project = Client("5aa41e8ba........").get_project("proj_b705a........")

                project.batch.webhooks.delete("webhook_f7d8aec2-7e2b-4d2c-a103-c8dd575c29c7")
        """
        assert isinstance(webhook_id, str)
        return self.requester.DELETE(
            f"/projects/{self.project_id}/batch/webhooks/{webhook_id}",
            response_type=models.DeleteResponse,
        )

    def get(self, webhook_id: str) -> batch_models.WebhookModel:
        """Get a webhook.

        :param webhook_id: The webhook ID.
        :return: A msgspec struct containing the webhook metadata with the following structure:

            .. code-block:: python

                WebhookModel(
                    id='webhook_f7d8aec2-7e2b-4d2c-a103-c8dd575c29c7',
                    object='webhook',
                    project_id='proj_ca5fe71e7592bbcf7705ea36e4f29ed4',
                    name='localhost',
                    endpoint='https://lambda-url.ap-southeast-1.on.aws/',
                    retries=WebhookRetries(
                        max_retries=3,
                        max_retry_delay=15000
                    ),
                    create_date=1723633671620,
                    update_date=1723736909980
                )

        :example:
            .. code-block:: python

                from datature.nexus import Client
                project = Client("5aa41e8ba........").get_project("proj_b705a........")

                project.batch.webhooks.get("webhook_f7d8aec2-7e2b-4d2c-a103-c8dd575c29c7")
        """
        assert isinstance(webhook_id, str)
        return self.requester.GET(
            f"/projects/{self.project_id}/batch/webhooks/{webhook_id}",
            response_type=batch_models.WebhookModel,
        )

    def list(
        self,
        pagination: Union[Pagination, dict, None] = None,
    ) -> models.PaginationResponse[batch_models.WebhookModel]:
        """List all webhooks.

        :param pagination: The pagination options.
        :return: A msgspec struct containing the pagination response with the following structure:

            .. code-block:: python

                PaginationResponse(
                    next_page=None,
                    prev_page=None,
                    data=[
                        WebhookModel(
                            id='webhook_f7d8aec2-7e2b-4d2c-a103-c8dd575c29c7',
                            object='webhook',
                            project_id='proj_ca5fe71e7592bbcf7705ea36e4f29ed4',
                            name='localhost',
                            endpoint='https://lambda-url.ap-southeast-1.on.aws/',
                            retries=WebhookRetries(
                                max_retries=3,
                                max_retry_delay=15000
                            ),
                            create_date=1723633671620,
                            update_date=1723736909980
                        )
                    ]
                )

        :example:
            .. code-block:: python

                from datature.nexus import Client
                project = Client("5aa41e8ba........").get_project("proj_b705a........")

                project.batch.webhooks.list()
        """
        assert isinstance(pagination, (Pagination, dict, type(None)))

        if isinstance(pagination, dict):
            pagination = Pagination(**pagination)
        if pagination is None:
            pagination = Pagination()

        return self.requester.GET(
            f"/projects/{self.project_id}/batch/webhooks",
            query={**pagination.to_json()},
            response_type=models.PaginationResponse[batch_models.WebhookModel],
        )

    def update(
        self, webhook_id: str, webhook_spec: Union[WebhookSpec, dict, None]
    ) -> batch_models.WebhookModel:
        """Update a webhook.

        :param webhook_id: The webhook ID.
        :param webhook_spec: The webhook specification.
        :return: A msgspec struct containing the webhook metadata with the following structure:

            .. code-block:: python

                WebhookModel(
                    id='webhook_f7d8aec2-7e2b-4d2c-a103-c8dd575c29c7',
                    object='webhook',
                    project_id='proj_ca5fe71e7592bbcf7705ea36e4f29ed4',
                    name='localhost',
                    endpoint='https://lambda-url.ap-southeast-1.on.aws/',
                    retries=WebhookRetries(
                        max_retries=3,
                        max_retry_delay=15000
                    ),
                    create_date=1723633671620,
                    update_date=1723736909980
                )

        :example:
            .. code-block:: python

                from datature.nexus import Client
                project = Client("5aa41e8ba........").get_project("proj_b705a........")

                project.batch.webhooks.update(
                    webhook_id="webhook_f7d8aec2-7e2b-4d2c-a103-c8dd575c29c7",
                    webhook_spec={
                        "endpoint": "https://lambda-url.ap-southeast-1.on.aws/",
                        "retries": {
                            "max_retries": 3,
                            "max_retry_delay": 15000
                        }
                    }
                )
        """
        assert isinstance(webhook_spec, (WebhookSpec, dict, type(None)))
        if isinstance(webhook_spec, dict):
            webhook_spec = WebhookSpec(**webhook_spec)
            webhook_spec.secret = None
        webhook_options = WebhookMetadata(spec=webhook_spec)

        return self.requester.PATCH(
            f"/projects/{self.project_id}/batch/webhooks/{webhook_id}",
            request_body=webhook_options.to_json(),
            response_type=batch_models.WebhookModel,
        )

    def update_secret(self, webhook_id: str, secret: str) -> batch_models.WebhookModel:
        """Update a webhook secret.

        :param webhook_id: The webhook ID.
        :param secret: The webhook secret.
        :return: A msgspec struct containing the webhook metadata with the following structure:

            .. code-block:: python

                WebhookModel(
                    id='webhook_f7d8aec2-7e2b-4d2c-a103-c8dd575c29c7',
                    object='webhook',
                    project_id='proj_ca5fe71e7592bbcf7705ea36e4f29ed4',
                    name='localhost',
                    endpoint='https://lambda-url.ap-southeast-1.on.aws/',
                    retries=WebhookRetries(
                        max_retries=3,
                        max_retry_delay=15000
                    ),
                    create_date=1723633671620,
                    update_date=1723736909980
                )

        :example:
            .. code-block:: python

                from datature.nexus import Client
                from datature.nexus.utils import utils
                project = Client("5aa41e8ba........").get_project("proj_b705a........")

                webhook_secret = utils.generate_webhook_secret()

                project.batch.webhooks.update_secret(
                    webhook_id="webhook_f7d8aec2-7e2b-4d2c-a103-c8dd575c29c7",
                    secret=webhook_secret,
                )
        """
        assert isinstance(secret, str)
        return self.requester.PUT(
            f"/projects/{self.project_id}/batch/webhooks/{webhook_id}/secret",
            request_body={"contents": secret},
            response_type=batch_models.WebhookModel,
        )

    def test(self, webhook_id: str) -> batch_models.WebhookTestResponse:
        """Test a webhook by sending a sample payload.

        :param webhook_id: The webhook ID.
        :return: A msgspec struct containing the webhook test response with the following structure:

            .. code-block:: python

                WebhookTestResponse(
                    status='Ok',
                    response_code=204,
                    latency_ms=648,
                    attempt_count=1,
                    body=None,
                    reason=None
                )

        :example:
            .. code-block:: python

                from datature.nexus import Client
                project = Client("5aa41e8ba........").get_project("proj_b705a........")

                project.batch.webhooks.test("webhook_f7d8aec2-7e2b-4d2c-a103-c8dd575c29c7")
        """
        assert isinstance(webhook_id, str)
        return self.requester.POST(
            f"/projects/{self.project_id}/batch/webhooks/{webhook_id}:test",
            response_type=batch_models.WebhookTestResponse,
        )
