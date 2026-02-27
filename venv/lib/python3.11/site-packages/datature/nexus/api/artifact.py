#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   artifact.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Datature Artifact API
"""

import json
import time
import zipfile
from pathlib import Path
from typing import Union

import msgspec

from datature.nexus import config, error, models
from datature.nexus.api.types import (
    ArtifactExportOptions,
    ArtifactFilters,
    OperationStatusOverview,
)
from datature.nexus.client_context import RestContext
from datature.nexus.utils import utils


class Artifact(RestContext):
    """Datature Artifact API Resource."""

    def list(
        self,
        filters: Union[ArtifactFilters, dict] = None,
        include_exports: bool = False,
    ) -> models.Artifacts:
        """Lists all artifacts in the project.

        :param filters: The filters to apply to the artifacts.
        :param include_exports: The boolean indication on whether to return the exported models.
        :return: A list of msgspec structs containing
            the artifact metadata with the following structure:

            .. code-block:: python

                [Artifact(
                    id='artifact_65ae274540259e2a07533532',
                    project_id='proj_ecfb4589d153999ba9ce01f54568fa72',
                    run_id='run_4a5d406d-464d-470c-bd7d-e92456621ad3',
                    flow_title='Test workflow',
                    artifact_name='ckpt-20',
                    create_date=1705912133684,
                    is_training=False,
                    step=5000,
                    is_deployed=False,
                    metric=ArtifactMetric(
                        total_loss=0.32356,
                        classification_loss=0.012036,
                        localization_loss=0.010706,
                        regularization_loss=0.0
                    ),
                    model_name='fasterrcnn-inceptionv2-1024x1024',
                    export_options=[
                        ArtifactExportOptions(
                            format='ONNX',
                            optimizations=ArtifactExportOptimizations(
                                quantization=['float32', 'float16']
                            ),
                            default_optimizations=ArtifactExportOptimizations(
                                quantization='float32'
                            )
                        ),
                        ArtifactExportOptions(
                            format='TensorFlow',
                            optimizations=ArtifactExportOptimizations(
                                quantization=['float32']
                            ),
                            default_optimizations=ArtifactExportOptimizations(
                                quantization='float32'
                            )
                        ),
                    ],
                    exports=None
                )]

        :example:
            .. code-block:: python

                from datature.nexus import Client

                project = Client("5aa41e8ba........").get_project("proj_b705a........")
                artifacts = project.artifacts.list(include_exports=True)

                artifacts_with_filter = project.artifacts.list(
                    filters={
                        "run_ids": ['run_55608ecd-da05-40d8-8882-5033c46a612f']
                    },
                    include_exports=True
                )
        """
        assert isinstance(filters, (ArtifactFilters, dict, type(None)))

        if isinstance(filters, dict):
            filters = ArtifactFilters(**filters)
        if filters is None:
            filters = ArtifactFilters()

        return self.requester.GET(
            f"/projects/{self.project_id}/artifacts",
            query={"includeExports": include_exports, **filters.to_json()},
            response_type=models.Artifacts,
        )

    def get(self, artifact_id: str, include_exports: bool = False) -> models.Artifact:
        """Retrieves a specific artifact using the artifact ID.

        :param artifact_id: The ID of the artifact as a string.
        :param include_exports: The boolean indication on whether to return the exported models.
        :return: A msgspec struct containing the specific
            artifact metadata with the following structure:

            .. code-block:: python

                Artifact(
                    id='artifact_65ae274540259e2a07533532',
                    project_id='proj_ecfb4589d153999ba9ce01f54568fa72',
                    run_id='run_4a5d406d-464d-470c-bd7d-e92456621ad3',
                    flow_title='Test workflow',
                    artifact_name='ckpt-20',
                    create_date=1705912133684,
                    is_training=False,
                    step=5000,
                    is_deployed=False,
                    metric=ArtifactMetric(
                        total_loss=0.32356,
                        classification_loss=0.012036,
                        localization_loss=0.010706,
                        regularization_loss=0.0
                    ),
                    model_name='fasterrcnn-inceptionv2-1024x1024',
                    export_options=[
                        ArtifactExportOptions(
                            format='ONNX',
                            optimizations=ArtifactExportOptimizations(
                                quantization=['float32', 'float16']
                            ),
                            default_optimizations=ArtifactExportOptimizations(
                                quantization='float32'
                            )
                        ),
                        ArtifactExportOptions(
                            format='TensorFlow',
                            optimizations=ArtifactExportOptimizations(
                                quantization=['float32']
                            ),
                            default_optimizations=ArtifactExportOptimizations(
                                quantization='float32'
                            )
                        ),
                    ],
                    exports=None
                )

        :example:
            .. code-block:: python

                from datature.nexus import Client

                project = Client("5aa41e8ba........").get_project("proj_b705a........")
                project.artifacts.get("artifact_63bd140e67b42dc9f431ffe2", include_exports=True)
        """
        return self.requester.GET(
            f"/projects/{self.project_id}/artifacts/{artifact_id}",
            query={"includeExports": include_exports},
            response_type=models.Artifact,
        )

    def list_exported_models(self, artifact_id: str) -> models.ArtifactModels:
        """Lists all exported models of a specific artifact.

        :param artifact_id: The ID of the artifact as a string.
        :return: A list of msgspec structs with the
            exported model metadata with the following structure:

            .. code-block:: python

                [ArtifactModel(
                    id='model_5x6yy4q204538r3479q1351vw6w006r6',
                    artifact_id='artifact_65a7678a91afa7d22455c5ba',
                    status='Finished',
                    format='TensorFlow',
                    quantization="float32",
                    create_date=1705472326144,
                    download=DownloadSignedUrl(
                        method='GET',
                        expiry_date=1705558963838,
                        url='https://storage.googleapis.com/699baa54-f607-4c1b-9403-a015a0b4ff1c-ckpt-12-tensorflow.zip'
                    )
                )]

        :example:
            .. code-block:: python

                from datature.nexus import Client

                project = Client("5aa41e8ba........").get_project("proj_b705a........")
                project.artifacts.list_exported_models("artifact_63bd140e67b42dc9f431ffe2")
        """
        assert isinstance(artifact_id, str)

        return self.requester.GET(
            f"/projects/{self.project_id}/artifacts/{artifact_id}/exports",
            response_type=models.ArtifactModels,
        )

    def create_export(
        self,
        artifact_id: str,
        export_options: Union[ArtifactExportOptions, dict],
        background: bool = False,
    ) -> models.ArtifactModel:
        """Exports an artifact model in a specific model format.

        :param artifact_id: The ID of the artifact as a string.
        :param export_options: The export options of the model.

        :return: A msgspec struct containing the operation
            metadata of the model export with the following structure:

            .. code-block:: python

                ArtifactModel(
                    id='model_15x95x513v9yrvvx2x329vvr34308w96',
                    artifact_id='artifact_656eb13aa533dcb05a020124',
                    status='Queued',
                    format='TensorFlow',
                    quantization='float32',
                    create_date=1701927649302,
                    download=None
                )

        :example:
            .. code-block:: python

                from datature.nexus import Client

                project = Client("5aa41e8ba........").get_project("proj_b705a........")
                project.artifacts.create_export(
                    "artifact_63bd140e67b42dc9f431ffe2",
                    {
                        "format": "TensorFlow",
                    }
                )
        """
        assert isinstance(artifact_id, str)
        assert isinstance(export_options, (ArtifactExportOptions, dict))

        if isinstance(export_options, dict):
            export_options = ArtifactExportOptions(**export_options)

        new_export = self.requester.POST(
            f"/projects/{self.project_id}/artifacts/{artifact_id}/exports",
            request_body=export_options.to_json(),
            response_type=models.ArtifactModel,
        )

        if background:
            return new_export

        # Wait for the export to finish
        while True:
            exports = self.list_exported_models(artifact_id)
            for export in exports:
                if (
                    export.status == OperationStatusOverview.FINISHED.value
                    and export.id == new_export.id
                ):
                    return new_export
            time.sleep(config.OPERATION_LOOPING_DELAY_SECONDS)

    def download_exported_model(
        self, model_id: str, path: Union[str, Path, None] = None
    ) -> models.LocalArtifact:
        """Download and unzip an artifact model to local path.

        :param model_id: The ID of the artifact exported model.
        :param path: The download path for the model, default current path.

        :return: A msgspec struct containing the download path of the model:

            .. code-block:: python

                LocalArtifact(
                    download_path='local',
                    model_filename='datature-yolov8l.pt',
                    label_filename='label_map.pbtxt'
                )

        :example:
            .. code-block:: python

                from datature.nexus import Client

                project = Client("5aa41e8ba........").get_project("proj_b705a........")

                project.artifacts.download_exported_model(
                    "model_2q510q03x26882r4295x8y92yyqqqvq3"
                    path="./local"
                )
        """
        assert isinstance(model_id, str)
        assert isinstance(path, (str, Path, type(None)))

        artifacts = self.list(include_exports=True)

        download_path = utils.get_download_path(path)

        for artifact in artifacts:
            if not artifact.exports:
                continue

            for model in artifact.exports:
                if (
                    model.status == OperationStatusOverview.FINISHED.value
                    and model_id in (model.id, model.id.split("_")[1])
                ):
                    download_tmpfile = utils.download_files_to_tempfile(model.download)

                    # Unzip the file
                    model_files = []

                    with zipfile.ZipFile(download_tmpfile, "r") as zip_ref:
                        zip_ref.extractall(download_path)

                        for file_name in zip_ref.namelist():
                            # Check if the file ends with the desired extension
                            if any(
                                file_name.endswith(ext)
                                for ext in [".onnx", ".tflite", ".pt"]
                            ):
                                model_files.append(file_name)

                    return msgspec.json.decode(
                        json.dumps(
                            {
                                "download_path": str(download_path),
                                "model_filename": (
                                    "saved_model/"
                                    if model.format == "TensorFlow"
                                    else model_files[0]
                                ),
                                "label_filename": (
                                    "label.txt"
                                    if model.format == "TFLite"
                                    else "label_map.pbtxt"
                                ),
                            }
                        ),
                        type=models.LocalArtifact,
                    )

        # If didn't find the model key in the artifacts, raise an 404 error
        raise error.NotFoundError(
            f"Model with id {model_id} not found, please export model first."
        )

    def get_available_instances(
        self, artifact_id: str, region: str = "*"
    ) -> models.AvailableInstances:
        """Retrieves the available deployment instances for a specific artifact.

        :param artifact_id: The ID of the artifact as a string.
        :param region:
            The region to check the available instances, default all regions represented by "*".
        :return: A msgspec struct containing the available instances with the following structure:

            .. code-block:: python

                AvailableInstances(
                    id='instance_t4-standard-1g',
                    region='*',
                    instances=[
                        AvailableInstance(
                            id='instance_65a7678a91afa7d22455c5ba',
                            resources=DeploymentResources(
                                cpu=6,
                                memory=24576,
                                GPU_T4=1,
                                GPU_L4=None,
                                GPU_A100_40GB=None,
                                GPU_A100_80GB=None,
                                GPU_H100=None,
                            ),
                            regions=['asia-east1', 'us'],
                            accelerator=InstanceAccelerator(
                                kind='NvidiaGpu',
                                name='Nvidia T4',
                                count=1,
                                cuda_cores=2560,
                                vram_bytes=17179869184,
                            )
                        )
                    ]
                )

            :example:
                .. code-block:: python

                    from datature.nexus import Client

                    project = Client("5aa41e8ba........").get_project("proj_b705a........")
                    project.artifacts.get_available_instances(
                        artifact_id="artifact_63bd140e67b42dc9f431ffe2",
                        region="us"
                    )
        """
        assert isinstance(artifact_id, str)
        assert isinstance(region, str)

        return self.requester.GET(
            f"/projects/{self.project_id}/artifacts/{artifact_id}"
            f"/availableInstances/regions/{region}",
            response_type=models.AvailableInstances,
        )
