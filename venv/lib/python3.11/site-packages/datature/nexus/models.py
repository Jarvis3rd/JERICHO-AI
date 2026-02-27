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
# pylint: disable=R0903,C0302,C0103,W0212

from collections.abc import Iterable
from enum import Enum, unique
from typing import Any, Dict, Generic, List, Optional, Tuple, TypeVar, Union

import msgspec

T = TypeVar("T")


def add_mapping(enum_cls):
    """Add Mapping to Type."""

    enum_cls._member_map_.update(enum_cls.__MAPPING__)
    return enum_cls


class NexusStruct(msgspec.Struct):
    """
    A custom msgspec Struct class,
        which enhances attribute access to mimic dictionary-like behavior.
        This class allows getting attributes with a default value if the key is not found.
    """

    def get(self, key: str, default: Optional[T] = None) -> Optional[T]:
        """
        Retrieves the value of the specified attribute.

        Args:
            key (str): The attribute name to retrieve.
            default (Optional[T]): The default value to return if the attribute is not found.

        Returns:
            Optional[T]: The value of the attribute or the default value.
        """
        return getattr(self, key, default)

    def __getitem__(self, key: str) -> Optional[T]:
        """
        Overrides the __getitem__ method to allow dictionary-like access to attributes.

        Args:
            key (str): _description_
        """
        return self.get(key)

    def __repr__(self, indent: int = 2):
        """
        Overrides the __repr__ method to provide a pretty representation of the object.

        Args:
            indent (int): The number of spaces to indent the output, default is 2.

        Returns:
            str: The pretty string representation of the object.
        """

        def _pretty(obj: T, level: int = 1):
            """
            Recursively formats the object into a pretty string representation.

            Args:
                obj (T): The object to format.
                level (int): The current level of indentation.

            Returns:
                str: The pretty string representation of the object.
            """
            indent_str = " " * (level * indent)

            if isinstance(obj, msgspec.Struct):
                fields = []

                for field in obj.__struct_fields__:
                    value = getattr(obj, field)
                    field_repr = f"{indent_str}{field}={_pretty(value, level + 1)}"
                    fields.append(field_repr)

                if len(fields) > 0:
                    fields_str = ",\n".join(fields)
                    return f"{obj.__class__.__name__}(\n{fields_str}\n{indent_str[:-indent]})"

                return f"{obj.__class__.__name__}({', '.join(fields)})"

            if isinstance(obj, Iterable) and not isinstance(obj, (str, bytes)):
                if len(obj) > 1:
                    items = [f"{indent_str}{_pretty(item, level + 1)}" for item in obj]
                    items_str = ",\n".join(items)
                    return f"[\n{items_str}\n{indent_str[:-indent]}]"

                items = [_pretty(item, level + 1) for item in obj]
                return f"[{', '.join(items)}]"

            return repr(obj)

        return _pretty(self)


class Workspace(NexusStruct):
    """
    Represents a workspace in a msgspec struct format, containing essential workspace information.

    Attributes:
        id (str): Unique identifier of the workspace.
        name (str): Name of the workspace.
        owner (str): Owner of the workspace.
        tier (str): The str or level of the workspace.
        create_date (int): The creation date of the workspace as an integer timestamp.
    """

    id: str
    name: str
    owner: str
    tier: str
    create_date: int = msgspec.field(name="createDate")


class RunCheckpoint(NexusStruct):
    """
    Describes a checkpoint configuration in a training process.

    Attributes:
        strategy (str): Strategy for checkpoint creation (e.g., interval-based).
        evaluation_interval (int): Interval at which evaluations are performed.
        metric (Optional[str]): Metric used for evaluation.
    """

    strategy: str
    evaluation_interval: int = msgspec.field(name="evaluationInterval")
    metric: Optional[str] = None


class TagsCountItem(NexusStruct):
    """
    Describes a tag count item in a project, indicating the number of occurrences of a specific tag.

    Attributes:
        name (str): The name of the tag.
        count (int): The count of how many times the tag appears.
    """

    name: str
    count: int


class AssetAnnotationsStatistic(NexusStruct):
    """
    Represents statistical data related to a project.

    Attributes:
        tags_count (Optional[List[TagsCountItem]]): A list of tag count items.
        total_annotations (Optional[int]): Total number of annotations.
    """

    tags_count: Optional[List[TagsCountItem]] = msgspec.field(
        name="tagsCount", default=None
    )
    total_annotations: Optional[int] = msgspec.field(
        name="totalAnnotations", default=None
    )


class AnnotationStatistic(AssetAnnotationsStatistic):
    """
    Represents statistical data related to a project.

    Attributes:
        tags_count (Optional[List[TagsCountItem]]): A list of tag count items.
        total_assets (Optional[int]): Total number of assets.
        annotated_assets (Optional[int]): Number of annotated assets.
        total_annotations (Optional[int]): Total number of annotations.
    """

    total_assets: Optional[int] = msgspec.field(name="totalAssets", default=None)
    annotated_assets: Optional[int] = msgspec.field(
        name="annotatedAssets", default=None
    )


class Project(NexusStruct):
    """
    Represents a project within a workspace, detailing its structure and attributes.

    Attributes:
        id (str): Unique identifier of the project.
        name (str): Name of the project.
        workspace_id (str): Identifier of the workspace this project belongs to.
        type (str): The type of the project.
        create_date (int): Creation date of the project as an integer timestamp.
        localization (str): Localization or region information of the project.
        tags (List[str]): List of tags associated with the project.
        groups (List[str]): List of groups associated with the project.
        statistic (Optional[Statistic]): Statistical data related to the project.
    """

    id: str
    name: str
    workspace_id: str = msgspec.field(name="workspaceId")
    type: str
    create_date: int = msgspec.field(name="createDate")
    localization: str
    tags: List[str]
    groups: List[str]
    statistic: Optional[AnnotationStatistic] = None


Projects = List[Project]


class ProjectUser(NexusStruct):
    """
    Describes a user within a project, detailing their role and basic information.

    Attributes:
        id (str): Unique identifier of the user.
        access_type (str): The type of access the user has (e.g., admin, viewer).
        email (str): The email address of the user.
        nickname (str): The nickname or username of the user.
        picture (str): URL of the user's profile picture.
    """

    id: str
    access_type: str = msgspec.field(name="accessType")
    email: str
    nickname: str
    picture: str


ProjectUsers = List[ProjectUser]


class ArtifactMetric(NexusStruct):
    """
    Represents metrics for insights in a project, detailing various loss measures.

    Attributes:
        total_loss (Optional[float]): The total loss metric.
        classification_loss (Optional[float]): Loss metric specific to classification tasks.
        localization_loss (Optional[float]): Loss metric specific to localization tasks.
        regularization_loss (Optional[float]): The regularization loss metric.
    """

    total_loss: Optional[float] = msgspec.field(name="totalLoss", default=None)
    classification_loss: Optional[float] = msgspec.field(
        name="classificationLoss", default=None
    )
    localization_loss: Optional[float] = msgspec.field(
        name="localizationLoss", default=None
    )
    regularization_loss: Optional[float] = msgspec.field(
        name="regularizationLoss", default=None
    )


