#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   converter.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   TensorRT converter module
"""

# pylint: disable=E1102,R0902,R0913,R0914,R0915

import os
import shutil
import subprocess
import time
from typing import Dict, List, Optional, Tuple

from datature.nexus import config, error, models
from datature.nexus.api.project import Project
from datature.nexus.api.types import OperationStatusOverview

from .logger import trt_logger
from .params import ConversionParams, DockerParams

try:
    import pynvml
except ModuleNotFoundError as import_exc:
    raise ModuleNotFoundError(
        "nvidia-ml-py not installed! "
        "Please visit https://developers.datature.io/docs/tensorrt-export "
        "to learn how to set up your environment."
    ) from import_exc

try:
    import docker
except ModuleNotFoundError as import_exc:
    raise ModuleNotFoundError(
        "Docker not installed! "
        "Please visit https://developers.datature.io/docs/tensorrt-export "
        "to learn how to set up your environment."
    ) from import_exc


class Converter:
    """The Converter class provides an interface to the TensorRT Converter."""

    _min_driver_version: str = "530.00"
    _min_cuda_version: str = "11.8"
    _model_directory: str = ".datature_models"

    def __init__(
        self,
        docker_client,
        api_client,
        docker_params: Optional[DockerParams] = DockerParams(),
        conversion_params: Optional[ConversionParams] = ConversionParams(),
    ) -> None:
        """
        Instantiates the TensorRT Converter.

        Args:
            docker_client (docker.client.DockerClient): The Docker client instance.
            api_client (docker.api.client.APIClient): The Docker API client instance.
            conversion_docker_image (str):
                The Docker image name used for TensorRT conversion,
                defaults to "nvcr.io/nvidia/tensorflow:23.04-tf2-py3".
                The list of Docker images can be found here:
                https://catalog.ngc.nvidia.com/orgs/nvidia/containers/tensorflow/tags
            device (int): GPU id to use for conversion, defaults to 0.
            timeout (int):
                The maximum time in seconds to wait for the conversion process to complete,
                defaults to 1800.
        """

        self._docker_client = docker_client
        self._api_client = api_client
        self._docker_params = docker_params
        self._conversion_params = conversion_params

        try:
            self._device_request = docker.types.DeviceRequest(
                device_ids=[f"{self._docker_params.device}"], capabilities=[["gpu"]]
            )
        except docker.errors.DockerException as device_exc:
            raise ConnectionError(
                f"Could not detect device {self._docker_params.device}. "
                "Please ensure that your system contains an NVIDIA GPU "
                "or NVIDIA-compatible edge device, such as a Jetson."
            ) from device_exc
        self._exec_id = ""
        self._logs = None
        self._cont = None

    def setup(self) -> None:
        """Checks the system environment and sets up the conversion Docker image."""
        os_name = os.uname().sysname

        if os_name == "Darwin":
            raise SystemError(
                "TensorRT conversion is not supported on MacOS. "
                "Please refer to our documentation for supported platforms: "
                "https://developers.datature.io/docs/tensorrt-export"
            )

        if os_name == "Windows":
            raise SystemError(
                f"TensorRT conversion is not supported natively on {os_name}. "
                "You will need to install Windows Subsystem for Linux (WSL). "
                "Please refer to our documentation for supported platforms and "
                "installation guides: https://developers.datature.io/docs/tensorrt-export"
            )

        if os_name == "Linux" and os.path.exists("/proc/sys/kernel/osrelease"):
            with open(
                "/proc/sys/kernel/osrelease", "r", encoding="utf-8"
            ) as os_release:
                if "WSL2" in os_release.read():
                    trt_logger.info("OS: Windows Subsystem for Linux 2 (WSL2)")
                else:
                    trt_logger.info("OS: %s", os_name)

        else:
            raise SystemError(
                f"Your OS {os_name} is unsupported. Please refer to "
                "https://developers.datature.io/docs/tensorrt-export "
                "for supported platforms."
            )

        gpu_info = self._get_gpu_info()

        if gpu_info["driver_version"] is None:
            raise SystemError("Could not determine GPU driver version")

        if str(gpu_info["driver_version"]) < self._min_driver_version:
            raise SystemError(
                f"GPU driver version is less than {self._min_driver_version}, "
                "please upgrade to a newer version. Please refer to "
                "https://developers.datature.io/docs/tensorrt-export "
                "for more information."
            )

        if gpu_info["cuda_version"] is None:
            raise SystemError("Could not determine CUDA version")

        if str(gpu_info["cuda_version"]) < self._min_cuda_version:
            raise SystemError(
                f"CUDA version is less than {self._min_cuda_version}, "
                "please upgrade to a newer version. Please refer to "
                "https://developers.datature.io/docs/tensorrt-export "
                "for more information."
            )

        # environment check: docker and client machine compatibility
        candidate = self._docker_client.images.list(
            filters={"reference": self._docker_params.conversion_docker_image}
        )

        if len(candidate) == 0:
            trt_logger.info(
                "Pulling Docker image %s", self._docker_params.conversion_docker_image
            )
            self._docker_client.images.pull(self._docker_params.conversion_docker_image)

    def convert(
        self,
        model_path: str,
        output_path: str = "",
    ) -> None:
        """
        Converts an ONNX model to TensorRT format.

        Args:
            model_path (str): The path to the saved model directory.
            output_path (str): The path to the output directory.
        """
        try:
            commands = self._get_commands(model_path, output_path)
            self._start_docker_container()
            self._exec_id = self._api_client.exec_create(
                container=self._cont.id,
                cmd=commands,
                environment={
                    "POLYGRAPHY_AUTOINSTALL_DEPS": (
                        1 if self._conversion_params.autoinstall_deps else 0
                    ),
                    "POLYGRAPHY_INTERNAL_CORRECTNESS_CHECKS": (
                        1 if self._conversion_params.internal_correctness_checks else 0
                    ),
                },
            )["Id"]
            self._logs = self._api_client.exec_start(
                self._exec_id, stream=True, detach=False
            )

            self._print_logs()

            if self.get_status() != 0:
                raise error.Error(
                    "TensorRT conversion was not successful, please read "
                    "the error logs printed above or visit "
                    "https://developers.datature.io/docs/tensorrt-export for more information."
                )

            trt_logger.info(
                "TensorRT model conversion successful, model is saved at %s", model_path
            )
            trt_logger.info(
                "Run `with trt.inference_server(YOUR_MODEL_FOLDER):` to spin up "
                "NVIDIA Triton Inference Server for local inference. "
                "Refer to https://developers.datature.io/docs/tensorrt-export "
                "on how to make predictions with your own data."
            )
        except KeyboardInterrupt:
            trt_logger.warning("Keyboard interrupt detected")
        except Exception as exc:
            raise error.Error(exc) from exc
        finally:
            self._cleanup()

    def create_export(
        self,
        project: Project,
        artifact_id: str,
    ) -> str:
        """
        Exports an ONNX model from Datature Nexus given a Project instance
        and an artifact ID, and returns the model ID.

        Args:
            project (Project): The Project instance.
            artifact_id (str): The artifact ID of the model to export.

        Returns:
            str: The exported model ID.

        Raises:
            InternalServerError: If the artifact export encounters an error.
            BadRequestError: If the artifact export has previously been cancelled.
        """
        assert isinstance(project, Project)
        assert isinstance(artifact_id, str)

        target_format = "TensorRT"
        export_options = {"format": target_format}
        is_exported = False

        try:
            model = project.requester.POST(
                f"/projects/{project.project_id}/artifacts/{artifact_id}/hiddenExports",
                request_body=export_options,
                response_type=models.ArtifactModel,
            )
            model_id = model.id
        except error.BadRequestError as exc:
            raise error.BadRequestError(
                "Your model architecture is not supported for TensorRT conversion. "
                "Please refer to our documentation for supported model architectures: "
                "https://developers.datature.io/docs/tensorrt-export"
            ) from exc
        except error.InternalServerError as exc:
            if exc.detail["code"] == "ConflictError":
                trt_logger.info("Model has already been exported, retrieving export")
                is_exported = True
                model_id = [
                    model
                    for model in project.artifacts.list_exported_models(artifact_id)
                    if model.format == target_format
                ][-1].id
            else:
                raise error.InternalServerError(
                    "Artifact export encountered an error, "
                    "please contact our engineers at support@datature.io for support."
                ) from exc

        if not is_exported:
            target_export = [
                export
                for export in project.artifacts.list_exported_models(artifact_id)
                if export.id == model_id
            ][-1]

            while target_export.status != OperationStatusOverview.FINISHED.value:
                if target_export.status == OperationStatusOverview.ERRORED.value:
                    raise error.InternalServerError(
                        "Artifact export encountered an error, "
                        "please contact our engineers at support@datature.io for support."
                    )

                if target_export.status == OperationStatusOverview.CANCELLED.value:
                    raise error.BadRequestError(
                        "Artifact export has previously been cancelled by user, "
                        "please start a new export."
                    )

                time.sleep(config.OPERATION_LOOPING_DELAY_SECONDS)
                target_export = [
                    export
                    for export in project.artifacts.list_exported_models(artifact_id)
                    if export.id == model_id
                ][-1]
        return model_id

    def download_export(self, project: Project, model_id: str) -> str:
        """
        Downloads the exported model from Nexus to a local directory given a model ID,
        and returns the path to the downloaded model.

        Args:
            project (Project): The Project instance.
            model_id (str): The model ID of the model to download.

        Returns:
            str: The path to the downloaded model.

        Raises:
            FileNotFoundError: If the path to the downloaded ONNX model cannot be found.
        """
        download_details = project.artifacts.download_exported_model(
            model_id, self._model_directory
        )
        model_path = os.path.join(
            download_details.download_path, download_details.model_filename
        )

        if not os.path.exists(model_path):
            raise FileNotFoundError(
                "There was a problem locating your model file, "
                "please ensure that you have provided a valid directory "
                "and re-run the .convert() function again"
            )

        return model_path

    def _start_docker_container(self) -> None:
        """Starts docker container used for TensorRT conversion."""
        working_dir = os.getcwd()

        self._docker_client.images.get(self._docker_params.conversion_docker_image)
        container = self._docker_client.containers.run(
            self._docker_params.conversion_docker_image,
            stdin_open=True,
            auto_remove=True,
            detach=True,
            volumes={
                working_dir: {
                    "bind": self._docker_params.workspace_path,
                    "mode": self._docker_params.dir_perms,
                }
            },
            device_requests=[self._device_request],
        )
        self._cont = self._docker_client.containers.get(container.id)
        self._cont.start()

        start = time.time()
        while self._cont.status != "running":
            self._cont = self._docker_client.containers.get(container.id)

            if self._cont.status == "running":
                pass
            elif self._cont.status == "paused":
                self._cont.unpause()
            elif self._cont.status == "exited":
                self._cont.start()
            elif self._cont.status == "restarting":
                pass
            else:
                raise error.Error(f"Error starting container: {container.id}")

            time.sleep(1)

            if int(time.time() - start) > self._conversion_params.timeout:
                raise TimeoutError(
                    "Docker container startup timed out. "
                    "Please refer to our documentation "
                    "https://developers.datature.io/docs/tensorrt-export for more details, "
                    "or contact our engineers at support@datature.io for assistance."
                )
        trt_logger.info("Docker container running")

    def _get_commands(
        self,
        model_path: str,
        output_path: str = "",
    ) -> List[str]:
        """
        Constructs a command string for running a model conversion script.

        Args:
            precision (str): The quantization precision, either "FP32" or "INT8".
            model_path (str): The path to the saved model directory.
            output_path (str): The path to the output directory.

        Returns:
            List[str]: A list of command strings for running the model conversion script.

        Raises:
            ValueError: If the precision is "INT8", as it is currently not yet supported.
            ValueError: If the mode is not "FP32" or "FP16".
            ValueError: If the model path is not a valid ONNX model.
        """
        if self._conversion_params.precision == "INT8":
            raise ValueError(
                "INT8 quantization is currently not yet supported."
                "Please contact our engineers at support@datature.io "
                "if you require a custom conversion."
            )

        if self._conversion_params.precision not in ["FP32", "FP16"]:
            raise ValueError(
                "Invalid mode. Must be either 'FP32' or 'FP16'."
                "INT8 quantization is currently not yet supported."
                "Please contact our engineers at support@datature.io "
                "if you require a custom conversion."
            )

        if not os.path.exists(model_path) or not model_path.endswith(".onnx"):
            raise ValueError(
                "Invalid model path."
                "Please ensure that you provide the correct path to your ONNX model."
                "Refer to our documentation for supported model files: "
                "https://developers.datature.io/docs/tensorrt-export"
            )

        os.makedirs(self._conversion_params.log_dir, exist_ok=True)
        log_file = os.path.join(
            self._conversion_params.log_dir, f"{int(time.time())}.log"
        )
        trt_logger.info("Verbose logs will be saved at: %s", log_file)

        commands = ["sh", "-c", "pip3 install -qqq colored"]

        check_commands = ""
        sanitize_commands = ""
        conversion_experimental_commands = ""

        if self._conversion_params.experimental:
            (
                check_commands,
                sanitize_commands,
                conversion_experimental_commands,
            ) = self._get_experimental_commands(
                model_path,
                check_commands,
                sanitize_commands,
                conversion_experimental_commands,
            )

        precision_flag = "--fp16" if self._conversion_params.precision == "FP16" else ""
        convert_verbose_flag = (
            "--verbosity VERBOSE" if self._conversion_params.verbose else ""
        )
        conversion_commands = (
            f" && polygraphy convert {model_path}"
            f" --model-type onnx"
            f" -o {output_path}"
            f" --convert-to trt"
            f" {precision_flag}"
            f" --builder-optimization-level {self._conversion_params.builder_optimization_level}"
            f" --precision-constraints {self._conversion_params.precision_constraints}"
            f" {convert_verbose_flag}"
            f" --log-file {log_file}"
        )
        commands[-1] += check_commands
        commands[-1] += sanitize_commands
        commands[-1] += conversion_commands
        commands[-1] += conversion_experimental_commands
        return commands

    def _get_experimental_commands(
        self,
        model_path: str,
        check_commands: str,
        sanitize_commands: str,
        conversion_experimental_commands: str,
    ) -> Tuple[str, str, str]:
        """
        Constructs a command string for running experimental conversion settings.

        Args:
            check_commands (str): The command string for running `polygraphy check lint`.
            sanitize_commands (str): The command string for running `polygraphy surgeon sanitize`.
            conversion_experimental_commands (str):
                The command string for adding experimental conversion settings.

        Returns:
            Tuple[str, str, str]: A tuple of command strings for running the
                experimental conversion settings.
        """
        experimental_params = self._conversion_params.experimental
        check_params = experimental_params.check_params
        sanitize_params = experimental_params.sanitize_params
        if check_params.enabled:
            trt_logger.warning(
                "[EXPERIMENTAL] `polygraphy check lint` has been enabled."
                " This is an experimental setting and conversion may fail."
                " This check will be run before TensorRT conversion to"
                " topologically lint ONNX model to find faulty nodes in the graph."
            )
            output_json_path_flag = (
                f"--output_json_path {check_params.output_json_path}"
            )
            provider = f"--provider {check_params.provider}"
            check_verbosity_flag = "--verbosity VERBOSE" if check_params.verbose else ""
            check_commands = (
                f" && polygraphy check lint {model_path}"
                f" {output_json_path_flag}"
                f" {provider}"
                f" {check_verbosity_flag}"
            )

        if sanitize_params.enabled:
            trt_logger.warning(
                "[EXPERIMENTAL] `polygraphy surgeon sanitize` has been enabled."
                " This is an experimental setting and conversion may fail."
                " ONNX graph surgeon will be run before TensorRT conversion to"
                " clean up and optimize input shapes in an ONNX model."
            )
            root_dir, file_name = os.path.split(model_path)
            output_path = (
                sanitize_params.output_model_path
                if sanitize_params.output_model_path
                else os.path.join(root_dir, f"sanitized_{file_name}")
            )
            cleanup_flag = "--cleanup" if sanitize_params.cleanup else ""
            toposort_flag = "--toposort" if sanitize_params.toposort else ""
            no_shape_inference_flag = (
                "--no-shape-inference" if sanitize_params.no_shape_inference else ""
            )
            force_fallback_shape_inference_flag = (
                "--force-fallback-shape-inference"
                if sanitize_params.force_fallback_shape_inference
                else ""
            )
            fold_constants_flag = (
                "--fold-constants" if sanitize_params.fold_constants else ""
            )
            partitioning_flag = (
                f"--partitioning {sanitize_params.partitioning}"
                if sanitize_params.partitioning
                else ""
            )
            no_fold_shapes_flag = (
                "--no-fold-shapes" if sanitize_params.no_fold_shapes else ""
            )
            no_per_pass_shape_inference_flag = (
                "--no-per-pass-shape-inference"
                if sanitize_params.no_per_pass_shape_inference
                else ""
            )
            sanitize_commands = (
                f" && polygraphy surgeon sanitize {model_path}"
                f" --output {output_path}"
                f" {cleanup_flag}"
                f" {toposort_flag}"
                f" {no_shape_inference_flag}"
                f" {force_fallback_shape_inference_flag}"
                f" {fold_constants_flag}"
                f" {partitioning_flag}"
                f" {no_fold_shapes_flag}"
                f" {no_per_pass_shape_inference_flag}"
            )
            model_path = output_path

        docs_reference = (
            "Please refer to"
            " https://docs.nvidia.com/deeplearning/tensorrt/polygraphy/docs/backend/trt/config.html"
            " for more information."
        )
        sparse_weights_flag = ""
        version_compatible_flag = ""
        error_on_timing_cache_miss_flag = ""
        load_timing_cache_flag = ""
        save_timing_cache_flag = ""
        disable_compilation_cache_flag = ""
        load_tactics_flag = ""
        save_tactics_flag = ""

        if experimental_params.sparse_weights:
            sparse_weights_flag = "--sparse-weights"
            trt_logger.warning(
                "[EXPERIMENTAL] `%s` has been enabled."
                " This is an experimental setting and conversion may fail."
                " This will enable optimizations for sparse weights in TensorRT. %s",
                sparse_weights_flag,
                docs_reference,
            )

        if experimental_params.version_compatible:
            version_compatible_flag = "--version-compatible"
            trt_logger.warning(
                "[EXPERIMENTAL] `%s` has been enabled."
                " This is an experimental setting and conversion may fail."
                " This will build an engine designed to be"
                " forward TensorRT version compatible. %s",
                version_compatible_flag,
                docs_reference,
            )

        if experimental_params.error_on_timing_cache_miss:
            error_on_timing_cache_miss_flag = "--error-on-timing-cache-miss"
            trt_logger.warning(
                "[EXPERIMENTAL] `%s` has been enabled."
                " This is an experimental setting and conversion may fail."
                " The conversion process will emit errors when a tactic being timed"
                " is not present in the timing cache. %s",
                error_on_timing_cache_miss_flag,
                docs_reference,
            )

        if experimental_params.load_timing_cache:
            load_timing_cache_flag = (
                f"--load-timing-cache {experimental_params.load_timing_cache}"
            )
            trt_logger.warning(
                "[EXPERIMENTAL] `%s` has been enabled."
                " This is an experimental setting and conversion may fail."
                " This will load the specified tactic timing cache [%s]"
                " used to speed up the TensorRT engine building process. %s",
                load_timing_cache_flag,
                experimental_params.load_timing_cache,
                docs_reference,
            )

        if experimental_params.save_timing_cache:
            save_timing_cache_flag = (
                f"--save-timing-cache {experimental_params.save_timing_cache}"
            )
            trt_logger.warning(
                "[EXPERIMENTAL] `%s` has been enabled."
                " This is an experimental setting and conversion may fail."
                " This will enable saving of tactic timing cache to file [%s]. %s",
                save_timing_cache_flag,
                experimental_params.save_timing_cache,
                docs_reference,
            )

        if experimental_params.disable_compilation_cache:
            disable_compilation_cache_flag = "--disable-compilation-cache"
            trt_logger.warning(
                "[EXPERIMENTAL] `%s` has been enabled."
                " This is an experimental setting and conversion may fail."
                " This will disable caching of JIT-compiled code. %s",
                disable_compilation_cache_flag,
                docs_reference,
            )

        if experimental_params.load_tactics:
            load_tactics_flag = f"--load-tactics {experimental_params.load_tactics}"
            trt_logger.warning(
                "[EXPERIMENTAL] `%s` has been enabled."
                " This is an experimental setting and conversion may fail."
                " This will load specified tactic replay file [%s], which will"
                " override tactics in TensorRT's default selections. %s",
                load_tactics_flag,
                experimental_params.load_tactics,
                docs_reference,
            )

        if experimental_params.save_tactics:
            save_tactics_flag = f"--save-tactics {experimental_params.save_tactics}"
            trt_logger.warning(
                "[EXPERIMENTAL] `%s` has been enabled."
                " This is an experimental setting and conversion may fail."
                " This will save tactics selected by TensorRT to a"
                " specified JSON file [%s]. %s",
                save_tactics_flag,
                experimental_params.save_tactics,
                docs_reference,
            )

        conversion_experimental_commands = (
            f" {sparse_weights_flag}"
            f" {version_compatible_flag}"
            f" {error_on_timing_cache_miss_flag}"
            f" {load_timing_cache_flag}"
            f" {save_timing_cache_flag}"
            f" {disable_compilation_cache_flag}"
            f" {load_tactics_flag}"
            f" {save_tactics_flag}"
        )
        return check_commands, sanitize_commands, conversion_experimental_commands

    def _get_gpu_info(self) -> Dict[str, str]:
        """
        Returns the GPU information of the system.

        Returns:
            dict: A dictionary containing the GPU name, driver version, and CUDA version.
        """
        try:
            pynvml.nvmlInit()
            driver_version = pynvml.nvmlSystemGetDriverVersion()
            if isinstance(driver_version, bytes):
                driver_version = driver_version.decode("utf-8")
            cuda_version = pynvml.nvmlSystemGetCudaDriverVersion()

            device_count = pynvml.nvmlDeviceGetCount()
            if device_count == 0:
                raise error.Error("No NVIDIA GPU found")
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            gpu_name = str(pynvml.nvmlDeviceGetName(handle))
            pynvml.nvmlShutdown()

            return {
                "gpu_name": gpu_name,
                "driver_version": driver_version,
                "cuda_version": cuda_version,
            }
        except subprocess.CalledProcessError as exc:
            raise error.Error(f"Error running nvidia-settings: {exc.stderr}") from exc
        except pynvml.NVMLError as exc:
            raise error.NotFoundError(
                f"{exc}\nError: TensorRT conversion requires pre-installed NVIDIA drivers.\n"
                "If the necessary NVIDIA drivers are already installed, you might lack sufficient permissions to access them.\n"
            ) from exc
        except error.Error as exc:
            raise exc from exc

    def _cleanup(self):
        """Stops Docker container and removes temporary ONNX exported models."""
        trt_logger.info("Cleaning up TensorRT conversion resources...")
        if self._cont.status != "exited":
            self._cont.stop()
            self._docker_client.containers.prune()

        if os.path.exists(self._model_directory):
            shutil.rmtree(self._model_directory)

    def _print_logs(self):
        """Prints logs from TensorRT conversion"""
        for chunk in self._logs:
            for line in chunk.decode().split("\n"):
                if "[V]" in line:
                    trt_logger.debug(line)
                elif "[W]" in line:
                    trt_logger.warning(line)
                elif "[E]" in line:
                    trt_logger.error(line)
                else:
                    trt_logger.info(line)

    def get_status(self) -> Optional[int]:
        """
        Get exit status of TensorRT conversion to check if the process was successful.

        Returns:
            int:
                None if the process is still running,
                0 if the process exited successfully,
                any other exit code means an error has occurred.
        """
        return self._api_client.exec_inspect(self._exec_id).get("ExitCode")
