#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   types.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Types for Datature API resources.
"""
# pylint: disable=R0902,C0103,C0302,W0212

import json
import logging
from dataclasses import dataclass, field
from enum import Enum, unique
from typing import Dict, List, Optional, Union

logger = logging.getLogger("datature-nexus")


def add_mapping(enum_cls):
    """Add Mapping to Type."""

    enum_cls._member_map_.update(enum_cls.__MAPPING__)
    return enum_cls


@dataclass
class ProjectMetadata:
    """Project metadata.

    :param name: The name of the project.
    """

    name: str

    def to_json(self):
        """Function to convert dataclass to dict"""
        return {
            "name": self.name,
        }


@add_mapping
@unique
class BoundType(Enum):
    """Bound Type.

    Bound Type Options:
        Rectangle
        Polygon
        Classification
        Keypoints
        Bitmask3d
    """

    POLYGON = "Polygon"
    RECTANGLE = "Rectangle"
    CLASSIFICATION = "Classification"
    KEYPOINTS = "Keypoints"
    BITMASK3D = "Bitmask3d"

    __MAPPING__ = {
        "Polygon": POLYGON,
        "Rectangle": RECTANGLE,
        "Classification": CLASSIFICATION,
        "Keypoints": KEYPOINTS,
        "Bitmask3d": BITMASK3D,
    }


@add_mapping
@unique
class AnnotationExportFormat(Enum):
    """Annotation Export CSV Format.

    Bounding Box Options:
        coco
        csv_fourcorner
        csv_widthheight
        pascal_voc
        yolo_darknet
        yolo_keras_pytorch
        createml
        tfrecord

    Polygon Options:
        polygon_single
        polygon_coco

    Classification Options:
        csv_classification
        classification_tfrecord

    Key Point Options:
        keypoints_coco
    """

    COCO = "coco"
    CSV_FOURCORNER = "csv_fourcorner"
    CSV_WIDTHHEIGHT = "csv_widthheight"
    PASCAL_VOC = "pascal_voc"
    YOLO_DARKNET = "yolo_darknet"
    YOLO_KERAS_PYTORCH = "yolo_keras_pytorch"
    CREATEML = "createml"
    TFRECORD = "tfrecord"
    POLYGON_COCO = "polygon_coco"
    POLYGON_SINGLE = "polygon_single"
    CSV_CLASSIFICATION = "csv_classification"
    CLASSIFICATION_TFRECORD = "classification_tfrecord"
    KEYPOINTS_COCO = "keypoints_coco"
    COCO_RLE = "coco_rle"

    __MAPPING__ = {
        "coco": COCO,
        "csv_fourcorner": CSV_FOURCORNER,
        "csv_widthheight": CSV_WIDTHHEIGHT,
        "pascal_voc": PASCAL_VOC,
        "yolo_darknet": YOLO_DARKNET,
        "yolo_keras_pytorch": YOLO_KERAS_PYTORCH,
        "createml": CREATEML,
        "tfrecord": TFRECORD,
        "polygon_coco": POLYGON_COCO,
        "polygon_single": POLYGON_SINGLE,
        "csv_classification": CSV_CLASSIFICATION,
        "classification_tfrecord": CLASSIFICATION_TFRECORD,
        "keypoints_coco": KEYPOINTS_COCO,
        "coco_rle": COCO_RLE,
    }


@add_mapping
@unique
class AssetStatus(Enum):
    """Asset Status.

    Asset Status Options:
        Annotated
        Review
        Completed
        Tofix
        None
    """

    ANNOTATED = "Annotated"
    REVIEW = "Review"
    COMPLETED = "Completed"
    TOFIX = "Tofix"
    NONE = "None"

    __MAPPING__ = {
        "Annotated": ANNOTATED,
        "Review": REVIEW,
        "Completed": COMPLETED,
        "Tofix": TOFIX,
        "None": NONE,
    }


@add_mapping
@unique
class OperationStatusOverview(Enum):
    """Operation Status."""

    QUEUED = "Queued"
    RUNNING = "Running"
    FINISHED = "Finished"
    CANCELLED = "Cancelled"
    ERRORED = "Errored"

    __MAPPING__ = {
        "Queued": QUEUED,
        "Running": RUNNING,
        "Finished": FINISHED,
        "Cancelled": CANCELLED,
        "Errored": ERRORED,
    }


@add_mapping
@unique
class DeploymentStatusOverview(Enum):
    """Deployment Status."""

    CREATING = "Creating"
    UPDATING = "Updating"
    REMOVING = "Removing"
    AVAILABLE = "Available"
    ERRORED = "Errored"

    __MAPPING__ = {
        "Creating": CREATING,
        "Updating": UPDATING,
        "Removing": REMOVING,
        "Available": AVAILABLE,
        "Errored": ERRORED,
    }


@add_mapping
@unique
class RunStatusOverview(Enum):
    """Run Status."""

    CREATING = "Creating"
    RUNNING = "Running"
    FINISHED = "Finished"
    ERRORED = "Errored"
    CANCELLED = "Cancelled"

    __MAPPING__ = {
        "Creating": CREATING,
        "Running": RUNNING,
        "Finished": FINISHED,
        "Errored": ERRORED,
        "Cancelled": CANCELLED,
    }


@add_mapping
@unique
class ModelFormat(Enum):
    """Artifact supported Models Format."""

    TENSORFLOW = "TensorFlow"
    TFLITE = "TFLite"
    ONNX = "ONNX"
    PYTORCH = "PyTorch"
    COREML = "CoreML"

    __MAPPING__ = {
        "TensorFlow": TENSORFLOW,
        "TFLite": TFLITE,
        "ONNX": ONNX,
        "PyTorch": PYTORCH,
        "CoreML": COREML,
    }


@add_mapping
@unique
class SequenceBulkUpdateAbortMode(Enum):
    """Mode of aborting the bulk update operation.

    AbortOnAnyFailed:
        Bulk update operation will be aborted if any single sequence-related
        action fails.
    None:
        Bulk update operation will never be aborted even with failed actions.
    """

    NONE = "None"
    ABORT_ON_ANY_FAILED = "AbortOnAnyFailed"

    __MAPPING__ = {
        "None": NONE,
        "AbortOnAnyFailed": ABORT_ON_ANY_FAILED,
    }


@add_mapping
@unique
class SequenceMergeMode(Enum):
    """Sequence merge mode.

    ReplaceExistingEntry:
        When linking an asset to a sequence, overwrite any existing sequence entry
        which conflicts with the incoming entry.
    RejectSequenceOperation:
        When linking an asset to a sequence, cause the action to fail if it conflicts
        with an existing sequence entry.
    """

    REPLACE_EXISTING_ENTRY = "ReplaceExistingEntry"
    REJECT_SEQUENCE_OPERATION = "RejectSequenceOperation"

    __MAPPING__ = {
        "ReplaceExistingEntry": REPLACE_EXISTING_ENTRY,
        "RejectSequenceOperation": REJECT_SEQUENCE_OPERATION,
    }


DEFAULT_INSTANCES = [
    "instance_x1cpu-standard",
    "instance_t4-standard-1g",
    "instance_l4-standard-1g",
]


@dataclass
class AnnotationMetadata:
    """Annotation metadata.

    :param asset_id: The unique ID of the asset.
    :param tag: The tag class name of the annotation.
    :param bound_type: The bound type of the annotation (Rectangle or Polygon).
    :param bound: The bound coordinates of the annotation in
        [[x1, y1], [x2, y2], ... , [xn, yn]] format.
    """

    asset_id: str
    tag: str
    bound_type: BoundType
    bound: list
    frame: Optional[int] = None
    aggregation: Optional[dict] = None
    attributes: Optional[list] = None

    def __post_init__(self):
        if isinstance(self.bound_type, str):
            self.bound_type = BoundType(self.bound_type)

    def to_json(self):
        """Function to convert dataclass to dict"""
        annotation_metadata = {
            "assetId": self.asset_id,
            "tag": self.tag,
            "boundType": self.bound_type.value,
            "bound": self.bound,
            "frame": self.frame,
            "aggregation": self.aggregation,
            "attributes": self.attributes,
        }

        return {k: v for k, v in annotation_metadata.items() if v is not None}


@dataclass
class AnnotationExportOptions:
    """Annotation exported options.

    :param split_ratio: The ratio used to split the data into training and validation sets.
    :param seed: The number used to initialize a pseudorandom
        number generator to randomize the annotation shuffling.
    :param normalized: Boolean to indicate whether the bound
        coordinates of the exported annotations should be normalized. Defaults to True.
    """

    split_ratio: float
    seed: int
    normalized: bool = True

    def to_json(self):
        """Function to convert dataclass to dict"""
        return {
            "splitRatio": self.split_ratio,
            "seed": self.seed,
            "normalized": self.normalized,
        }


@dataclass
class AnnotationExportMetadata:
    """Annotation exported metadata.

    :param format: The annotation format for bounding boxes or polygons as a string.
    :param options: The exporting options.
    """

    format: Union[AnnotationExportFormat, str]
    options: Union[AnnotationExportOptions, dict]

    def __post_init__(self):
        assert isinstance(self.format, (AnnotationExportFormat, str))
        assert isinstance(self.options, (AnnotationExportOptions, dict))

        if isinstance(self.format, str):
            self.format = AnnotationExportFormat(self.format)
        if isinstance(self.options, dict):
            self.options = AnnotationExportOptions(**self.options)

    def to_json(self):
        """Function to convert dataclass to dict"""
        return {"format": self.format.value, "options": self.options.to_json()}


@dataclass
class Pagination:
    """Pagination Params.
    If the length of the function call results exceeds the limit,
    the results will be broken into multiple pages.

    :param page: An optional cursor to specify pagination if there are multiple pages of results.
    :param limit: A limit on the number of objects to be returned in a page. Defaults to 100.
    """

    page: str = None
    limit: int = 100

    def to_json(self):
        """Function to convert dataclass to dict"""
        pagination = {
            "page": self.page,
            "limit": self.limit,
        }

        # Remove None values
        return {k: v for k, v in pagination.items() if v is not None}


@dataclass
class AssetMetadata:
    """Asset Metadata.

    :param status: The annotation status of the asset (annotated, review, completed, tofix, none).
    :param custom_metadata: A dictionary containing any key-value pairs.
    """

    status: Union[AssetStatus, None] = None
    custom_metadata: Dict[str, Union[str, int, float, bool]] = field(
        default_factory=dict
    )

    def to_json(self):
        """Function to convert dataclass to dict"""
        asset_metadata = {
            "status": self.status,
            "customMetadata": self.custom_metadata,
        }

        # Remove None values
        return {k: v for k, v in asset_metadata.items() if v is not None}


@dataclass
class AssetFilePart:
    """Represents a single part of a multipart upload.

    :param part_number: The part number of the file part.
    :param start_byte: The starting byte of the file part.
    :param end_byte: The ending byte of the file part.
    """

    part_number: int
    start_byte: int
    end_byte: int

    def to_json(self):
        """Function to convert dataclass to dict"""
        file_part = {
            "partNumber": self.part_number,
            "startByte": self.start_byte,
            "endByte": self.end_byte,
        }

        # Remove None values
        return {k: v for k, v in file_part.items() if v is not None}


@dataclass
class AssetParent:
    """Image asset parent.

    :param kind: The kind of the parent.
    :param asset_id: The id of the asset.
    """

    kind: str = "customMetadata#assetParent"
    asset_id: Optional[str] = None

    def to_json(self):
        """Function to convert dataclass to dict"""
        parent = {
            "kind": self.kind,
            "assetId": self.asset_id,
        }
        return {k: v for k, v in parent.items() if v is not None}


@dataclass
class AssetFrameParent:
    """Frame asset parent.

    :param kind: The kind of the parent.
    :param asset_id: The id of the asset.
    :param frame: The frame of the asset.
    """

    kind: str = "customMetadata#assetFrameParent"
    asset_id: Optional[str] = None
    frame: Optional[int] = None

    def to_json(self):
        """Function to convert dataclass to dict"""
        parent = {
            "kind": self.kind,
            "assetId": self.asset_id,
            "frame": self.frame,
        }
        return {k: v for k, v in parent.items() if v is not None}


@dataclass
class AssetFilenameParent:
    """Asset filename parent.

    :param kind: The kind of the parent.
    :param filename: The filename of the asset.
    """

    kind: str = "customMetadata#assetFilenameParent"
    filename: Optional[str] = None

    def to_json(self):
        """Function to convert dataclass to dict"""
        parent = {
            "kind": self.kind,
            "filename": self.filename,
        }
        return {k: v for k, v in parent.items() if v is not None}


@dataclass
class AssetFilenameFrameParent:
    """Asset filename frame parent.

    :param kind: The kind of the parent.
    :param filename: The filename of the asset.
    :param frame: The frame of the asset.
    """

    kind: str = "customMetadata#assetFilenameFrameParent"
    filename: Optional[str] = None
    frame: Optional[int] = None

    def to_json(self):
        """Function to convert dataclass to dict"""
        parent = {
            "kind": self.kind,
            "filename": self.filename,
            "frame": self.frame,
        }
        return {k: v for k, v in parent.items() if v is not None}


CustomMetadataParent = Union[
    AssetFilenameFrameParent, AssetFilenameParent, AssetFrameParent, AssetParent
]


@dataclass
class AssetCustomMetadata:
    """Asset custom metadata.

    :param parent: The parent of the custom metadata.
    :param custom_metadata: The custom metadata.
    """

    parent: CustomMetadataParent
    custom_metadata: Dict[str, Union[str, int, float, bool]] = field(
        default_factory=dict
    )

    def to_json(self):
        """Function to convert dataclass to dict"""
        return {
            "parent": self.parent.to_json(),
            "customMetadata": self.custom_metadata,
        }


@dataclass
class AssetCustomMetadataBatch:
    """Custom metadata batch.

    :param custom_metadata_batch: A list of custom metadata batch items.
    """

    custom_metadata_batch: List[AssetCustomMetadata] = field(default_factory=list)

    def to_json(self):
        """Function to convert dataclass to dict"""
        return {
            "customMetadatas": [item.to_json() for item in self.custom_metadata_batch]
        }


@dataclass
class DeploymentOptions:
    """The configuration options for creating each Inference API instance.

    :param evaluation_strategy: The evaluation strategy to use
        of each Inference API, default entropy_score.
    :param evaluation_threshold: The evaluation threshold to
        use to trigger post-evaluation actions, default 0.5.
    :param evaluation_group: The asset group to which assets
        triggered by the active learning route will be uploaded, comma-separated list.
    """

    evaluation_strategy: str = None
    evaluation_threshold: float = None
    evaluation_group: List[str] = None

    def to_json(self):
        """Function to convert dataclass to dict"""
        options = {
            "evaluationStrategy": self.evaluation_strategy,
            "evaluationThreshold": self.evaluation_threshold,
            "evaluationGroup": self.evaluation_group,
        }
        # Remove None values
        return {k: v for k, v in options.items() if v is not None}


@dataclass
class DeploymentResource:
    """The resource allocation for the deployment instance, optional.
    [DEPRECATED] This field is deprecated and will be removed in future versions.

    :param cpu: The number of CPU cores to allocate, optional.
    :param ram: The amount of RAM to allocate in GB, optional.
    :param GPU_T4: The number of NVIDIA Tesla T4 GPUs to allocate, optional.
    :param GPU_L4: The number of NVIDIA Tesla L4 GPUs to allocate, optional.
    :param GPU_A100_40GB: The number of NVIDIA A100 (40GB) GPUs to allocate, optional.
    :param GPU_A100_80GB: The number of NVIDIA A100 (80GB) GPUs to allocate, optional.
    :param GPU_H100: The number of NVIDIA H100 GPUs to allocate, optional.
    """

    cpu: Optional[int] = None
    ram: Optional[int] = None
    GPU_T4: Optional[int] = None
    GPU_L4: Optional[int] = None
    GPU_A100_40GB: Optional[int] = None
    GPU_A100_80GB: Optional[int] = None
    GPU_H100: Optional[int] = None

    def __post_init__(self):
        logger.warning(
            "WARNING: The `resources` field is deprecated and will be removed in future versions. "
            "Use the `instance` field instead."
        )

    def to_json(self):
        """Function to convert dataclass to dict"""
        resource = {
            "cpu": self.cpu,
            "ram": self.ram,
            "GPU_T4": self.GPU_T4,
            "GPU_L4": self.GPU_L4,
            "GPU_A100_40GB": self.GPU_A100_40GB,
            "GPU_A100_80GB": self.GPU_A100_80GB,
            "GPU_H100": self.GPU_H100,
        }
        # Remove None values
        return {k: v for k, v in resource.items() if v is not None}


@dataclass
class DeploymentMetadata:
    """Deployment Settings Metadata.

    :param name: The name of the deployment instance.
    :param model_id: The ID of the exported artifact to be deployed.
        [DEPRECATED] This field is deprecated and will be removed in future versions.
        Use the `artifact_id` field instead.
    :param artifact_id: The ID of the artifact to be deployed.
    :param replicas: Number of deployment instances to spawn. Defaults to 1.
    :param region: The region where the deployment instance will be spawned.
    :param version_tag: The current version tag of the deployment instance.
    :param instance: The instance type for the deployment instance, optional.
    :param resources: The resource allocation for the deployment instance, optional.
        [DEPRECATED] This field is deprecated and will be removed in future versions.
    :param options: The configuration options for the deployment instance, optional.
    """

    name: Optional[str] = None
    model_id: Optional[str] = None
    artifact_id: Optional[str] = None
    replicas: int = 1
    region: Optional[str] = None
    version_tag: Optional[str] = None
    instance_id: Optional[str] = None
    resources: Optional[DeploymentResource] = None
    options: Optional[DeploymentOptions] = None

    def __post_init__(self):
        if isinstance(self.options, dict):
            self.options = DeploymentOptions(**self.options)
        if isinstance(self.resources, dict):
            logger.warning(
                "WARNING: The `resources` field is deprecated and will be removed in future versions. "
                "Use the `instance` field instead."
            )
            self.resources = DeploymentResource(**self.resources)

        if not self.instance_id and not self.resources:
            raise ValueError("Please provide either `instance_id` or `resources`.")

    def to_json(self):
        """Function to convert dataclass to dict"""
        if self.model_id is not None:
            logger.warning(
                "WARNING: The `model_id` field is deprecated and will be removed "
                "in future versions. Use the `artifact_id` field instead."
            )

        deployment_metadata = {
            "name": self.name,
            "modelId": self.model_id,
            "artifactId": self.artifact_id,
            "replicas": self.replicas,
            "region": self.region,
            "versionTag": self.version_tag,
            "instanceId": self.instance_id,
            "resources": (
                self.resources.to_json() if self.resources is not None else None
            ),
            "options": self.options.to_json() if self.options is not None else None,
        }
        return {
            k: v for k, v in deployment_metadata.items() if v is not None and v != {}
        }


@dataclass
class Accelerator:
    """The hardware accelerator to be used for the training.

    :param name: The name of the GPU to be used for the training
        (GPU_T4, GPU_P100, GPU_V100, GPU_L4, GPU_A100_40GB).
    :param count: The number of GPUs to be used for the training.
        More GPUs will use up more compute minutes. Defaults to 1.
    """

    name: str
    count: int = 1

    def to_json(self):
        """Function to convert dataclass to dict"""
        return {
            "name": self.name,
            "count": self.count,
        }


@dataclass
class Checkpoint:
    """The checkpoint metric to be used for the training.

    :param strategy: The checkpointing strategy to be used for the training.

        Checkpoint Strategies:
            STRAT_EVERY_N_EPOCH: Checkpoints are saved at intervals of n epochs.
            STRAT_ALWAYS_SAVE_LATEST: The final checkpoint is always saved.
            STRAT_LOWEST_VALIDATION_LOSS: The checkpoint with the lowest validation loss is saved.
            STRAT_HIGHEST_ACCURACY: The checkpoint with the highest accuracy is saved.

    :param metric: The checkpointing metric to be used for training.
        Note that metrics starting with "Loss" are only applicable when the
        strategy is set to "STRAT_LOWEST_VALIDATION_LOSS", and metrics starting with
        "DetectionBoxes" are only applicable when the strategy is set to "STRAT_HIGHEST_ACCURACY".

        Loss:
            Loss/total_loss
            Loss/regularization_loss
            Loss/classification_loss
            Loss/localization_loss

        Precision:
            DetectionBoxes_Precision/mAP
            DetectionBoxes_Precision/mAP@.50IOU
            DetectionBoxes_Precision/mAP@.75IOU
            DetectionBoxes_Precision/mAP (small)
            DetectionBoxes_Precision/mAP (medium)
            DetectionBoxes_Precision/mAP (large)

        Recall:
            DetectionBoxes_Recall/AR@1
            DetectionBoxes_Recall/AR@10
            DetectionBoxes_Recall/AR@100
            DetectionBoxes_Recall/AR@100 (small)
            DetectionBoxes_Recall/AR@100 (medium)
            DetectionBoxes_Recall/AR@100 (large)

    :param evaluation_interval: The step interval for checkpoint
        evaluation during training. Defaults to 250.
    """

    strategy: str
    metric: str = None
    evaluation_interval: int = 250

    def to_json(self):
        """Function to convert dataclass to dict"""

        checkpoint = {
            "strategy": self.strategy,
            "metric": self.metric,
            "evaluationInterval": self.evaluation_interval,
        }
        # Remove None values
        return {k: v for k, v in checkpoint.items() if v is not None}


@dataclass
class Limit:
    """The limit configuration for the training.

    :param metric: The limit metric for the training.

        Limit Metrics:
            LIM_MINUTE: Limits the training to a maximum number of minutes before it is killed.
            LIM_EPOCHS: Limits the training to a maximum number of epochs before it is killed.
            LIM_NONE: No limit will be set for the training.

    :param value: The limit value for the training. This value will not be
        used if the limit metric is "LIM_NONE". Defaults to 1.
    """

    metric: str
    value: int = 1

    def to_json(self):
        """Function to convert dataclass to dict"""
        return {
            "metric": self.metric,
            "value": self.value,
        }


@dataclass
class RunSetupMetadata:
    """The settings to start training.

    :param accelerator: The hardware accelerator to be used for the training.
    :param checkpoint: The checkpoint metric to be used for the training.
    :param limit: The limit configuration for the training.
    :param preview: [DEPRECATED] Boolean to indicate whether preview
        is enabled for the training. Use the `advancedEvaluation` field instead.
        Defaults to True.
    :param matrix: [DEPRECATED] Boolean to indicate whether confusion matrix
        is enabled for the training. Use the `advancedEvaluation` field instead.
        Defaults to True.
    :param advanced_evaluation: Boolean to indicate whether advanced evaluation
        features are enabled for the training.
    """

    accelerator: Accelerator = None
    checkpoint: Checkpoint = None
    limit: Limit = None
    preview: Optional[bool] = None
    matrix: Optional[bool] = None
    advanced_evaluation: Optional[bool] = None
    debug: bool = False

    def __post_init__(self):
        if isinstance(self.accelerator, dict):
            self.accelerator = Accelerator(**self.accelerator)
        if isinstance(self.checkpoint, dict):
            self.checkpoint = Checkpoint(**self.checkpoint)
        if isinstance(self.limit, dict):
            self.limit = Limit(**self.limit)

        if self.preview is None:
            self.preview = (
                self.advanced_evaluation
                if self.advanced_evaluation is not None
                else True
            )
        else:
            logger.warning(
                "WARNING: Preview and other advanced evaluation features will be merged into a "
                "single field `advanced_evaluation` in future versions. The `preview` field is "
                "deprecated and will be removed in future versions."
            )

        if self.matrix is not None:
            logger.warning(
                "WARNING: Confusion matrix will be enabled by default and is no longer billable. "
                "The `matrix` field is deprecated and will be removed in future versions."
            )


@dataclass
class FlowMetadata:
    """Workflow Metadata.

    :param title: The title of the workflow.
    """

    title: str

    def to_json(self):
        """Function to convert dataclass to dict"""
        return {
            "title": self.title,
        }


@dataclass
class AssetFilter:
    """Asset list filter."""

    groups: List[str] = None
    filename: str = None
    metadata_query: str = None
    status: Union[AssetStatus, str, None] = None
    asset_filter: str = None

    def __post_init__(self):
        assert isinstance(self.groups, (List, type(None)))

        if isinstance(self.status, str):
            self.status = AssetStatus(self.status)

        if self.asset_filter:
            try:
                self.asset_filter = json.dumps(json.loads(self.asset_filter))
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON format for asset filter. {exc}. "
                    "Please provide a valid JSON string."
                ) from exc

    def to_json(self):
        """Function to convert dataclass to dict"""
        asset_filters = {
            "group": self.groups,
            "filename": self.filename,
            "metadataQuery": self.metadata_query,
            "status": self.status.value if self.status is not None else None,
            "filter": self.asset_filter,
        }

        return {k: v for k, v in asset_filters.items() if v is not None}


@dataclass
class AnnotationFilter:
    """Annotation list filter."""

    asset_ids: List[str] = None

    def __post_init__(self):
        assert isinstance(self.asset_ids, (List, type(None)))

    def to_json(self):
        """Function to convert dataclass to dict"""
        annotation_filters = {
            "assetId": self.asset_ids,
        }

        return {k: v for k, v in annotation_filters.items() if v is not None}


@dataclass
class ObjectFilter:
    """Object list filter."""

    asset_filter: str = None
    annotation_filter: str = None

    def __post_init__(self):
        if self.asset_filter:
            try:
                self.asset_filter = json.dumps(json.loads(self.asset_filter))
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON format for asset filter. {exc}. "
                    "Please provide a valid JSON string."
                ) from exc

        if self.annotation_filter:
            try:
                self.annotation_filter = json.dumps(json.loads(self.annotation_filter))
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON format for annotation filter. {exc}. "
                    "Please provide a valid JSON string."
                ) from exc

    def to_json(self):
        """Function to convert dataclass to dict"""
        object_filter = {
            "assetFilter": self.asset_filter,
            "annotationFilter": self.annotation_filter,
        }

        return {k: v for k, v in object_filter.items() if v is not None}


@dataclass
class PredictionFilter:
    """Prediction list filter."""

    asset_filter: str = None
    prediction_filter: str = None

    def __post_init__(self):
        if self.asset_filter:
            try:
                self.asset_filter = json.dumps(json.loads(self.asset_filter))
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON format for asset filter. {exc}. "
                    "Please provide a valid JSON string."
                ) from exc

        if self.prediction_filter:
            try:
                self.prediction_filter = json.dumps(json.loads(self.prediction_filter))
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON format for prediction filter. {exc}. "
                    "Please provide a valid JSON string."
                ) from exc

    def to_json(self):
        """Function to convert dataclass to dict"""
        prediction_filter = {
            "assetFilter": self.asset_filter,
            "predictionFilter": self.prediction_filter,
        }

        return {k: v for k, v in prediction_filter.items() if v is not None}


@dataclass
class TagMetadata:
    """Tag Metadata."""

    name: str = None
    color: str = None
    description: str = None

    def to_json(self):
        """Function to convert dataclass to dict"""
        tag = {
            "name": self.name,
            "color": self.color,
            "description": self.description,
        }

        # Remove None values
        return {k: v for k, v in tag.items() if v is not None}


@dataclass
class ArtifactExportOptions:
    """Artifact Export Options."""

    format: Union[ModelFormat, str]
    quantization: str = None

    def __post_init__(self):
        assert isinstance(self.format, (ModelFormat, str))

        if isinstance(self.format, str):
            self.format = ModelFormat(self.format)

    def to_json(self):
        """Function to convert dataclass to dict"""
        options = {
            "format": self.format.value,
            "quantization": self.quantization,
        }

        # Remove None values
        return {k: v for k, v in options.items() if v is not None}


@dataclass
class ArtifactFilters:
    """Artifact list filter."""

    run_ids: List[str] = None

    def __post_init__(self):
        assert isinstance(self.run_ids, (List, type(None)))

    def to_json(self):
        """Function to convert dataclass to dict"""
        artifact_filters = {
            "runId": self.run_ids,
        }

        return {k: v for k, v in artifact_filters.items() if v is not None}


@dataclass
class SequenceFilter:
    """Sequence list filter."""

    name: Optional[str] = None

    def to_json(self):
        """Function to convert dataclass to dict"""
        sequence_filter = {
            "name": self.name,
        }
        return {k: v for k, v in sequence_filter.items() if v is not None}


@dataclass
class SequencePatch:
    """Sequence patch."""

    name: Optional[str] = None
    attributes: Optional[Dict[str, str]] = None

    def __post_init__(self):
        assert isinstance(self.attributes, (Dict, type(None)))

        if self.attributes:
            self.attributes = {k: str(v) for k, v in self.attributes.items()}

    def to_json(self):
        """Function to convert dataclass to dict"""
        return {
            "name": self.name,
            "attributes": self.attributes,
        }


@dataclass
class SequenceLinkMetadata:
    """Sequence link metadata."""

    name: str
    merge: SequenceMergeMode = SequenceMergeMode.REPLACE_EXISTING_ENTRY
    ord: Optional[int] = None
    role: Optional[str] = None

    def __post_init__(self):
        assert isinstance(self.name, str)
        assert isinstance(self.merge, SequenceMergeMode)
        assert isinstance(self.ord, (int, type(None)))
        assert isinstance(self.role, (str, type(None)))

    def to_json(self):
        """Function to convert dataclass to dict"""
        return {
            "name": self.name,
            "merge": self.merge.value,
            "ord": self.ord,
            "role": self.role,
        }


@dataclass
class SequenceBulkUpdateActionLink:
    """Sequence bulk update action link."""

    kind: str = "Link"
    sequence: Union[SequenceLinkMetadata, dict, str] = "Unset"
    asset_id: Optional[str] = None
    asset_filename: Optional[str] = None

    def __post_init__(self):
        assert isinstance(self.asset_id, (str, type(None)))
        assert isinstance(self.asset_filename, (str, type(None)))
        assert not (
            self.asset_id is not None and self.asset_filename is not None
        ), "Only one of `asset_id` or `asset_filename` should be provided."
        assert not (
            self.asset_id is None and self.asset_filename is None
        ), "Either `asset_id` or `asset_filename` must be provided."
        assert isinstance(self.sequence, (SequenceLinkMetadata, dict, str))

        if isinstance(self.sequence, dict):
            self.sequence = SequenceLinkMetadata(**self.sequence)

    def to_json(self):
        """Function to convert dataclass to dict"""
        link_meta = {
            "kind": self.kind,
            "assetId": self.asset_id,
            "assetFilename": self.asset_filename,
            "sequence": (
                self.sequence.to_json()
                if isinstance(self.sequence, SequenceLinkMetadata)
                else self.sequence
            ),
        }
        return {k: v for k, v in link_meta.items() if v is not None}


@dataclass
class SequenceBulkUpdateActionPatchSequence:
    """Sequence bulk update action patch sequence."""

    patch: Union[SequencePatch, dict]
    kind: str = "PatchSequence"
    sequence_id: Optional[str] = None
    sequence_name: Optional[str] = None

    def __post_init__(self):
        assert isinstance(self.patch, (SequencePatch, dict))
        assert isinstance(self.sequence_id, (str, type(None)))
        assert isinstance(self.sequence_name, (str, type(None)))
        assert not (
            self.sequence_id is not None and self.sequence_name is not None
        ), "Only one of `sequence_id` or `sequence_name` should be provided."
        assert not (
            self.sequence_id is None and self.sequence_name is None
        ), "Either `sequence_id` or `sequence_name` must be provided."

        if isinstance(self.patch, dict):
            self.patch = SequencePatch(**self.patch)

    def to_json(self):
        """Function to convert dataclass to dict"""
        patch_meta = {
            "kind": self.kind,
            "patch": self.patch.to_json(),
            "sequenceId": self.sequence_id,
            "sequenceName": self.sequence_name,
        }
        return {k: v for k, v in patch_meta.items() if v is not None}


@dataclass
class SequenceBulkUpdateActionRemoveSequence:
    """Sequence bulk update action remove sequence."""

    kind: str = "RemoveSequence"
    sequence_id: Optional[str] = None
    sequence_name: Optional[str] = None

    def __post_init__(self):
        assert isinstance(self.sequence_id, (str, type(None)))
        assert isinstance(self.sequence_name, (str, type(None)))

    def to_json(self):
        """Function to convert dataclass to dict"""
        remove_meta = {
            "kind": self.kind,
            "sequenceId": self.sequence_id,
            "sequenceName": self.sequence_name,
        }
        return {k: v for k, v in remove_meta.items() if v is not None}


SequenceBulkUpdateAction = Union[
    SequenceBulkUpdateActionLink,
    SequenceBulkUpdateActionPatchSequence,
    SequenceBulkUpdateActionRemoveSequence,
]


@add_mapping
@unique
class OntologyAttributeType(Enum):
    """Ontology attribute type."""

    CATEGORICAL = "Categorical"
    NUMERIC = "Numeric"
    STRING = "String"

    __MAPPING__ = {
        "Categorical": CATEGORICAL,
        "Numeric": NUMERIC,
        "String": STRING,
    }


@dataclass
class OntologyAttributeOptions:
    """Ontology attribute options."""

    categories: Optional[List[str]] = None

    def __post_init__(self):
        assert isinstance(self.categories, (list, type(None)))

    def to_json(self):
        """Function to convert dataclass to dict"""
        ontology_attribute_options = {
            "categories": self.categories,
        }
        return {k: v for k, v in ontology_attribute_options.items() if v is not None}


@dataclass
class OntologyAttribute:
    """Ontology attribute."""

    name: str
    type: OntologyAttributeType
    description: Optional[str] = None
    required: bool = False
    options: Optional[OntologyAttributeOptions] = None
    default: Optional[Union[str, int, float, List[str]]] = None

    def __post_init__(self):
        if isinstance(self.type, str):
            self.type = OntologyAttributeType(self.type)

        if isinstance(self.options, dict):
            self.options = OntologyAttributeOptions(**self.options)

        assert isinstance(self.type, OntologyAttributeType)
        assert isinstance(self.required, bool)
        assert isinstance(self.options, (OntologyAttributeOptions, type(None)))
        assert isinstance(self.default, (str, int, float, list, type(None)))

    def to_json(self):
        """Function to convert dataclass to dict"""
        attribute = {
            "name": self.name,
            "type": self.type.value,
            "description": self.description,
            "required": self.required,
            "options": self.options.to_json() if self.options else None,
            "default": self.default,
        }
        return {k: v for k, v in attribute.items() if v is not None}


@dataclass
class OntologyMetadata:
    """Ontology metadata."""

    attributes: List[OntologyAttribute]

    def __post_init__(self):
        if isinstance(self.attributes, list) and all(
            isinstance(attr, dict) for attr in self.attributes
        ):
            self.attributes = [OntologyAttribute(**attr) for attr in self.attributes]

        assert isinstance(self.attributes, list)
        assert all(isinstance(attr, OntologyAttribute) for attr in self.attributes)

    def to_json(self):
        """Function to convert dataclass to dict"""
        metadata = {
            "attributes": [attr.to_json() for attr in self.attributes],
        }
        return {k: v for k, v in metadata.items() if v is not None}