class DatasetSettings(NexusStruct):
    """
    Configuration settings for a dataset.

    Attributes:
        split_ratio (float): The ratio used to split the dataset.
        shuffle (bool): Whether to shuffle the dataset.
        seed (int): Seed for randomization, if shuffle is enabled.
        using_sliding_window (bool): Indicates whether a sliding window is used (default is False).
    """

    split_ratio: float = msgspec.field(name="splitRatio")
    shuffle: bool
    seed: int
    using_sliding_window: bool = msgspec.field(name="usingSlidingWindow", default=False)


class InsightDataset(NexusStruct):
    """
    Representation of a dataset with additional insights.

    Attributes:
        data_type (str): Type of data in the dataset.
        num_classes (int): Number of classes in the dataset.
        average_annotations (float): Average annotations per asset.
        total_assets (int): Total number of assets in the dataset.
        settings (DatasetSettings): Configuration settings for the dataset.
    """

    data_type: str = msgspec.field(name="dataType")
    num_classes: int = msgspec.field(name="numClasses", default=None)
    average_annotations: float = msgspec.field(name="averageAnnotations", default=None)
    total_assets: int = msgspec.field(name="totalAssets", default=None)
    settings: Union[DatasetSettings, None] = None


class InsightModel(NexusStruct):
    """
    Representation of a machine learning model with training parameters.

    Attributes:
        name (str): Name of the model.
        batch_size (int): Batch size used during training.
        training_steps (int): Number of training steps.
        max_detection_per_class (int): Maximum detections per class.
        solver (str): Solver used for training.
        learning_rate (float): Learning rate for the optimizer.
        momentum (float): Momentum for the optimizer.
    """

    name: str
    batch_size: int = msgspec.field(name="batchSize")
    training_steps: int = msgspec.field(name="trainingSteps")
    max_detection_per_class: int = msgspec.field(name="maxDetectionPerClass")
    solver: str
    learning_rate: float = msgspec.field(name="learningRate")
    momentum: float


class InsightArtifact(NexusStruct):
    """
    Represents an artifact within a project, detailing its properties and associated metrics.

    Attributes:
        id (str): Unique identifier of the artifact.
        is_training (bool): Indicates whether the artifact is related to training.
        step (int): Step number in the process.
        metric (ArtifactMetric): Metrics associated with the artifact.
    """

    id: str
    is_training: bool = msgspec.field(name="isTraining")
    metric: ArtifactMetric
    step: Optional[int] = None


class ProjectInsight(NexusStruct):
    """
    Describes insights of a project, including metrics, statistics, and configuration details.

    Attributes:
        flow_title (str): Title of the workflow.
        run_id (str): Identifier for the run.
        dataset (InsightDataset): Dataset associated with the insight.
        model (InsightModel): Model associated with the insight.
        checkpoint (RunCheckpoint): Checkpointing configuration used during training.
        artifact: InsightArtifact: Artifact associated with the insight.
        create_date (int): Creation date of the insight.
    """

    flow_title: str = msgspec.field(name="flowTitle")
    run_id: str = msgspec.field(name="runId")
    dataset: InsightDataset
    model: InsightModel
    checkpoint: RunCheckpoint
    artifact: InsightArtifact
    create_date: int = msgspec.field(name="createDate")


ProjectInsights = List[ProjectInsight]


class DownloadSignedUrl(NexusStruct):
    """
    Represents a signed URL for downloading, including its method and expiry information.

    Attributes:
        method (str): HTTP method to be used with the URL (e.g., GET).
        expiry_date (int): Expiration date of the download URL as an integer timestamp.
        url (str): The signed URL for download.
    """

    method: str
    expiry_date: int = msgspec.field(name="expiryDate")
    url: str


class AssetMetadata(NexusStruct):
    """
    Represents metadata for an asset, detailing its properties and characteristics.

    Attributes:
        file_size (int): The size of the file in bytes.
        mime_type (str): The MIME type of the file.
        height (int): The height of the image or asset in pixels.
        width (int): The width of the image or asset in pixels.
        groups (List[str]): List of groups associated with the asset.
        custom_metadata (Optional[Dict[str, Union[str, int, float, bool]]]):
            Additional custom metadata for the asset.
    """

    file_size: int = msgspec.field(name="fileSize")
    mime_type: str = msgspec.field(name="mimeType")
    height: int
    width: int
    groups: List[str]
    custom_metadata: Optional[Dict[str, Union[str, int, float, bool]]] = msgspec.field(
        name="customMetadata", default=None
    )


class Asset(NexusStruct):
    """
    Describes an asset within a project, including its metadata and associated data.

    Attributes:
        id (str): Unique identifier of the asset.
        filename (str): The name of the file.
        project (str): The project to which this asset belongs.
        status (str): The status of the asset.
        create_date (int): The creation date of the asset as an integer timestamp.
        url (str): URL where the asset is located.
        metadata (AssetMetadata): Metadata associated with the asset.
        statistic (Optional[AssetAnnotationsStatistic]): Statistical data related to the asset.
    """

    id: str
    project_id: str = msgspec.field(name="projectId")
    filename: str
    status: str
    create_date: int = msgspec.field(name="createDate")
    url: str
    metadata: AssetMetadata
    statistic: Optional[AssetAnnotationsStatistic] = None


class PaginationResponse(NexusStruct, Generic[T]):
    """
    Generic structure for paginated responses, providing navigation to other pages.

    Attributes:
        next_page (Optional[str]): URL to the next page of results.
        prev_page (Optional[str]): URL to the previous page of results.
        data (Union[List[T], T]): The data returned in the response.
    """

    next_page: Optional[str] = msgspec.field(name="nextPage", default=None)
    prev_page: Optional[str] = msgspec.field(name="prevPage", default=None)
    data: Union[T, List[T]] = None


class DeleteResponse(NexusStruct):
    """
    Structure representing the response to a delete request.

    Attributes:
        deleted (bool): Indicates whether the deletion was successful.
        id (Optional[str]): The ID of the deleted item, if applicable.
    """

    deleted: bool
    id: Optional[str] = None


class CancelResponse(NexusStruct):
    """
    Structure representing the response to a cancel request.
    """

    cancelled: bool
    id: Optional[str] = None


class AssetGroupStatistic(NexusStruct):
    """
    Represents statistics for a group of assets, providing various counts.

    Attributes:
        total_assets (Optional[int]): Total number of assets in the group.
        annotated_assets (Optional[int]): Number of annotated assets.
        reviewed_assets (Optional[int]): Number of reviewed assets.
        to_fixed_assets (Optional[int]): Number of assets marked to be fixed.
        completed_assets (Optional[int]): Number of completed assets.
    """

    total_assets: Optional[int] = msgspec.field(name="totalAssets", default=None)
    annotated_assets: Optional[int] = msgspec.field(
        name="annotatedAssets", default=None
    )
    reviewed_assets: Optional[int] = msgspec.field(name="reviewedAssets", default=None)
    to_fixed_assets: Optional[int] = msgspec.field(name="toFixedAssets", default=None)
    completed_assets: Optional[int] = msgspec.field(
        name="completedAssets", default=None
    )


