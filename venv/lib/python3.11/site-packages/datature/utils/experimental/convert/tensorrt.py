#!/usr/env/bin python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   tensorrt.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   TensorRT main module.
"""

# pylint: disable=E1102,R0902,R0913,R0914,R1732,W0511

import subprocess
import time
from contextlib import contextmanager
from typing import Generator, Optional

import requests

try:
    import docker
except ImportError as import_exc:
    raise ModuleNotFoundError(
        "Docker not installed! "
        "Please visit https://developers.datature.io/docs/tensorrt-export "
        "to learn how to set up your environment."
    ) from import_exc

from alive_progress import alive_bar

from datature.nexus import config, error
from datature.nexus.api.project import Project

from .converter import Converter
from .logger import trt_logger
from .params import ConversionParams, DockerParams
from .predictor import (
    MaskPredictor,
    ObjectDetectionPredictor,
    SemanticPredictor,
    VideoClassificationPredictor,
    YOLOv8BoxPredictor,
    YOLOv8ClassificationPredictor,
    YOLOv8MaskPredictor,
    YOLOv8PosePredictor,
)


class TensorRTConverter:
    """The TensorRT class provides an interface to the TensorRT Converter and Predictor."""

    _predictor_classes = {
        "od": ObjectDetectionPredictor,
        "mask": MaskPredictor,
        "semantic": SemanticPredictor,
        "video-cls": VideoClassificationPredictor,
        "yolov8": YOLOv8BoxPredictor,
        "yolov8-seg": YOLOv8MaskPredictor,
        "yolov8-pose": YOLOv8PosePredictor,
        "yolov8-cls": YOLOv8ClassificationPredictor,
        "yolov9": YOLOv8BoxPredictor,
    }

    def __init__(self, docker_params: Optional[DockerParams] = DockerParams()):
        """
        Instantiates the TensorRT Converter.

        Args:
            docker_params (DockerParams):
                Docker parameters for conversion and inference.
        """
        self._docker_params = docker_params
        self._converter = None
        self._inference_server = None
        self._docker_client = docker.from_env()
        self._api_client = docker.APIClient()

    def convert(
        self,
        project: Optional[Project] = None,
        artifact_id: Optional[str] = "",
        model_path: Optional[str] = "",
        output_path: Optional[str] = "",
        conversion_params: ConversionParams = ConversionParams(),
    ) -> None:
        """
        Instantiates the TensorRT Converter and runs the conversion process.

        Args:
            project (Project): The Nexus project instance containing the model to be converted.
            artifact_id (str): The artifact ID of the model to be converted.
            model_path (str): The path to the saved model directory.
            output_path (str): The path to the output directory.
            conversion_params (ConversionParams): Dictionary of conversion parameters.

        Raises:
            ValueError: If neither a local path to an ONNX model nor a Project instance is provided.
        """
        try:
            if not model_path and not project:
                raise ValueError(
                    "Either a local path to an ONNX model or a Project instance "
                    "needs to be provided if you wish to export an ONNX model "
                    "from your project on Datature Nexus"
                )
            trt_logger.info(
                "TensorRT conversion process may take up to 30 minutes, please be patient..."
            )
            with alive_bar(
                4 if project else 2,
                title="Running TensorRT Conversion",
                title_length=30,
                stats=False,
            ) as progress_bar:
                progress_bar.text("Setting up environment and resources")
                self._converter = Converter(
                    docker_client=self._docker_client,
                    api_client=self._api_client,
                    docker_params=self._docker_params,
                    conversion_params=conversion_params,
                )
                self._converter.setup()
                progress_bar()

                if project:
                    progress_bar.text("Exporting TensorRT-compatible ONNX model")
                    model_id = self._converter.create_export(
                        project=project, artifact_id=artifact_id
                    )
                    progress_bar.text(
                        "TensorRT-compatible ONNX model model successfully exported!"
                    )
                    progress_bar()
                    progress_bar.text("Downloading exported model")
                    model_path = self._converter.download_export(
                        project=project, model_id=model_id
                    )
                    progress_bar.text(
                        "TensorRT-compatible ONNX model model successfully downloaded!"
                    )
                    progress_bar()

                progress_bar.text("Converting to TensorRT")
                self._converter.convert(
                    model_path=model_path,
                    output_path=output_path,
                )
                progress_bar()
        except Exception as exc:  # pylint: disable=W0703
            trt_logger.error(exc)

    @contextmanager
    def inference_server(self, model_folder: str, timeout: int = 180) -> Generator:
        """
        Context manager to start and stop the NVIDIA Triton Inference Server Docker container.

        Args:
            model_folder (str): The path to the model folder containing the model files
                to be loaded into the inference server.
            timeout (int):
                The maximum time in seconds to wait for the inference server to be ready,
                defaults to 180.

        Raises:
            Error: If the inference server fails to start.
        """
        try:
            self._start_inference_server(model_folder, timeout)
            yield
        finally:
            self._stop_inference_server()

    def predict(
        self,
        task: str,
        input_path: str,
        model_name: str,
        label_map_path: str,
        skeleton_file_path: str = "",
        threshold: float = 0.7,
        save: bool = True,
        output_path: str = "",
        dtype: str = "float32",
    ) -> None:
        """
        Instantiates the TensorRT Predictor and runs the prediction process.

        Args:
            task (str):
                The task to be performed, either "od", "mask", "semantic", "yolov8",
                "yolov8-seg", "yolov8-pose", "yolov8-cls", or "yolov9".
            input_path (str): The path to the input image or video file.
            model_name (str): The name of the model to be used for prediction.
            label_map_path (str): The path to the label map file.
            skeleton_file_path (str): The path to the skeleton file for pose estimation.
            threshold (float): The confidence threshold for object detection, defaults to 0.7.
            save (bool): Whether to save the output, defaults to True.
            output_path (str): The path to the output directory, defaults to "".
            dtype (str):
                The data type of the model, either "float32" or "float16", defaults to "float32".
        """
        kwargs = {}
        if task == "yolov8-pose" and skeleton_file_path != "":
            kwargs["skeleton_file_path"] = skeleton_file_path

        try:
            predictor = self._predictor_classes.get(task)(
                dtype=dtype,
                input_path=input_path,
                model_name=model_name,
                label_map_path=label_map_path,
                threshold=threshold,
                save=save,
                output_path=output_path,
                **kwargs,
            )
        except TypeError as type_exc:
            trt_logger.error(type_exc, exc_info=True)
            trt_logger.error(
                "Prediction task not supported, valid tasks are one of "
                "['od', 'mask', 'semantic', 'yolov8', 'yolov8-seg', "
                "'yolov8-pose', 'yolov8-cls', 'yolov9']. "
                "Please refer to https://developers.datature.io/docs/tensorrt-export "
                "for more information on how to define the inference commands."
            )
            return

        try:
            predictor()
        except KeyboardInterrupt:
            trt_logger.info("Keyboard interrupt detected")
        except Exception as exc:  # pylint: disable=W0703
            trt_logger.error(exc, exc_info=True)

    def get_status(self):
        """Retrieve TensorRT conversion status."""
        self._converter.get_status()

    def _start_inference_server(self, model_folder: str, timeout: int = 180) -> None:
        """
        Starts the NVIDIA Triton Inference Server Docker container.

        Args:
            model_folder (str): The path to the model folder containing the model files
                to be loaded into the inference server.
            timeout (int):
                The maximum time in seconds to wait for the inference server to be ready,
                defaults to 180.

        Raises:
            Error: If the inference server fails to start.
        """
        try:
            candidate = self._docker_client.images.list(
                filters={"reference": self._docker_params.inference_docker_image}
            )

            if len(candidate) == 0:
                trt_logger.info(
                    "Pulling Docker image %s",
                    self._docker_params.inference_docker_image,
                )
                self._docker_client.images.pull(
                    self._docker_params.inference_docker_image
                )
        except docker.errors.DockerException as docker_exc:
            raise ConnectionError(
                f"Could not not pull Docker image {self._docker_params.inference_docker_image}"
            ) from docker_exc

        command = [
            "docker",
            "run",
            "--gpus",
            "all",
            "--rm",
            "-p",
            "8000:8000",
            "-p",
            "8001:8001",
            "-p",
            "8002:8002",
            "-v",
            f"{model_folder}:/models",
            self._docker_params.inference_docker_image,
            "tritonserver",
            "--model-repository=/models",
        ]

        trt_logger.info("Starting inference server...")
        try:
            self._inference_server = subprocess.Popen(
                command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        except subprocess.CalledProcessError as sp_exc:
            raise ConnectionError(sp_exc) from sp_exc

        time.sleep(5)
        start = time.time()
        while int(time.time() - start) < timeout:
            try:
                response = requests.get(
                    "http://localhost:8000/v2/health/ready",
                    timeout=config.REQUEST_TIME_OUT_SECONDS,
                )

                if response.status_code == 200:
                    trt_logger.info("Inference server ready!")
                    return

                raise error.InternalServerError(
                    "Something went wrong with starting the Triton Inference Server, "
                    "please visit https://developers.datature.io/docs/tensorrt-export "
                    "for more information on how to set up the inference server."
                )
            except requests.exceptions.ConnectionError as conn_exc:
                trt_logger.error(conn_exc)
                trt_logger.warning(
                    "Trying to establish connection to inference server..."
                )
                time.sleep(10)

        raise ConnectionRefusedError(
            "Could not connect to the Triton Inference Server, "
            "please visit https://developers.datature.io/docs/tensorrt-export "
            "for more information on how to set up the inference server."
        )

    def _stop_inference_server(self) -> None:
        """Stops the NVIDIA Triton Inference Server Docker container."""
        if self._inference_server is None:
            trt_logger.warning(
                "Inference server is not either not running or could not be found."
            )
            trt_logger.warning(
                "Please run `docker ps -a` to check if the inference server is already running."
            )
            return

        if self._inference_server.poll() is None:
            trt_logger.info("Stopping inference server...")
            self._inference_server.terminate()
