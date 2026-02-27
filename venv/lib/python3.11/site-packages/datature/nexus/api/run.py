#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   run.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Datature Run API
"""

from typing import Union

from datature.nexus import models
from datature.nexus.api.types import RunSetupMetadata
from datature.nexus.client_context import RestContext


class Run(RestContext):
    """Datature Run API Resource."""

    def list(self) -> models.Runs:
        """Lists all training runs regardless of status.

        :return: A list of msgspec structs containing
            the training run metadata with the following structure:

            .. code-block:: python

                [Run(
                    id='run_610ba26c-6fbb-42eb-b838-839c61b68b26',
                    project_id='proj_cd067221d5a6e4007ccbb4afb5966535',
                    flow_id='flow_63bbd3bf8a78eb906f417396',
                    execution=RunExecution(
                        accelerator=RunAccelerator(name='GPU_T4', count=1),
                        checkpoint=RunCheckpoint(
                            strategy='STRAT_ALWAYS_SAVE_LATEST',
                            evaluation_interval=250,
                            metric=None
                        ),
                        limit=RunLimit(metric='LIM_NONE', value=0)
                    ),
                    features=RunFeatures(preview=True, matrix=True, using_sliding_window=False),
                    status=RunStatus(
                        overview='Creating',
                        message='Creating service.',
                        update_data=1705466384796
                    ),
                    create_date=1705466384796,
                    update_date=1705466392067,
                    log_ids=['runlog_UjYxMGJhMjZjLTZmYmItNDJlYi1iODM4LTgzOWM2MWI2OGIyNg']
                )]

        :example:
            .. code-block:: python

                from datature.nexus import Client

                project = Client("5aa41e8ba........").get_project("proj_b705a........")

                project.runs.list()
        """
        return self.requester.GET(
            f"/projects/{self.project_id}/runs", response_type=models.Runs
        )

    def get(self, run_id: str) -> models.Run:
        """Retrieves a specific training run using the run ID.

        :param run_id: The ID of the training run.
        :return: A msgspec struct containing the specific
            training run metadata with the following structure:

            .. code-block:: python

                Run(
                    id='run_610ba26c-6fbb-42eb-b838-839c61b68b26',
                    project_id='proj_cd067221d5a6e4007ccbb4afb5966535',
                    flow_id='flow_63bbd3bf8a78eb906f417396',
                    execution=RunExecution(
                        accelerator=RunAccelerator(name='GPU_T4', count=1),
                        checkpoint=RunCheckpoint(
                            strategy='STRAT_ALWAYS_SAVE_LATEST',
                            evaluation_interval=250,
                            metric=None
                        ),
                        limit=RunLimit(metric='LIM_NONE', value=0)
                    ),
                    features=RunFeatures(preview=True, matrix=True, using_sliding_window=False),
                    status=RunStatus(
                        overview='Creating',
                        message='Creating service.',
                        update_data=1705466384796
                    ),
                    create_date=1705466384796,
                    update_date=1705466392067,
                    log_ids=['runlog_UjYxMGJhMjZjLTZmYmItNDJlYi1iODM4LTgzOWM2MWI2OGIyNg']
                )

        :example:
            .. code-block:: python

                    from datature.nexus import Client

                    project = Client("5aa41e8ba........").get_project("proj_b705a........")

                    project.runs.get("run_610ba26c-6fbb-42eb-b838-839c61b68b26")
        """
        assert isinstance(run_id, str)

        return self.requester.GET(
            f"/projects/{self.project_id}/runs/{run_id}", response_type=models.Run
        )

    def kill(self, run_id: str) -> models.Run:
        """Kills a specific training run using the run ID.

        :param run_id: The ID of the training run.
        :return: A msgspec struct containing the
            killed training metadata with the following structure:

            .. code-block:: python

                Run(
                    id='run_e2a14cee-eacc-4335-bc95-94c3ee196b04',
                    project_id='proj_cd067221d5a6e4007ccbb4afb5966535',
                    flow_id='flow_64e812a7e47592ef374cbbc2',
                    execution=RunExecution(
                        accelerator=RunAccelerator(name='GPU_L4', count=1),
                        checkpoint=RunCheckpoint(
                            strategy='STRAT_LOWEST_VALIDATION_LOSS',
                            evaluation_interval=220,
                            metric='Loss/total_loss'
                        ),
                        limit=RunLimit(metric='LIM_NONE', value=0)
                    ),
                    status=RunStatus(
                        overview='Cancelled',
                        message='Training cancelled.',
                        update_data=1700204316180
                    ),
                    create_date=1701927649302,
                    update_date=1701927649302,
                    features=RunFeatures(preview=True, matrix=True),
                    log_ids=['runlog_UmUyYTE0Y2VlLWVhY2MtNDMzNS1iYzk1LTk0YzNlZTE5NmIwNA']
                )

        :example:
            .. code-block:: python

                from datature.nexus import Client

                project = Client("5aa41e8ba........").get_project("proj_b705a........")

                project.runs.kill("run_63eb212ff0f856bf95085095")
        """
        assert isinstance(run_id, str)

        return self.requester.PATCH(
            f"/projects/{self.project_id}/runs/{run_id}",
            request_body={"status": "Cancelled"},
            response_type=models.Run,
        )

    def start(self, flow_id: str, setup: Union[RunSetupMetadata, dict]) -> models.Run:
        """Starts a new training run from a specific workflow using the flow ID.

        :param flow_id: The ID of the workflow.
        :param setup: The metadata of the training.
        :return: A msgspec struct containing the
            newly-initialized training run metadata with the following structure:

            .. code-block:: python

                Run(
                    id='run_e2a14cee-eacc-4335-bc95-94c3ee196b04',
                    project_id='proj_cd067221d5a6e4007ccbb4afb5966535',
                    flow_id='flow_64e812a7e47592ef374cbbc2',
                    execution=RunExecution(
                        accelerator=RunAccelerator(name='GPU_L4', count=1),
                        checkpoint=RunCheckpoint(
                            strategy='STRAT_LOWEST_VALIDATION_LOSS',
                            evaluation_interval=220,
                            metric='Loss/total_loss'
                        ),
                        limit=RunLimit(metric='LIM_NONE', value=0)
                    ),
                    status=RunStatus(
                        overview='Creating',
                        message='Training starting.',
                        update_data=1700204316180
                    ),
                    create_date=1701927649302,
                    update_date=1701927649302,
                    features=RunFeatures(
                        preview=True,
                        matrix=True,
                        advanced_evaluation=True
                    ),
                    log_ids=['runlog_UmUyYTE0Y2VlLWVhY2MtNDMzNS1iYzk1LTk0YzNlZTE5NmIwNA']
                )

        :example:
            .. code-block:: python

                from datature.nexus import Client

                project = Client("5aa41e8ba........").get_project("proj_b705a........")

                project.runs.start("flow_63d0f2d5fb1f9189db9b1c4b", {
                    "accelerator": {
                        "name": "GPU_T4",
                        "count": 1
                    },
                    "checkpoint": {
                        "strategy": "STRAT_ALWAYS_SAVE_LATEST",
                        "evaluation_interval": 250
                    },
                    "limit": {
                        "metric": "LIM_NONE",
                        "value": 0
                    },
                    "advanced_evaluation": True,
                })
        """
        assert isinstance(flow_id, str)
        assert isinstance(setup, (RunSetupMetadata, dict))

        if isinstance(setup, dict):
            setup = RunSetupMetadata(**setup)

        return self.requester.POST(
            f"/projects/{self.project_id}/runs",
            request_body={
                "flowId": flow_id,
                "execution": {
                    "accelerator": setup.accelerator.to_json(),
                    "checkpoint": setup.checkpoint.to_json(),
                    "limit": setup.limit.to_json(),
                    "debug": setup.debug,
                },
                "features": {
                    "advancedEvaluation": setup.advanced_evaluation,
                    "preview": setup.preview,
                    "matrix": setup.matrix,
                },
            },
            response_type=models.Run,
        )

    def get_logs(self, log_id: str) -> models.RunLogs:
        """
        Retrieves a specific training log using the log ID.

        :param log_id: The ID of the training log.
        :return: A msgspec struct with the specific
            training log metadata with the following structure:

            .. code-block:: python

                RunLogs(
                    id='runlog_UmUyYTE0Y2VlLWVhY2MtNDMzNS1iYzk1LTk0YzNlZTE5NmIwNA',
                    logs=[
                        {
                            'ev': 'trainingCheckpoint',
                            't': 1700200466147,
                            'pl': {
                                'step': 0,
                                'log': 'Step 0, totalLoss: 6.4055E+01, boxLoss: 5.3928E+00, classificationLoss: 5.2646E+01, distributedFocalLoss: 6.0163E+00.',
                                'totalLoss': 64.055,
                                'boxLoss': 5.3928,
                                'classificationLoss': 52.646,
                                'distributedFocalLoss': 6.0163
                            }
                        }
                    ]
                )

        :example:
            .. code-block:: python

                from datature.nexus import Client

                project = Client("5aa41e8ba........").get_project("proj_b705a........")

                project.runs.get_logs("runlog_63eb212ff0f856bf95085095")
        """
        assert isinstance(log_id, str)
        return self.requester.GET(
            f"/projects/{self.project_id}/runs/logs/{log_id}",
            response_type=models.RunLogs,
        )

    def get_confusion_matrix(self, run_id: str) -> models.RunConfusionMatrix:
        """Retrieves a training confusion matrix using the run ID.

        :param run_id: The ID of the training run.
        :return: A msgspec struct containing the specific
            training matrix json string with the following structure:

            .. code-block:: python

                RunConfusionMatrix(
                    "object" = "confusionMatrix",
                    "data" = "{\"0\":[{\"id\":\"RBC\",\"data\":[{\"x\":\"RBC\",\"y\":0},{\"x\":\"WBC\",\"y\":0},{\"x\":\"Platelets\",\"y\":0},{\"x\":\"boat\",\"y\":0},{\"x\":\"Background\",\"y\":0}]},{\"id\":\"WBC\",\"data\":[{\"x\":\"RBC\",\"y\":0},{\"x\":\"WBC\",\"y\":0},{\"x\":\"Platelets\",\"y\":0},{\"x\":\"boat\",\"y\":0},{\"x\":\"Background\",\"y\":0}]},{\"id\":\"Platelets\",\"data\":[{\"x\":\"RBC\",\"y\":0},{\"x\":\"WBC\",\"y\":0},{\"x\":\"Platelets\",\"y\":0},{\"x\":\"boat\",\"y\":0},{\"x\":\"Background\",\"y\":0}]},{\"id\":\"boat\",\"data\":[{\"x\":\"RBC\",\"y\":0},{\"x\":\"WBC\",\"y\":0},{\"x\":\"Platelets\",\"y\":0},{\"x\":\"boat\",\"y\":0},{\"x\":\"Background\",\"y\":0}]},{\"id\":\"Background\",\"data\":[{\"x\":\"RBC\",\"y\":302},{\"x\":\"WBC\",\"y\":27},{\"x\":\"Platelets\",\"y\":22},{\"x\":\"boat\",\"y\":2},{\"x\":\"Background\",\"y\":0}]}]}"
                )

        :example:
            .. code-block:: python

                from datature.nexus import Client

                project = Client("5aa41e8ba........").get_project("proj_b705a........")
                project.runs.get_confusion_matrix("run_63eb212ff0f856bf95085095")
        """
        assert isinstance(run_id, str)
        return self.requester.GET(
            f"/projects/{self.project_id}/runs/{run_id}/confusionMatrix",
            response_type=models.RunConfusionMatrix,
        )