class AssetGroup(NexusStruct):
    """
    Describes a group of assets within a project, along with their statistics.

    Attributes:
        group (str): The name of the group.
        statistic (Optional[AssetGroupStatistic]): Statistical data for the group.
    """

    group: str = msgspec.field(name="group", default=None)
    statistic: Optional[AssetGroupStatistic] = None


AssetGroups = List[AssetGroup]


class UploadSignedUrl(NexusStruct):
    """
    Represents a signed URL structure for secure access to resources.

    Attributes:
        method (str): HTTP method to be used with the URL (e.g., GET, POST).
        url (str): The signed URL.
        headers (Any): Headers required for accessing the URL.
        expiry_date (Optional[int]): Expiration date of the signed URL as an integer timestamp.
    """

    method: str
    url: str
    headers: Dict
    expiry_date: Optional[int] = msgspec.field(name="expiryDate", default=None)


class UploadSessionAssetMetadata(NexusStruct):
    """
    Describes the metadata for an asset to be uploaded in a session.

    Attributes:
        filename (str): Name of the file.
        mime (str): MIME type of the file.
        size (int): Size of the file in bytes.
        crc32c (int): CRC32C checksum of the file for data integrity.
    """

    filename: str
    mime: str
    size: int
    crc32c: int


class UploadSessionAssetItem(NexusStruct):
    """
    Represents an individual asset item within an upload session.

    Attributes:
        metadata (UploadSessionAssetMetadata): Metadata of the asset to be uploaded.
        upload (UploadSignedUrl): Signed URL for uploading the asset.
    """

    metadata: UploadSessionAssetMetadata
    upload: UploadSignedUrl


class UploadSession(NexusStruct):
    """
    Represents an upload session, including its identifier and the assets to be uploaded.

    Attributes:
        id (str): Unique identifier of the upload session.
        op_id (str): Operation identifier for the session.
        assets (List[UploadSessionAssetItem]): List of assets included in the session.
    """

    id: str
    op_id: str = msgspec.field(name="opId")
    assets: List[UploadSessionAssetItem]


class MultipartUploadSignedUrl(NexusStruct):
    """
    Represents a signed URL for a multipart upload.
    Attributes:
        method (str): HTTP method to be used with the URL (e.g., GET, POST).
        url (str): The signed URL.
        expiry (int): Expiration date of the signed URL as an integer timestamp.
        response_headers (List[str]): List of headers expected in the response.
        response_body (bool): Indicates whether the response body is expected.
        headers (Optional[Dict[str, str]]): Additional headers to be included in the request.
    """

    method: str
    url: str
    expiry: int
    response_headers: List[str] = msgspec.field(name="responseHeaders")
    response_body: bool = msgspec.field(name="responseBody")
    headers: Optional[Dict[str, str]] = None


class MultipartUploadSession(NexusStruct):
    """
    Represents a multipart upload session, including its identifier and part count.
    Attributes:
        id (str): Unique identifier of the multipart upload session.
        part_count (int): Number of parts in the multipart upload.
    """

    id: str
    part_count: int = msgspec.field(name="partCount")


class MultipartPartStatus(NexusStruct):
    """
    Represents the status of a part in a multipart upload session.

    Attributes:
        part_number (int): The part number in the multipart upload.
        status (str): The status of the part (e.g., "uploaded", "pending").
        size (int): Size of the part in bytes.
    """

    id: str
    part_number: int = msgspec.field(name="partNumber")
    completed: bool


class MultipartCompleteResponse(NexusStruct):
    """
    Represents the response to a complete request for a multipart upload session.

    Attributes:
        id (str): Unique identifier of the multipart upload session.
        completed (bool): Indicates whether the multipart upload session was successfully completed.
    """

    id: str
    completed: bool


class MultipartAbortResponse(NexusStruct):
    """
    Represents the response to an abort request for a multipart upload session.

    Attributes:
        id (str): Unique identifier of the multipart upload session.
        aborted (bool): Indicates whether the multipart upload session was successfully aborted.
    """

    id: str
    aborted: bool


class AssetParent(NexusStruct):
    """
    Represents the parent of an asset.

    Attributes:
        asset_id (Optional[str]): The asset ID.
        filename (Optional[str]): The filename.
        project (Optional[str]): The project ID.
        frame (Optional[int]): The frame number.
    """

    asset_id: Optional[str] = msgspec.field(name="assetId", default=None)
    filename: Optional[str] = None
    project: Optional[str] = None
    frame: Optional[int] = None


class AssetCustomMetadata(NexusStruct):
    """
    Represents custom metadata for an asset.

    Attributes:
        parent (AssetParent): The parent of the custom metadata.
        custom_metadata (Dict[str, Union[str, int, float, bool]]): The custom metadata.
        id (Optional[str]): The ID of the custom metadata.
        object (Optional[str]): The object of the custom metadata.
    """

    parent: AssetParent
    custom_metadata: Dict[str, Union[str, int, float, bool]] = msgspec.field(
        name="customMetadata"
    )
    id: Optional[str] = msgspec.field(name="id", default=None)
    object: Optional[str] = msgspec.field(name="object", default=None)


class AssetCustomMetadatas(NexusStruct):
    """
    Represents a list of custom metadata for an asset.

    Attributes:
        custom_metadatas (List[AssetCustomMetadata]): The custom metadata.
    """

    custom_metadatas: List[AssetCustomMetadata] = msgspec.field(name="customMetadatas")


class AssetCustomMetadataError(NexusStruct):
    """
    Represents an error for a custom metadata.

    Attributes:
        custom_metadata (AssetCustomMetadata): The custom metadata.
        error (str): The error message.
    """

    custom_metadata: AssetCustomMetadata = msgspec.field(name="customMetadata")
    error: str


class AssetCustomMetadataBatch(NexusStruct):
    """
    Represents a batch of custom metadata for an asset.

    Attributes:
        errors (List[AssetCustomMetadataError]): The errors for the custom metadata.
        custom_metadatas (List[AssetCustomMetadata]): The custom metadata.
    """

    errors: List[AssetCustomMetadataError]
    custom_metadatas: List[AssetCustomMetadata] = msgspec.field(name="customMetadatas")


class DeleteCustomMetadataBatchError(NexusStruct):
    """
    Represents an error for a custom metadata batch.

    Attributes:
        id (str): The ID of the custom metadata.
        error (str): The error message.
    """

    id: str
    error: str


class DeleteCustomMetadataBatchResponse(NexusStruct):
    """
    Represents the response to a delete custom metadata batch request.

    Attributes:
        errors (List[DeleteCustomMetadataBatchError]): The errors for the custom metadata.
    """

    errors: List[DeleteCustomMetadataBatchError] = []


