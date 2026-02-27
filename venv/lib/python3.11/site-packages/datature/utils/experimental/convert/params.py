#!/usr/env/bin python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   params.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   TensorRT parameters module.
"""

# pylint: disable=R0902

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DockerParams:
    """
    Docker parameters for conversion and inference.

    Args:
        conversion_docker_image (str, optional):
            Docker image for conversion. Defaults to "nvcr.io/nvidia/tensorflow:23.04-tf2-py3".
        inference_docker_image (str, optional):
            Docker image for inference. Defaults to "nvcr.io/nvidia/tritonserver:23.04-py3".
        device (int, optional): Device to use for conversion. Defaults to 0.
        workspace_path (str, optional): Workspace path. Defaults to "/workspace".
        dir_perms (str, optional): Directory permissions. Defaults to "rw".
    """

    conversion_docker_image: Optional[str] = "nvcr.io/nvidia/tensorflow:23.04-tf2-py3"
    inference_docker_image: Optional[str] = "nvcr.io/nvidia/tritonserver:23.04-py3"
    device: Optional[int] = 0
    workspace_path: Optional[str] = "/workspace"
    dir_perms: Optional[str] = "rw"


@dataclass
class CheckParams:
    """
    Parameters for `polygraphy check lint`, which topologically "lints"
    an ONNX model to find faulty nodes in the graph.

    Args:
        enabled (bool, optional): Enables `polygraphy check lint`. Defaults to False.
        output_json_path (str, optional):
            Output JSON path. Defaults to ".datature_logs/<CURRENT_TIME>.json".
        provider (str, optional): Execution provider for ONNX model loading. Defaults to "cpu".
        timeout (int, optional): Timeout for lint. Defaults to 1800 seconds.
        verbose (bool, optional): Verbose output. Defaults to False.
    """

    enabled: Optional[bool] = False
    output_json_path: Optional[str] = f".datature_logs/{int(time.time())}.json"
    provider: Optional[str] = "cpu"
    timeout: Optional[int] = 1800
    verbose: Optional[bool] = False


@dataclass
class SanitizeParams:
    """
    Parameters for `polygraphy surgeon sanitize`, which runs ONNX graph surgeon to
    clean up and optimize input shapes in an ONNX model.

    Args:
        enabled (bool, optional): Enables `polygraphy surgeon sanitize`. Defaults to False.
        output_model_path (str, optional): Output path to save sanitized model. Defaults to "".
        cleanup (bool, optional): Run dead layer removal on the graph.
            This is generally not required if other options are set.
        toposort (bool, optional): Topologically sort nodes in the graph.
        no_shape_inference (bool, optional):
            Disable ONNX shape inference when loading the model. Defaults to False.
        force_fallback_shape_inference (bool, optional):
            Force Polygraphy to use ONNX-Runtime to determine metadata
            for tensors in the graph. This can be useful in cases where
            ONNX shape inference does not generate correct information.
            Note that this will cause dynamic dimensions to become static.
        fold_constants (bool, optional):
            Fold constants in the graph by computing subgraphs whose
            values are not dependent on runtime inputs. Defaults to False.
        num_passes (int, optional):
            The number of constant folding passes to run. Sometimes,
            subgraphs that compute tensor shapes may not be foldable in a single pass.
            If not specified, Polygraphy will automatically determine the number of passes
            required. Defaults to None.
        partitioning (str, optional):
            Controls how to partition the graph during constant folding:
            {{'basic': Partition the graph so failures in one part do not affect other parts,
            'recursive': In addition to partitioning the graph, partition partitions where
            needed}}. Defaults to None.
        no_fold_shapes (bool, optional): Disable folding Shape nodes and
            subgraphs that operate on shapes. Defaults to False.
        no_per_pass_shape_inference (bool, optional): Disable shape inference between
            passes of constant folding. Defaults to False.
        timeout (int, optional): Timeout for model sanitization. Defaults to 1800 seconds.
        verbose (bool, optional): Verbose output. Defaults to False.
        log_dir (str, optional): Log directory. Defaults to ".datature_logs".
    """

    enabled: Optional[bool] = False
    output_model_path: Optional[str] = ""
    cleanup: Optional[bool] = False
    toposort: Optional[bool] = False
    no_shape_inference: Optional[bool] = False
    force_fallback_shape_inference: Optional[bool] = False
    fold_constants: Optional[bool] = False
    num_passes: Optional[int] = None
    partitioning: Optional[str] = None
    no_fold_shapes: Optional[bool] = False
    no_per_pass_shape_inference: Optional[bool] = False
    timeout: Optional[int] = 1800
    verbose: Optional[bool] = False
    log_dir: Optional[str] = ".datature_logs"


@dataclass
class ConversionExperimentalParams:
    """
    Experimental parameters for TensorRT conversion.

    Args:
        check_params (CheckParams, optional):
            Parameters for `polygraphy check lint`. Defaults to None.
        sanitize_params (SanitizeParams, optional):
            Parameters for `polygraphy surgeon sanitize`. Defaults to None.
        sparse_weights (bool, optional):
            Whether to enable optimizations for sparse weights in TensorRT. Defaults to False.
        version_compatible (bool, optional): Whether to build an engine designed to be
            forward TensorRT version compatible. Defaults to False.
        error_on_timing_cache_miss (bool, optional): Whether to emit errors when a
            tactic being timed is not present in the timing cache. Defaults to False.
        load_timing_cache (str, optional): Load specified file containing tactic timing cache
            used to speed up the TensorRT engine building process. Defaults to None.
        save_timing_cache (str, optional):
            Save tactic timing cache to specified file. Defaults to None.
        disable_compilation_cache (bool, optional):
            Whether to disable caching of JIT-compiled code. Defaults to False.
        load_tactics (str, optional): Load specified tactic replay file to
            override tactics in TensorRT's default selections. Defaults to None.
        save_tactics (str, optional): Save tactics selected by TensorRT
            to a specified JSON file. Defaults to None.
    """

    check_params: CheckParams = field(default_factory=CheckParams)
    sanitize_params: SanitizeParams = field(default_factory=SanitizeParams)
    sparse_weights: Optional[bool] = False
    version_compatible: Optional[bool] = False
    error_on_timing_cache_miss: Optional[bool] = False
    load_timing_cache: Optional[str] = None
    save_timing_cache: Optional[str] = None
    disable_compilation_cache: Optional[bool] = False
    load_tactics: Optional[str] = None
    save_tactics: Optional[str] = None


@dataclass
class ConversionParams:
    """
    Parameters for TensorRT conversion.

    Args:
        precision (str, optional): Floating-point precision for TensorRT conversion,
            either "FP32" or "FP16". Defaults to "FP32".
        autoinstall_deps (bool, optional): Whether Polygraphy will automatically
            install required Python packages at runtime. Defaults to True.
        internal_correctness_checks (bool, optional):
            Whether internal correctness checks are enabled. Defaults to False.
        builder_optimization_level (int, optional):
            Optimization level for TensorRT builder in the range [1, 5].
            A higher optimization level allows the optimizer to spend more time
            searching for optimization opportunities. The resulting engine may have
            better performance compared to an engine built with a lower optimization level,
            but the conversion time will increase significantly. Defaults to 3.
        precision_constraints (str, optional):
            If set to “obey”, require that layers execute in specified precisions.
            If set to “prefer”, prefer that layers execute in specified precisions
            but allow TRT to fall back to other precisions if no implementation exists
            for the requested precision. Otherwise, precision constraints are ignored.
            Defaults to "none".
        timeout (int, optional): Timeout (in seconds) for conversion. Defaults to 1800.
        verbose (bool, optional): Verbose output. Defaults to False.
        log_dir (str, optional): Log directory. Defaults to ".datature_logs".
        experimental (ConversionExperimentalParams, optional):
            Experimental parameters for TensorRT conversion. Defaults to None.
    """

    precision: Optional[str] = "FP32"
    autoinstall_deps: Optional[bool] = True
    internal_correctness_checks: Optional[bool] = False
    builder_optimization_level: Optional[int] = 3
    precision_constraints: Optional[str] = "none"
    timeout: Optional[int] = 1800
    verbose: Optional[bool] = False
    log_dir: Optional[str] = ".datature_logs"
    experimental: Optional[ConversionExperimentalParams] = None