class ArtifactModel(NexusStruct):
    """
    Represents a model associated with an artifact, detailing its status and download information.

    Attributes:
        id (str): Unique identifier of the artifact model.
        artifact_id (str): Identifier of the artifact associated with the model.
        status (str): Current status of the model.
        format (str): Format of the model.
        quantization (str): Quantization of the model.
        create_date (int): Creation date of the model as an integer timestamp.
        download (Optional[DownloadSignedUrl]): Signed URL for downloading the model, if available.
    """

    id: str
    artifact_id: str = msgspec.field(name="artifactId")
    status: str
    format: str
    quantization: str
    create_date: int = msgspec.field(name="createDate")
    download: Optional[DownloadSignedUrl] = None


ArtifactModels = List[ArtifactModel]


class ArtifactExportOptimizations(NexusStruct):
    """
    Represents optimization options for artifact export.

    Attributes:
        quantization (Union[List[str], str]): Quantization options for optimization.
            Can be a list of quantization options or a single quantization option.
    """

    quantization: Union[List[str], str]


class ArtifactExportOptions(NexusStruct):
    """
    Represents options for exporting an artifact.

    Attributes:
        format (str): Format in which the artifact should be exported.
        optimizations (ArtifactExportOptimizations): Optimization options for the export.
        default_optimizations (ArtifactExportOptimizations):
            Default optimization options for the export.
    """

    format: str
    optimizations: ArtifactExportOptimizations
    default_optimizations: ArtifactExportOptimizations = msgspec.field(
        name="defaultOptimizations"
    )


class Artifact(InsightArtifact):
    """
    Represents an artifact within a project, detailing its properties and associated metrics.

    Attributes:
        id (str): Unique identifier of the artifact.
        run_id (str): Identifier of the run associated with the artifact.
        project_id (str): Project identifier to which the artifact belongs.
        is_training (bool): Indicates whether the artifact is related to training.
        step (int): Step number in the process.
        flow_title (str): Title of the workflow.
        artifact_name (str): Name of the artifact.
        create_date (int): Creation date of the artifact as an integer timestamp.
        metric (ArtifactMetric): Metrics associated with the artifact.
        is_deployed (bool): Indicates whether the artifact is deployed.
        model_name (str): Name of the model associated with the artifact.
        exportable_formats (List[str]): List of exportable formats for the artifact.
        exports (Optional[List[ArtifactModel]]): List of exported
            models associated with the artifact.
    """

    project_id: str = msgspec.field(name="projectId", default="")
    run_id: str = msgspec.field(name="runId", default="")
    flow_title: str = msgspec.field(name="flowTitle", default="")
    display_name: str = msgspec.field(name="displayName", default="")
    artifact_name: str = msgspec.field(name="artifactName", default="")
    create_date: int = msgspec.field(name="createDate", default=0)
    is_deployed: bool = msgspec.field(name="isDeployed", default=False)
    model_name: str = msgspec.field(name="modelName", default="")
    export_options: List[ArtifactExportOptions] = msgspec.field(
        name="exportOptions", default_factory=list
    )
    exports: Optional[List[ArtifactModel]] = None


Artifacts = List[Artifact]


class RunAccelerator(NexusStruct):
    """
    Describes a training accelerator, specifying its name and count.

    Attributes:
        name (str): Name of the accelerator (e.g., GPU type).
        count (int): Number of accelerator units.
    """

    name: str
    count: int


class RunLimit(NexusStruct):
    """
    Represents a limit on a specific metric during training.

    Attributes:
        metric (str): The name of the metric to which the limit applies.
        value (int): The value of the limit for the specified metric.
    """

    metric: str
    value: int


class RunExecution(NexusStruct):
    """
    Describes the execution parameters for a training process.

    Attributes:
        accelerator (Optional[RunAccelerator]): The accelerator used for training, if any.
        checkpoint (Optional[RunCheckpoint]): Checkpointing configuration used during training.
        limit (Optional[RunLimit]): Limit configuration applied to the training process.
    """

    accelerator: Optional[RunAccelerator] = None
    checkpoint: Optional[RunCheckpoint] = None
    limit: Optional[RunLimit] = None


class RunFeatures(NexusStruct):
    """
    Specifies the additional features enabled for the training process.

    Attributes:
        preview (bool): Indicates whether a preview feature is enabled.
            [DEPRECATED] This will be merged with `advanced_evaluation`
            in version 1.9.0.
        matrix (bool): Indicates whether a matrix feature is enabled.
            [DEPRECATED] This will be merged with `advanced_evaluation`
            in version 1.9.0.
        advanced_evaluation (bool): Indicates whether advanced evaluation features are enabled.
        using_sliding_window (bool): Indicates whether a sliding window feature is enabled.
    """

    preview: bool = msgspec.field(name="preview", default=False)
    matrix: bool = msgspec.field(name="matrix", default=False)
    advanced_evaluation: bool = msgspec.field(name="advancedEvaluation", default=False)
    using_sliding_window: bool = msgspec.field(name="usingSlidingWindow", default=False)


class RunStatus(NexusStruct):
    """
    Represents the status of a machine learning model run.

    Attributes:
        overview (str): An overview of the run status.
        message (str): A message providing additional information about the run status.
        update_data (int): The date of the last update to the run status.
    """

    overview: str
    message: str
    update_data: int = msgspec.field(name="updateDate")


class Run(NexusStruct):
    """
    Represents a training process within a project.

    Attributes:
        id (str): Unique identifier for the training process.
        project_id (str): Identifier of the project associated with this training.
        flow_id (str): Identifier of the flow associated with this training.
        execution (RunExecution): Execution details of the training process.
        create_date (int): Creation date of the training process.
        update_date (int): The date when the training was last updated.
        features (Optional[RunFeatures]): Additional features related to the training.
        logs (Optional[List[str]]): Log entries associated with the training process.
    """

    id: str
    project_id: str = msgspec.field(name="projectId")
    flow_id: str = msgspec.field(name="flowId")
    execution: RunExecution
    status: RunStatus
    create_date: int = msgspec.field(name="createDate")
    update_date: int = msgspec.field(name="updateDate")
    features: Optional[RunFeatures] = None
    log_ids: Optional[List[str]] = msgspec.field(name="logIds", default=None)


Runs = List[Run]


class RunLogs(NexusStruct):
    """
    Represents the logs associated with a specific training process.

    Attributes:
        id (str): Unique identifier for the training logs.
        logs (List[Any]): A list of log entries recorded during the training process.
    """

    id: str
    logs: List[Any]


class RunConfusionMatrix(NexusStruct):
    """
    Represents a confusion matrix for a training process, useful for evaluating model performance.

    Attributes:
        data (Any): The data constituting the confusion matrix, usually a multidimensional array.
    """

    data: Any


class Tag(NexusStruct):
    """
    Describes a tag used in a project, typically for categorization or labeling.

    Attributes:
        index (int): The index or identifier of the tag.
        name (str): The name of the tag.
        color (Optional[str]): The color of the tag.
        description (Optional[str]): The description of the tag.
    """

    index: int
    name: str
    color: Optional[str] = None
    description: Optional[str] = None


Tags = List[Tag]


class Workflow(NexusStruct):
    """
    Represents a workflow within a project, detailing its structure and status.

    Attributes:
        id (str): Unique identifier of the workflow.
        project_id (str): Identifier of the project associated with this workflow.
        title (str): Title of the workflow.
        create_date (int): Creation date of the workflow.
        update_date (int): The date when the workflow was last updated.
    """

    id: str
    project_id: str = msgspec.field(name="projectId")
    title: str
    create_date: int = msgspec.field(name="createDate")
    update_date: int = msgspec.field(name="updateDate")


Workflows = List[Workflow]


class OntologyAttributeValue(NexusStruct):
    """
    Represents an attribute in an ontology.

    Attributes:
        id (str): Unique identifier for the ontology attribute.
        name (str): Name of the ontology attribute.
        value (Union[str, int, float, List[str], None]):
            Value for the ontology attribute (if any).
    """

    id: str
    name: str
    value: Union[str, int, float, List[str], None] = None


class AggregationDimensions(NexusStruct):
    """
    Represents the dimensions of an aggregation.

    Attributes:
        height (int): The height of the aggregation.
        width (int): The width of the aggregation.
        depth (int): The depth of the aggregation.
    """

    height: int
    width: int
    depth: int


class AggregationWhole(NexusStruct):
    """
    Represents the whole aggregation.

    Attributes:
        id (str): The id of the aggregation.
        dimensions (AggregationDimensions): The dimensions of the aggregation.
        chunkCount (int): The number of chunks in the aggregation.
        axisLabels (List[str]): The axis labels of the aggregation.
    """

    id: str
    dimensions: AggregationDimensions
    chunkCount: int
    axisLabels: Optional[List[str]] = None


class AggregationThisPart(NexusStruct):
    """
    Represents the this part of the aggregation.

    Attributes:
        chunkNumber (int): The number of the chunk.
        offset (AggregationDimensions): The offset of the chunk.
        size (AggregationDimensions): The size of the chunk.
    """

    chunkNumber: int
    offset: AggregationDimensions
    size: AggregationDimensions


class Aggregation(NexusStruct):
    """
    Represents the aggregation.

    Attributes:
        whole (AggregationWhole): The whole aggregation.
        thisPart (AggregationThisPart): The this part of the aggregation.
    """

    whole: AggregationWhole
    thisPart: AggregationThisPart


class Annotation(NexusStruct):
    """
    Represents an annotation on an asset within a project, detailing its characteristics.

    Attributes:
        id (str): Unique identifier of the annotation.
        project_id (str): Identifier of the project associated with this annotation.
        asset_id (str): Identifier of the asset to which this annotation is linked.
        tag (str): Tag or label associated with the annotation.
        bound_type (str): The type of boundary used for the annotation (e.g., box, polygon).
        create_date (int): Creation date of the annotation as an integer timestamp.
        bound (Union[[], List[Tuple[float, float]], List[Tuple[float, float, int]]]):
            The coordinates defining the boundary of the annotation.
        frame (Optional[int]): Frame number if the annotation is associated with a video asset.
        sequence (Optional[str]): Sequence identifier if the annotation is part of a sequence.
        ontology_id (Optional[str]): Identifier of the ontology associated with the annotation.
        attributes (Optional[List[OntologyAttributeValue]]):
            List of attributes associated with the annotation.
    """

    id: str
    project_id: str = msgspec.field(name="projectId")
    asset_id: str = msgspec.field(name="assetId")
    tag: str
    bound_type: str = msgspec.field(name="boundType")
    bound: List[Union[Any, Tuple[float, float], Tuple[float, float, int]]]
    frame: Optional[int] = None
    sequence: Optional[str] = None
    create_date: int = msgspec.field(name="createDate", default=None)
    ontology_id: str = msgspec.field(name="ontologyId", default=None)
    attributes: List[OntologyAttributeValue] = msgspec.field(
        name="attributes", default=None
    )
    aggregation: Optional[Aggregation] = None
    chunkData: Optional[str] = msgspec.field(name="chunkData", default=None)


GroupedAnnotation = List[Annotation]


class DeploymentOptions(NexusStruct):
    """ "
    Represents the configuration options for a deployment.

    Attributes:
        evaluation_strategy (Optional[str]): The strategy used for evaluation.
        evaluation_threshold (Optional[float]):
            The threshold used to trigger post-evaluation actions.
        evaluation_group (Optional[List[str]]): The asset group to which assets
            triggered by the active learning route will be uploaded.
    """

    evaluation_strategy: Optional[str] = None
    evaluation_threshold: Optional[float] = None
    evaluation_group: Optional[List[str]] = None


class DeploymentScaling(NexusStruct):
    """
    Describes the scaling configuration for a deployment, such as the number of instances.

    Attributes:
        num_instances (int): The number of instances to be used in the deployment.
        mode (str): The scaling mode, describing how scaling is managed (e.g., manual, auto).
    """

    replicas: int
    mode: str


class DeploymentResources(NexusStruct):
    """
    Represents the resources allocated for a deployment, including CPU, RAM, and GPU.

    Attributes:
        cpu (Optional[int]): The amount of CPU allocated for the deployment.
        ram (Optional[int]): The amount of RAM allocated for the deployment, typically in megabytes.
        GPU_T4 (Optional[int]): The number of T4 GPUs allocated for the deployment.
        GPU_L4 (Optional[int]): The number of L4 GPUs allocated for the deployment.
        GPU_A100_40GB (Optional[int]): The number of A100 40GB GPUs allocated for the deployment.
        GPU_A100_80GB (Optional[int]): The number of A100 80GB GPUs allocated for the deployment.
        GPU_H100 (Optional[int]): The number of H100 GPUs allocated for the deployment.
    """

    cpu: Optional[int] = None
    ram: Optional[int] = None
    GPU_T4: Optional[int] = None
    GPU_L4: Optional[int] = None
    GPU_A100_40GB: Optional[int] = None
    GPU_A100_80GB: Optional[int] = None
    GPU_H100: Optional[int] = None


class DeploymentHistoryVersion(NexusStruct):
    """
    Represents a specific version within the deployment history.

    Attributes:
        version_tag (str): The tag identifying the version.
            This is typically used for version control and identification.
        artifact_id (str): The identifier of the artifact
            associated with this version of the deployment.
        update_date (int): The date and time when this version was last updated,
            represented in Unix milliseconds format.
    """

    version_tag: str = msgspec.field(name="versionTag")
    artifact_id: str = msgspec.field(name="artifactId")
    update_date: int = msgspec.field(name="updateDate")


class DeploymentStatus(NexusStruct):
    """
    Represents the status of a deployed model.

    Attributes:
        overview (str): An overview of the deployment status.
        message (str): A message providing additional information about the deployment status.
        update_data (int): The date of the last update to the deployment status.
    """

    overview: str
    message: str
    update_data: int = msgspec.field(name="updateDate")


class Deployment(NexusStruct):
    """
    Describes a deployment of a project artifact, including its configuration and status.

    Attributes:
        id (str): Unique identifier of the deployment.
        name (str): The name of the deployment.
        status (DeploymentStatus): Current status of the deployment.
        create_date (int): Creation date of the deployment.
        update_date (int): The date when the deployment was last updated.
        project_id (str): Identifier of the project associated with this deployment.
        artifact_id (str): Identifier of the artifact being deployed.
        version_tag (str): The version tag of the deployment.
        region (Optional[str]): The region where the deployment is located.
        history_versions (Optional[List[DeploymentHistoryVersion]]):
            List of versions in the deployment history.
        options: DeploymentOptions): The configuration options for the deployment.
        instance_id (Optional[str]): The instance identifier of the deployment.
        resources (Optional[DeploymentResources]): The resources allocated for the deployment.
        scaling (Optional[DeploymentScaling]): The scaling configuration for the deployment.
        url (Optional[str]): URL where the deployment is accessible, if applicable.
    """

    id: Optional[str] = None
    name: Optional[str] = None
    status: Optional[DeploymentStatus] = None
    create_date: Optional[int] = msgspec.field(name="createDate", default=None)
    update_date: Optional[int] = msgspec.field(name="updateDate", default=None)
    project_id: Optional[str] = msgspec.field(name="projectId", default=None)
    artifact_id: Optional[str] = msgspec.field(name="artifactId", default=None)
    version_tag: Optional[str] = msgspec.field(name="versionTag", default=None)
    region: Optional[str] = None
    history_versions: Optional[List[DeploymentHistoryVersion]] = msgspec.field(
        name="historyVersions", default=None
    )
    options: Optional[DeploymentOptions] = None
    instance_id: Optional[str] = msgspec.field(name="instanceId", default=None)
    resources: Optional[DeploymentResources] = None
    scaling: Optional[DeploymentScaling] = None
    url: Optional[str] = None


Deployments = List[Deployment]


class InstanceAccelerator(NexusStruct):
    """
    Represents an accelerator available for deployment.

    Attributes:
        kind (str): The type of accelerator (e.g. NvidiaGpu).
        name (str): The name of the accelerator.
        count (int): The number of accelerators available.
        cuda_cores (Optional[int]): The number of CUDA cores available.
        vram_bytes (Optional[int]): The amount of VRAM available in bytes.
    """

    kind: str
    name: str
    count: int
    cuda_cores: Optional[int] = msgspec.field(name="cudaCores", default=None)
    vram_bytes: Optional[int] = msgspec.field(name="vramBytes", default=None)


class AvailableInstance(NexusStruct):
    """
    Represents an instance available for deployment.

    Attributes:
        id (str): Unique identifier of the instance.
        resources (DeploymentResources): The resources allocated for the instance.
        regions (List[str]): The regions where the instance is available.
    """

    id: str = msgspec.field(name="instanceId")
    resources: DeploymentResources
    regions: List[str]
    accelerator: Optional[InstanceAccelerator] = None


class AvailableInstances(NexusStruct):
    """
    Represents available instances for deployment.

    Attributes:
        artifact_id (str): Identifier of the artifact associated with the available instances.
        region (str): The region where the instances are available.
        instances (List[AvailableInstance]): List of available instances.
    """

    artifact_id: str = msgspec.field(name="artifactId")
    region: str
    instances: List[AvailableInstance] = msgspec.field(name="availableInstances")


class ImportSessionAnnotationStatus(NexusStruct):
    """
    Represents the count of annotations in different processing states within an import session.

    Attributes:
        Processed (int): The number of annotations that have been processed.
        Committed (int): The number of annotations that have been committed.
    """

    Processed: int
    Committed: int


class ImportSessionFilesStatus(NexusStruct):
    """
    Represents the count of files in various processing states within an import session.

    Attributes:
        Processing (int): The number of files currently being processed.
        Processed (int): The number of files that have been processed.
        FailedProcess (int): The number of files that failed during processing.
    """

    Processing: int
    Processed: int
    FailedProcess: int


class ImportSessionStatusAnnotations(NexusStruct):
    """
    Represents the status of annotations within an import session.

    Attributes:
        with_status (ImportSessionAnnotationStatus):
            The count of annotations in different processing states.
    """

    with_status: ImportSessionAnnotationStatus = msgspec.field(name="withStatus")


class ImportSessionStatusFiles(NexusStruct):
    """
    Represents the status of files within an import session.

    Attributes:
        total_size_bytes (int): The total size of all files in bytes.
        page_count (int): The number of pages of files.
        status_count (ImportSessionStatusFilesCount):
            The count of files in various processing states.
    """

    total_size_bytes: int = msgspec.field(name="totalSizeBytes")
    page_count: int = msgspec.field(name="pageCount")
    with_status: ImportSessionFilesStatus = msgspec.field(name="withStatus")


class ImportSessionStatus(NexusStruct):
    """
    Represents the status of an import session.

    Attributes:
        overview (str): An overview of the import session status.
        message (str): A message providing additional information about the import session status.
        update_date (int): The date of the last update to the import session status.
        annotations (ImportSessionStatusAnnotations):
            Status information related to annotations during the import session.
        files (ImportSessionStatusFiles):
            Status information related to files processed during the import session.
    """

    overview: str
    message: str
    update_date: int = msgspec.field(name="updateDate")
    annotations: ImportSessionStatusAnnotations
    files: ImportSessionStatusFiles


class ImportSession(NexusStruct):
    """
    Represents a session for importing data into a project, including its status and validity.

    Attributes:
        id (str): Unique identifier of the import session.
        project_id (str): Identifier of the project associated with this import session.
        status (Any): Current status of the import session.
        expiry_date (int): Expiration date of the import session as an integer timestamp.
        create_date (int): Creation date of the import session.
        update_date (int): The date when the import session was last updated.
    """

    id: str
    project_id: str = msgspec.field(name="projectId")
    status: ImportSessionStatus
    expiry_date: int = msgspec.field(name="expiryDate")
    create_date: int = msgspec.field(name="createDate")
    update_date: int = msgspec.field(name="updateDate")


ImportSessions = List[ImportSession]


class ImportSessionFile(NexusStruct):
    """
    Represents a file within an import session, including its name and upload URL.

    Attributes:
        filename (str): The name of the file to be imported.
        upload (UploadSignedUrl): The signed URL for uploading the file.
    """

    filename: str
    upload: UploadSignedUrl


class InsertImportSessionFiles(NexusStruct):
    """
    Describes a batch of files to be inserted into an import session.

    Attributes:
        id (str): Unique identifier of the import session to which these files belong.
        project_id (str): Identifier of the project associated with these files.
        files (List[ImportSessionFile]): List of files to be included in the import session.
    """

    id: str
    project_id: str = msgspec.field(name="projectId")
    files: List[ImportSessionFile]


class ImportSessionLogLogItem(NexusStruct):
    """
    Represents a single log entry in an import session.

    Attributes:
        timestamp (float): The timestamp when the log entry was recorded.
        level (str): The severity level of the log entry (e.g., 'INFO', 'ERROR').
        message (str): The message content of the log entry.
    """

    timestamp: float
    level: str
    message: str


class ImportSessionLog(NexusStruct):
    """
    Represents a collection of log entries for an import session.

    Attributes:
        id (str): Unique identifier of the import session.
        project_id (str): Identifier of the project associated with this import session.
        logs (List[ImportSessionLogLogItem]): A list of log entries for the import session.
    """

    id: str
    project_id: str = msgspec.field(name="projectId")
    logs: List[ImportSessionLogLogItem]


class LocalArtifact(NexusStruct):
    """
    Represents a local artifact consisting of model and label files.

    Attributes:
        download_path (str): The path where the artifact is downloaded or stored locally.
        model_filename (str): The filename of the model file included in the artifact.
        label_filename (str): The filename of the label file included in the artifact.
    """

    download_path: str
    model_filename: str
    label_filename: str


class ExportedAnnotations(NexusStruct):
    """
    Represents the exported annotations from a project or operation.

    Attributes:
        op_id (str):
            The identifier of the operation associated with the export of annotations.
        status (str):
            The current status of the exported annotations (e.g., 'completed', 'in-progress').
        download (Optional[DownloadSignedUrl]):
            An optional URL for downloading the exported annotations, if available.
    """

    op_id: str = msgspec.field(name="opId")
    status: str
    download: Optional[DownloadSignedUrl] = None


class LocalAnnotations(NexusStruct):
    """
    Represents local annotations stored in the filesystem,
        including their download path and file names.

    Attributes:
        download_path (str):
            The file system path where the annotations are downloaded or stored locally.
        file_names (List[str]):
            A list of file names for the annotation files stored at the download path.
    """

    download_path: str
    file_names: List[str]


class OperationProgressWithStatus(NexusStruct):
    """
    Represents the count of operations in various states.

    Attributes:
        Queued (int): The number of operations that are queued.
        Running (int): The number of operations that are currently running.
        Finished (int): The number of operations that have finished.
        Cancelled (int): The number of operations that have been cancelled.
        Errored (int): The number of operations that have encountered errors.
    """

    Queued: int
    Running: int
    Finished: int
    Cancelled: int
    Errored: int


class OperationProgress(NexusStruct):
    """
    Represents the progress status of an operation.

    Attributes:
        unit (str): The unit of measurement for the progress (e.g., 'files', 'percent').
        with_status (OperationProgressWithStatus):
            The progress of the operation categorized by different statuses.
    """

    unit: str
    with_status: OperationProgressWithStatus = msgspec.field(name="withStatus")


class OperationStatus(NexusStruct):
    """
    Represents the status of an operation.

    Attributes:
        overview (str): A brief overview or summary of the operation's status.
        message (str): A detailed message describing the current status of the operation.
        progress (OperationProgress): The progress of the operation.
    """

    overview: str
    message: str
    progress: OperationProgress


class Operation(NexusStruct):
    """
    Represents an operation within the Datature Nexus system.

    Attributes:
        id (str): The unique identifier of the operation.
        kind (str): The kind or type of the operation.
        status (OperationStatus): The current status of the operation.
        create_date (int): The timestamp when the operation was created.
        update_date (int): The timestamp when the operation was last updated.
    """

    id: str
    kind: str
    status: OperationStatus
    create_date: int = msgspec.field(name="createDate")
    update_date: int = msgspec.field(name="updateDate")


class OntologyAttributeOptions(NexusStruct):
    """
    Represents options available for an ontology attribute.

    Attributes:
        categories (List[str]): List of categories for the ontology attribute options.
    """

    categories: List[str] = msgspec.field(name="categories")


class OntologyAttribute(NexusStruct):
    """
    Represents an attribute in an ontology.

    Attributes:
        id (str): Unique identifier for the ontology attribute.
        name (str): Name of the ontology attribute.
        description (str): Description of the ontology attribute.
        type (str): Type of the ontology attribute.
        required (bool): Indicates whether the ontology attribute is required.
        options (Union[OntologyAttributeOptions, None]):
            Options available for the ontology attribute (if any).
        default (Union[str, int, List[str], None]):
            Default value for the ontology attribute (if any).
    """

    id: str
    name: str
    description: str
    type: str
    required: bool
    options: Union[OntologyAttributeOptions, None] = None
    default: Union[str, int, float, List[str], None] = None


class Ontology(NexusStruct):
    """
    Represents an ontology.

    Attributes:
        id (str): Unique identifier for the ontology.
        project_id (str): Identifier of the project to which the ontology belongs.
        index (int): Index of the ontology tag.
        name (str): Name of the ontology tag.
        color (Optional[str]): The color of the tag.
        description (Optional[str]): The description of the tag.
        attributes (List[OntologyAttribute]): List of attributes in the ontology (default is None).
    """

    id: str
    project_id: str = msgspec.field(name="projectId")
    index: int
    name: str
    version: int
    color: Optional[str] = None
    description: Optional[str] = None
    attributes: List[OntologyAttribute] = msgspec.field(name="attributes", default=None)


Ontologies = List[Ontology]


class Object(NexusStruct):
    """
    Represents an object within a project.

    Attributes:
        annotations (List[GroupedAnnotation]):
            List of grouped annotations associated with the object. Grouped annotations
            consist of one or more annotations that are associated within the same group.
        assets (List[Asset]): List of assets associated with the annotations.
    """

    annotations: List[GroupedAnnotation]
    assets: List[Asset]


class PredictionMetadata(NexusStruct):
    """
    Represents metadata associated with a prediction.

    Attributes:
        average_confidence (float): The average confidence of the prediction.
    """

    average_confidence: float = msgspec.field(name="averageConfidence")


class PredictionSliceMetadata(NexusStruct):
    """
    Represents metadata associated with a prediction slice.

    Attributes:
        average_confidence (float): The average confidence of the prediction slice.
        average_confidence_for_tag (Dict[str, float]): The average confidence for each tag.
        prediction_count (int): The number of predictions in the slice.
        prediction_count_for_tag (Dict[str, int]): The number of predictions for each tag.
    """

    average_confidence: float = msgspec.field(name="averageConfidence")
    average_confidence_for_tag: Dict[str, float] = msgspec.field(
        name="averageConfidenceForTag"
    )
    prediction_count: int = msgspec.field(name="predictionCount")
    prediction_count_for_tag: Dict[str, int] = msgspec.field(
        name="predictionCountForTag"
    )


class PredictionSlice(NexusStruct):
    """
    Represents a slice of a prediction.

    Attributes:
        project (str): The project to which the prediction slice belongs.
        asset_id (str): The identifier of the asset associated with the prediction slice.
        filename (str): The name of the file.
        slice (dict): The slice of the prediction.
        snapshot_id (str): The identifier of the snapshot associated with the prediction slice.
        run_id (str): The identifier of the run associated with the prediction slice.
        artifact_id (str): The identifier of the artifact associated with the prediction slice.
        id (str): The identifier of the prediction slice.
        prediction_metadata (PredictionSliceMetadata): Metadata associated with the prediction slice.
    """

    project: str
    asset_id: str = msgspec.field(name="assetId")
    filename: str
    slice: dict
    snapshot_id: str = msgspec.field(name="snapshotId")
    run_id: str = msgspec.field(name="runId")
    artifact_id: str = msgspec.field(name="artifactId")
    id: str
    prediction_metadata: PredictionSliceMetadata = msgspec.field(
        name="predictionMetadata"
    )


class PredictionObject(NexusStruct):
    """
    Represents a prediction object.

    Attributes:
        id (str): The identifier of the prediction object.
        object (str): The object associated with the prediction.
        prediction_slice (PredictionSlice): Prediction slice associated with the prediction object.
        metadata (PredictionMetadata): Metadata associated with the prediction.
        tag (Tag): The tag associated with the prediction.
        bound (Dict[str, Any]): The coordinate bounds of the prediction.
    """

    id: str
    object: str
    prediction_slice: PredictionSlice = msgspec.field(name="predictionSlice")
    metadata: PredictionMetadata
    tag: Tag
    bound: Dict[str, Any]


class Prediction(NexusStruct):
    """
    Represents a prediction.

    Attributes:
        id (str): The identifier of the prediction.
        project (str): The project to which the prediction belongs.
        asset_id (str): The identifier of the asset associated with the prediction.
        filename (str): The name of the file.
        snapshot_id (str): The identifier of the snapshot associated with the prediction.
        run_id (str): The identifier of the run associated with the prediction.
        artifact_id (str): The identifier of the artifact associated with the prediction.
        objects (List[PredictionObject]): The objects associated with the prediction.
    """

    predictions: List[PredictionObject]


class SequenceEntryAsset(NexusStruct):
    """
    Represents an entry asset in a sequence.

    Attributes:
        asset_id (str): The identifier of the asset.
        ord (int): The order of the asset.
        role (Optional[str]): The role of the asset.
    """

    asset_id: str = msgspec.field(name="assetId")
    ord: int
    role: Optional[str] = None


class SequenceAttributes(NexusStruct):
    """
    Represents the attributes of a sequence.

    Attributes:
        bytes_used (int): The number of bytes used by the sequence attributes.
        bytes_total (int): The maximum number of bytes allowed for the sequence attributes.
        items (Dict[str, str]): The items of the sequence attributes.
    """

    bytes_used: int = msgspec.field(name="bytesUsed")
    bytes_total: int = msgspec.field(name="bytesTotal")
    items: Optional[Dict[str, str]] = None


class Sequence(NexusStruct):
    """
    Represents a sequence.

    Attributes:
        id (str): The identifier of the sequence.
        name (str): The name of the sequence.
        project_id (str): The identifier of the project.
        items (List[SequenceEntryAsset]): The items of the sequence.
        attributes (SequenceAttributes): The attributes of the sequence.
        create_date (int): The creation date of the sequence.
        update_date (int): The update date of the sequence.
    """

    id: str
    name: str
    length: int
    project_id: str = msgspec.field(name="projectId")
    items: List[SequenceEntryAsset]
    item_count_with_role: Dict[str, int] = msgspec.field(name="itemCountWithRole")
    attributes: SequenceAttributes
    create_date: int = msgspec.field(name="createDate")
    update_date: int = msgspec.field(name="updateDate")


@add_mapping
@unique
class SequenceBulkUpdateResult(Enum):
    """Sequence bulk update result."""

    OK = "Ok"
    FAILED = "Failed"
    FAILED_LINK_ASSET_ALREADY_PROCESSED = "FailedLinkAssetAlreadyProcessed"
    FAILED_LINK_ASSET_NOT_FOUND = "FailedLinkAssetNotFound"
    FAILED_LINK_WOULD_OVERWRITE_EXISTING_ITEM = "FailedLinkWouldOverwriteExistingItem"
    FAILED_LINK_SEQUENCE_WOULD_EXCEED_MAXIMUM_ITEM_COUNT = (
        "FailedLinkSequenceWouldExceedMaximumItemCount"
    )
    FAILED_PATCH_SEQUENCE_SEQUENCE_NOT_FOUND = "FailedPatchSequenceSequenceNotFound"
    FAILED_PATCH_SEQUENCE_ATTRIBUTE_SIZE_WOULD_EXCEED_LIMIT = (
        "FailedPatchSequenceAttributeSizeWouldExceedLimit"
    )
    FAILED_PATCH_SEQUENCE_RENAME_WOULD_DUPLICATE = (
        "FailedPatchSequenceRenameWouldDuplicate"
    )
    FAILED_PATCH_SEQUENCE_SEQUENCE_ALREADY_PROCESSED = (
        "FailedPatchSequenceSequenceAlreadyProcessed"
    )
    FAILED_REMOVE_SEQUENCE_SEQUENCE_NOT_FOUND = "FailedRemoveSequenceSequenceNotFound"
    FAILED_REMOVE_SEQUENCE_SEQUENCE_ALREADY_PROCESSED = (
        "FailedRemoveSequenceSequenceAlreadyProcessed"
    )

    __MAPPING__ = {
        "Ok": OK,
        "Failed": FAILED,
        "FailedLinkAssetAlreadyProcessed": FAILED_LINK_ASSET_ALREADY_PROCESSED,
        "FailedLinkAssetNotFound": FAILED_LINK_ASSET_NOT_FOUND,
        "FailedLinkWouldOverwriteExistingItem": FAILED_LINK_WOULD_OVERWRITE_EXISTING_ITEM,
        "FailedLinkSequenceWouldExceedMaximumItemCount": FAILED_LINK_SEQUENCE_WOULD_EXCEED_MAXIMUM_ITEM_COUNT,
        "FailedPatchSequenceSequenceNotFound": FAILED_PATCH_SEQUENCE_SEQUENCE_NOT_FOUND,
        "FailedPatchSequenceAttributeSizeWouldExceedLimit": FAILED_PATCH_SEQUENCE_ATTRIBUTE_SIZE_WOULD_EXCEED_LIMIT,
        "FailedPatchSequenceRenameWouldDuplicate": FAILED_PATCH_SEQUENCE_RENAME_WOULD_DUPLICATE,
        "FailedPatchSequenceSequenceAlreadyProcessed": FAILED_PATCH_SEQUENCE_SEQUENCE_ALREADY_PROCESSED,
        "FailedRemoveSequenceSequenceNotFound": FAILED_REMOVE_SEQUENCE_SEQUENCE_NOT_FOUND,
        "FailedRemoveSequenceSequenceAlreadyProcessed": FAILED_REMOVE_SEQUENCE_SEQUENCE_ALREADY_PROCESSED,
    }


class SequenceBulkUpdateResults(NexusStruct):
    """Sequence bulk update results.

    Attributes:
        actions (List[SequenceBulkUpdateResult]): The list of sequence bulk update results.
    """

    actions: List[SequenceBulkUpdateResult]
