#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   upload_session.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Datature Asset Upload Session
"""
# pylint: disable=C0302,R1702,R1732,R0902,R0912,R0913,R0914,R0915,R0917,E0203,W0201,W0718

import concurrent.futures
import logging
import os
import random
import signal
import struct
import tempfile
import threading
import time
from collections import deque
from contextlib import ContextDecorator
from pathlib import Path
from typing import List, Optional, Tuple, Union

import crc32c
import cv2
from filetype import filetype
from tqdm.auto import tqdm

from datature.nexus import config, error
from datature.nexus.api.asset.multipart import MultipartHandler
from datature.nexus.api.operation import Operation
from datature.nexus.api.types import AssetFilePart, OperationStatusOverview
from datature.nexus.client_context import ClientContext, RestContext
from datature.nexus.models import (
    CancelResponse,
    MultipartAbortResponse,
    MultipartCompleteResponse,
    MultipartPartStatus,
)
from datature.nexus.models import MultipartUploadSession as MultipartUploadSessionModel
from datature.nexus.models import MultipartUploadSignedUrl
from datature.nexus.models import UploadSession as UploadSessionModel
from datature.nexus.models import UploadSessionAssetItem
from datature.nexus.utils import file_signature, utils

logger = logging.getLogger("datature-nexus")


class TokenBucketRateLimiter:
    """Thread-safe token bucket rate limiter for API requests.

    Implements a sliding window rate limiter that tracks request timestamps
    and ensures no more than max_requests occur within any window_seconds period.
    """

    def __init__(self, max_requests: int, window_seconds: float):
        """Initialize rate limiter.

        :param max_requests: Maximum number of requests allowed in the time window
        :param window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.request_times = deque()  # Stores timestamps of recent requests
        self.lock = threading.Lock()

    def acquire(self, timeout: Optional[float] = None) -> bool:
        """Acquire permission to make a request, blocking if necessary.

        :param timeout: Maximum time to wait in seconds (None = wait forever)
        :return: True if permission granted, False if timeout
        """
        start_time = time.time()

        while True:
            with self.lock:
                current_time = time.time()

                # Remove requests outside the current window
                while (
                    self.request_times
                    and current_time - self.request_times[0] >= self.window_seconds
                ):
                    self.request_times.popleft()

                # Check if we can proceed
                if len(self.request_times) < self.max_requests:
                    self.request_times.append(current_time)
                    return True

                # Calculate wait time until oldest request expires
                if self.request_times:
                    oldest_request_time = self.request_times[0]
                    wait_until = oldest_request_time + self.window_seconds
                    wait_time = wait_until - current_time
                else:
                    wait_time = 0.1

            # Check timeout
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    return False
                wait_time = min(wait_time, timeout - elapsed)

            # Sleep before retry
            if wait_time > 0:
                time.sleep(min(wait_time, 1.0))  # Cap at 1 second per iteration

    def get_current_usage(self) -> Tuple[int, int]:
        """Get current rate limit usage.

        :return: Tuple of (current_requests, max_requests)
        """
        with self.lock:
            current_time = time.time()
            # Remove expired requests
            while (
                self.request_times
                and current_time - self.request_times[0] >= self.window_seconds
            ):
                self.request_times.popleft()
            return (len(self.request_times), self.max_requests)


class UploadProgressTracker:
    """Thread-safe progress tracker for asset uploads with tqdm integration.

    Tracks upload progress across multiple parallel upload threads with
    synchronized updates and tqdm progress bar display (works in Jupyter and terminal).
    """

    def __init__(self, total_assets: int, show_progress: bool = True):
        """Initialize the progress tracker.

        :param total_assets: Total number of assets to upload
        :param show_progress: Whether to show tqdm progress bar
        """
        self.total_assets = total_assets
        self.completed_count = 0
        self.success_count = 0
        self.failed_count = 0
        self.show_progress = show_progress
        self._lock = threading.Lock()
        self._pbar = None

    def start(self):
        """Start the progress bar if enabled."""
        if self.show_progress and self.total_assets > 0:
            try:
                # tqdm.auto automatically detects environment (Jupyter vs terminal)
                # position=0 ensures it's displayed at the top
                # leave=True keeps the bar after completion
                self._pbar = tqdm(
                    total=self.total_assets,
                    desc="Uploading assets",
                    unit="file",
                    position=0,
                    leave=True,
                    dynamic_ncols=True,
                )
                logger.debug(f"Progress bar initialized for {self.total_assets} assets")
            except Exception as exc:
                logger.warning("Failed to initialize progress bar: %s", exc)
                self.show_progress = False

    def stop(self):
        """Stop and close the progress bar."""
        if self._pbar is not None:
            try:
                self._pbar.close()
            except Exception as exc:
                logger.warning("Error closing progress bar: %s", exc)
            finally:
                self._pbar = None

    def update_success(self, files_completed: int = 1):
        """Update progress for successful uploads.

        :param files_completed: Number of files successfully uploaded
        """
        with self._lock:
            self.completed_count += files_completed
            self.success_count += files_completed
            self._update_bar(files_completed)

    def update_failure(self, files_failed: int = 1):
        """Update progress for failed uploads.

        :param files_failed: Number of files that failed to upload
        """
        with self._lock:
            self.completed_count += files_failed
            self.failed_count += files_failed
            self._update_bar(files_failed)

    def _update_bar(self, n: int = 1):
        """Update the progress bar display.

        :param n: Number of items to increment
        """
        if self._pbar is not None:
            try:
                # Update postfix with current stats
                self._pbar.set_postfix(
                    {"✓": self.success_count, "✗": self.failed_count}, refresh=True
                )
                # Increment the bar
                self._pbar.update(n)
            except Exception as exc:
                logger.debug("Error updating progress bar: %s", exc)
        else:
            logger.debug(
                f"Progress bar not initialized yet (completed: {self.completed_count})"
            )

    def update_total(self, new_total: int):
        """Update the total number of assets and recalculate bar display.

        :param new_total: New total number of assets
        """
        with self._lock:
            old_total = self.total_assets
            if new_total != old_total:
                self.total_assets = new_total
                if self._pbar is not None:
                    # Update total
                    self._pbar.total = new_total

                    # For Jupyter widgets, directly update the widget's max value
                    # Check if this is a notebook widget (has 'container' attribute)
                    if hasattr(self._pbar, "container"):
                        # Access the progress bar widget and update its max
                        try:
                            # The widget is in container.children[1] (the actual progress bar)
                            if (
                                hasattr(self._pbar.container, "children")
                                and len(self._pbar.container.children) > 1
                            ):
                                progress_widget = self._pbar.container.children[1]
                                if hasattr(progress_widget, "max"):
                                    old_widget_max = progress_widget.max
                                    progress_widget.max = new_total
                                    logger.debug(
                                        f"Updated Jupyter widget max: {old_widget_max} -> {new_total}"
                                    )
                        except Exception as exc:
                            logger.debug(f"Could not update Jupyter widget max: {exc}")

                    # Update postfix stats
                    self._pbar.set_postfix(
                        {"✓": self.success_count, "✗": self.failed_count},
                        refresh=False,
                    )
                    # Force tqdm to recalculate bar by calling update(0)
                    # This triggers internal recalculation without changing n
                    self._pbar.update(0)
                logger.debug(
                    f"Progress tracker total updated: {old_total} -> {new_total}"
                )

    def get_stats(self) -> Tuple[int, int, int, int]:
        """Get current progress statistics.

        :return: Tuple of (completed, total, success_count, failed_count)
        """
        with self._lock:
            return (
                self.completed_count,
                self.total_assets,
                self.success_count,
                self.failed_count,
            )


class UploadSession(RestContext, ContextDecorator):
    """Datature Asset Upload Session Class.

    :param client_context: An instance of ClientContext.
    :param groups: A list of group names to categorize the upload. Default is None.
    :param background:
        A flag indicating whether the upload should run in the background. Default is False.
    :param show_progress: Whether to display a progress bar during upload.
        Default is True. Set to False when CLI implements its own progress tracking.
        Uses tqdm which works in both terminal and Jupyter notebook environments.
    """

    _batched_upload_warning_flag: bool = False

    def __init__(
        self,
        client_context: ClientContext,
        groups: Optional[List[str]] = None,
        background: bool = False,
        show_progress: bool = True,
    ):
        """Initialize the API Resource.

        :param show_progress: Whether to display progress bar during upload (uses tqdm).
            Default is True. Set to False when CLI implements its own progress tracking.
            tqdm automatically adapts to terminal or Jupyter notebook environments.
        """
        super().__init__(client_context)
        self._local = threading.local()

        self._operation = None  # Lazy initialization if needed
        self.assets = []
        self.file_name_map = {}
        self.upload_session_ids = []
        self.operation_ids = []

        self.groups = groups if groups is not None else ["main"]
        self.background = background
        self.show_progress = show_progress

        self.abort_event = threading.Event()

        # Track if cleanup warnings have been shown to avoid duplication
        self._cleanup_warnings_shown = False

        # Global progress tracker for all batches (initialized later when total is known)
        self.global_progress_tracker: Optional[UploadProgressTracker] = None

        # Thread pool for parallel batch uploads
        cpu_count = int(os.cpu_count() or 1)

        # Calculate batch workers based on config
        if config.ASSET_UPLOAD_SESSION_MAX_PARALLEL_BATCHES > 0:
            batch_workers = min(
                max(int(cpu_count * config.ASSET_UPLOAD_SESSION_WORKERS_RATIO), 1),
                config.ASSET_UPLOAD_SESSION_MAX_PARALLEL_BATCHES,
            )
        else:
            # Unlimited - use CPU-based calculation
            batch_workers = max(
                int(cpu_count * config.ASSET_UPLOAD_SESSION_WORKERS_RATIO), 1
            )

        logger.debug(
            f"Initializing upload session with {batch_workers} parallel batch workers"
        )

        self.batch_upload_executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=batch_workers
        )
        self.batch_upload_futures = []
        self.assets_lock = threading.Lock()

        # Track in-flight POST requests to defer interrupt handling
        self.inflight_posts_lock = threading.Lock()
        self.inflight_posts_count = 0
        self.inflight_posts_condition = threading.Condition(self.inflight_posts_lock)

        # Rate limiter for session creation to respect server limits
        self.session_creation_rate_limiter = TokenBucketRateLimiter(
            max_requests=config.ASSET_UPLOAD_SESSION_RATE_LIMIT_MAX_REQUESTS,
            window_seconds=config.ASSET_UPLOAD_SESSION_RATE_LIMIT_WINDOW_SECONDS,
        )
        logger.debug(
            f"Rate limiter initialized: {config.ASSET_UPLOAD_SESSION_RATE_LIMIT_MAX_REQUESTS} "
            f"sessions per {config.ASSET_UPLOAD_SESSION_RATE_LIMIT_WINDOW_SECONDS}s "
            f"({config.ASSET_UPLOAD_SESSION_RATE_LIMIT_WINDOW_SECONDS / config.ASSET_UPLOAD_SESSION_RATE_LIMIT_MAX_REQUESTS:.1f}s avg interval)"
        )

        # Shared thread pool for file uploads across all batches
        # Increased parallelism for faster GCS uploads
        upload_workers = max(
            int(cpu_count * config.ASSET_UPLOAD_PER_BATCH_WORKERS_RATIO), 1
        )
        logger.debug(
            f"Initializing file upload executor with {upload_workers} parallel workers"
        )

        self.shared_upload_executor = concurrent.futures.ThreadPoolExecutor(
            initializer=self._init_http_session, max_workers=upload_workers
        )

    @property
    def operation(self):
        """Initialize operation."""
        if self._operation is None:
            self._operation = Operation(self._context)
        return self._operation

    def _init_http_session(self, abort_events: Optional[List[threading.Event]] = None):
        """Initialize local session and retry policy."""
        if abort_events is None:
            abort_events = []

        self._local.abort_event = threading.Event()
        abort_events.append(self._local.abort_event)

        self._local.http_session = utils.init_gcs_upload_session(abort_events)

    def __enter__(self):
        return self

    def _cleanup_on_interrupt(
        self, max_wait_time: int = 120, cancel_all_futures: bool = True
    ):
        """Perform cleanup when interrupted.

        :param max_wait_time: Maximum time to wait for in-flight POSTs
        :param cancel_all_futures: Whether to cancel all futures or just pending ones
        """
        # Cancel pending (not yet started) futures
        cancelled_count = 0
        for future in self.batch_upload_futures:
            if cancel_all_futures:
                # Cancel all futures
                if not future.done() and future.cancel():
                    cancelled_count += 1
            else:
                # Cancel only pending (not running) futures
                if not future.running() and not future.done() and future.cancel():
                    cancelled_count += 1

        # Wait for any in-flight POST requests to complete so we get session IDs
        wait_start = time.time()

        if self.inflight_posts_count > 0:
            with self.inflight_posts_condition:
                while self.inflight_posts_count > 0:
                    elapsed = time.time() - wait_start
                    remaining = max_wait_time - elapsed

                    if remaining <= 0:
                        break

                    self.inflight_posts_condition.wait(timeout=min(5, remaining))

            self.inflight_posts_count = min(self.inflight_posts_count, 0)

        # Set abort event after waiting for POSTs
        self.abort_event.set()

        # Cancel sessions (progress bar is stopped by caller)
        self._cancel_upload_session()

    def __exit__(self, _exc_type, exc_val, _exc_tb):
        """Exit function.
        The function will be called if an exception is raised inside the context manager
        """
        # Handle exceptions that occurred during the 'with' block
        if exc_val is not None:
            # Stop progress bar FIRST so warnings are visible
            if self.global_progress_tracker is not None:
                self.global_progress_tracker.stop()

            if isinstance(exc_val, KeyboardInterrupt):
                # Show warnings only if not already shown in batch handler
                if not self._cleanup_warnings_shown:
                    logger.warning(
                        "Upload interrupted by user, cleaning up upload sessions..."
                    )
                    logger.warning(
                        "This may take up to 2 minutes, please be patient..."
                    )
                    logger.warning(
                        "WARNING: If you force quit or restart the runtime, some upload sessions might not be "
                        "cleaned up properly and might linger in the system for up to 48 hours. "
                        "This might affect the ability to perform other tasks, such as importing annotations."
                    )
                    self._cleanup_warnings_shown = True
            else:
                logger.warning("Upload session error: %s", exc_val)

            # Perform cleanup using helper method (only cancel pending futures)
            self._cleanup_on_interrupt(max_wait_time=120, cancel_all_futures=False)

            # Shutdown executors
            self.batch_upload_executor.shutdown(wait=False)
            self.shared_upload_executor.shutdown(wait=False)
            return False

        try:
            # Check if we have assets to upload
            total_assets = len(self.file_name_map)
            if total_assets == 0:
                raise error.Error("Assets to upload is empty")

            # Initialize or update progress tracker with final total
            if self.global_progress_tracker is None:
                # No batches were submitted yet (small upload), initialize now
                self.global_progress_tracker = UploadProgressTracker(
                    total_assets=total_assets,
                    show_progress=self.show_progress,
                )
                self.global_progress_tracker.start()
                logger.debug(f"Progress tracker initialized with {total_assets} assets")
            else:
                # Update total to final count (in case more assets were added)
                self.global_progress_tracker.update_total(total_assets)

            # Submit any remaining assets as final batch BEFORE waiting
            # This allows final batch to run in parallel with other batches
            if self.assets:
                future = self.batch_upload_executor.submit(
                    self._upload_assets, self.assets[:]
                )
                self.batch_upload_futures.append(future)
                # Clear assets to prevent double submission
                self.assets = []

            # check asset length
            if len(self.batch_upload_futures) == 0:
                raise error.Error("Assets to upload is empty")

            # Wait for ALL batch upload futures to complete (including final batch)
            try:
                for future in concurrent.futures.as_completed(
                    self.batch_upload_futures
                ):
                    response = future.result()
                    self.operation_ids.append(response.op_id)
            except KeyboardInterrupt:
                # Show warnings only if not already shown
                if not self._cleanup_warnings_shown:
                    logger.warning(
                        "Upload interrupted by user during batch processing, cleaning up upload sessions..."
                    )
                    logger.warning(
                        "This may take up to 2 minutes, please be patient..."
                    )
                    logger.warning(
                        "WARNING: If you force quit or restart the runtime, some upload sessions might not be "
                        "cleaned up properly and might linger in the system for up to 48 hours. "
                        "This might affect the ability to perform other tasks, such as importing annotations."
                    )
                    self._cleanup_warnings_shown = True

                # Set abort flag and cancel in-flight sessions immediately
                # This prevents orphaned sessions from lingering
                self.abort_event.set()
                self._cancel_upload_session()
                # Re-raise so __exit__ can finish cleanup
                raise
            except Exception as exc:
                logger.error("Error in batch upload: %s", exc)
                self.abort_event.set()
                self._cancel_upload_session()
                raise

            # In background mode, uploads are complete but server processing continues
            # Keep progress bar visible briefly to show completion
            if self.background:
                if self.global_progress_tracker is not None:
                    logger.info(
                        f"File uploads complete: "
                        f"✓ {self.global_progress_tracker.success_count} "
                        f"✗ {self.global_progress_tracker.failed_count}"
                    )
                return {"op_ids": self.operation_ids}

            # Wait for server to finish generating thumbnail
            self.wait_until_done()

            return {"op_ids": self.operation_ids}

        finally:
            # Stop progress bar
            if self.global_progress_tracker is not None:
                self.global_progress_tracker.stop()

            self.batch_upload_executor.shutdown(wait=True)
            self.shared_upload_executor.shutdown(wait=True)

    def __len__(self):
        """Over write len function."""
        return len(self.file_name_map)

    def add_path(self, file_path: str):
        """
        Add asset to upload.

        :param file_path: The path of the file to upload.
        """
        absolute_file_path = Path(file_path).expanduser().resolve()
        if not absolute_file_path.exists():
            raise error.Error("Cannot find the Asset file")

        if absolute_file_path.is_dir():
            file_paths = utils.find_all_assets(absolute_file_path)
        else:
            file_paths = [str(absolute_file_path)]

        for each_file_path in file_paths:
            self._generate_metadata(os.path.basename(each_file_path), each_file_path)
            # check current asset size
            self._check_current_asset_size()

    def add_bytes(
        self,
        file_bytes: bytes,
        filename: str,
    ):
        """Attach file in bytes to upload session

        :param file_bytes: The bytes of the file to upload.
        :param filename: The name of the file to upload, should include the file extension.
        """
        file_mime_type = file_signature.get_file_mime_by_signature(file_bytes)

        if file_mime_type is None:
            raise TypeError(f"Unsupported file: {filename}")

        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()

        # Create a temporary file path
        temp_file_path = os.path.join(temp_dir, filename)

        # Write file bytes to the temporary file
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(file_bytes)

        self._generate_metadata(os.path.basename(temp_file_path), temp_file_path)
        # check current asset size
        self._check_current_asset_size()

    def _generate_metadata(self, filename: str, file_path: str):
        """process the file to asset metadata."""
        size = os.path.getsize(file_path)

        if size < config.ASSET_UPLOAD_SESSION_MULTIPART_MIN_SIZE:
            file_hash = crc32c.CRC32CHash()

            with open(file_path, "rb") as file:
                chunk = file.read(config.FILE_CHUNK_SIZE)
                while chunk:
                    file_hash.update(chunk)
                    chunk = file.read(config.FILE_CHUNK_SIZE)

            # To fix the wrong crc32 caused by mac M1 clip
            crc32 = struct.unpack(">l", file_hash.digest())[0]

        else:
            crc32 = 0

        guess_result = filetype.guess(file_path)
        mime = utils.ASSET_FILE_EXTENSION_TO_MIME_TYPE_MAP.get(
            utils.get_file_extension(file_path),
            guess_result.mime if guess_result else None,
        )

        if self.file_name_map.get(filename) is not None:
            raise error.Error(
                f"Cannot add multiple files with the same name, {filename}"
            )

        if filename and size and mime:
            if mime in utils.SUPPORTED_VIDEO_MIME_TYPES:
                if size > config.VIDEO_MAX_SIZE:
                    raise error.Error(
                        f"Video {filename} size exceeds the limit: "
                        f"{config.VIDEO_MAX_SIZE / 1024 / 1024 / 1024} GB"
                    )

                frames = 1
                try:
                    cap = cv2.VideoCapture(file_path)
                    if not cap.isOpened():
                        raise error.Error(f"Failed to open video file: {filename}")

                    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    if frames <= 0:
                        raise error.Error(f"Invalid frame count for video: {filename}")

                    cap.release()

                except Exception as exc:
                    logger.warning(
                        "Error reading video file %s: %s, "
                        "Video will still be attempted to be uploaded",
                        filename,
                        str(exc),
                    )

                asset_metadata = {
                    "filename": filename,
                    "size": size,
                    "crc32c": crc32,
                    "mime": mime,
                    "frames": frames,
                    "encoder": {"profile": "h264Saver", "everyNthFrame": 1},
                }

            elif mime in utils.SUPPORTED_IMAGE_MIME_TYPES:
                if size > config.IMAGE_MAX_SIZE:
                    raise error.Error(
                        f"Image {filename} size exceeds the limit: "
                        f"{config.IMAGE_MAX_SIZE / 1024 / 1024} MB"
                    )

                asset_metadata = {
                    "filename": filename,
                    "size": size,
                    "crc32c": crc32,
                    "mime": mime,
                }

            elif mime in utils.SUPPORTED_MEDICAL_3D_MIME_TYPES:
                if size > config.MEDICAL_3D_MAX_SIZE:
                    raise error.Error(
                        f"Medical 3D {filename} size exceeds the limit: "
                        f"{config.MEDICAL_3D_MAX_SIZE / 1024 / 1024 / 1024} GB"
                    )

                asset_metadata = {
                    "filename": filename,
                    "size": size,
                    "crc32c": crc32,
                    "mime": mime,
                }

            else:
                raise error.Error(
                    f"Asset MIME type {mime} is not supported. "
                    "Supported MIME types: "
                    + ", ".join(utils.SUPPORTED_IMAGE_MIME_TYPES)
                    + ", "
                    + ", ".join(utils.SUPPORTED_VIDEO_MIME_TYPES)
                    + ", "
                    + ", ".join(utils.SUPPORTED_MEDICAL_3D_MIME_TYPES)
                )

            with self.assets_lock:
                self.assets.append(asset_metadata)
                self.file_name_map[filename] = {"path": file_path}

            logger.debug("Add asset: %s", asset_metadata)
        else:
            raise error.Error("Unsupported asset file")

    def _upload_file_through_signed_url(
        self, asset_upload, abort_event: threading.Event
    ) -> Tuple[str, bool]:
        """
        Upload a file through signed url with retry mechanism.

        :param asset_upload: The asset upload response containing metadata
        :param abort_event: Event to signal abort
        :return: A tuple of the filename and a boolean indicating if the upload was successful
        """
        filename = asset_upload.get("metadata").get("filename")
        file_path = self.file_name_map.get(filename)["path"]
        retry_count = 0

        # Check for abort before proceeding
        if abort_event.is_set():
            return filename, False

        while retry_count < config.ASSET_UPLOAD_MAX_RETRIES:
            try:
                # Check for abort before each retry attempt
                if abort_event.is_set():
                    return filename, False

                # upload asset to GCP
                with open(file_path, "rb") as file:
                    upload_response = self._local.http_session.request(
                        asset_upload.upload.method,
                        asset_upload.upload.url,
                        headers=asset_upload.upload.headers,
                        data=file,
                        timeout=config.REQUEST_TIME_OUT_SECONDS,
                    )

                if not upload_response.ok:
                    raise error.Error(
                        f"File upload failed: {upload_response.status_code} {upload_response.text}"
                    )

                logger.debug("Successfully uploaded file: %s", filename)
                return filename, True

            except Exception as exc:
                if abort_event.is_set():
                    return filename, False

                retry_count += 1
                if retry_count >= config.ASSET_UPLOAD_MAX_RETRIES:
                    logger.error(
                        "Failed to upload file %s after %d retries: %s",
                        filename,
                        config.ASSET_UPLOAD_MAX_RETRIES,
                        str(exc),
                    )
                    raise error.Error(
                        f"Failed to upload file {filename} after "
                        f"{config.ASSET_UPLOAD_MAX_RETRIES} retries: {str(exc)}"
                    )

                logger.warning(
                    "Error: %s, Retrying file upload for %s (attempt %d/%d)",
                    str(exc),
                    filename,
                    retry_count + 1,
                    config.ASSET_UPLOAD_MAX_RETRIES,
                )

                time.sleep(2**retry_count)

        # This should never be reached, but just in case
        return filename, False

    def _upload_part(
        self,
        multipart_handler: MultipartHandler,
        multipart_upload_session_response: MultipartUploadSessionModel,
        part: AssetFilePart,
        asset_upload: UploadSessionAssetItem,
        file_abort_event: threading.Event,
        abort_event: threading.Event,
    ):
        """
        Upload a single part of a large asset file.

        :param multipart_handler: The MultipartHandler instance managing the file parts.
        :param multipart_upload_session_response: The response from the multipart upload session.
        :param part: The part of the file to upload.
        :param asset_upload: The asset upload metadata.
        :param file_abort_event: Event to signal abort for this file's parts.
        :param abort_event: Global event to signal abort (e.g. from keyboard interrupt).
        :return: None
        """
        retry_count = 0

        while retry_count < config.ASSET_UPLOAD_MAX_RETRIES:
            try:
                # Check both abort events before proceeding
                if file_abort_event.is_set() or abort_event.is_set():
                    raise error.Error("Upload interrupted by user")

                part_url_response = self.requester.PUT(
                    f"/projects/{self.project_id}/multipartassetuploads/"
                    f"{multipart_upload_session_response.id}/parts/{part.part_number}",
                    response_type=MultipartUploadSignedUrl,
                )

                part_data = multipart_handler.read_part_data(part)

                # Upload part to GCS
                upload_response = self._local.http_session.request(
                    part_url_response.method,
                    part_url_response.url,
                    headers=part_url_response.headers,
                    data=part_data,
                    timeout=config.REQUEST_TIME_OUT_SECONDS,
                )

                if not upload_response.ok:
                    raise error.Error(
                        f"Part {part.part_number} upload failed: "
                        f"{upload_response.status_code} {upload_response.text}"
                    )

                upload_response_headers = {
                    k.lower(): v for k, v in upload_response.headers.items()
                }

                gcs_upload_response_data = {
                    "responseHeaders": {
                        header: upload_response_headers.get(header.lower(), "")
                        for header in part_url_response.response_headers
                    },
                }

                if part_url_response.response_body:
                    gcs_upload_response_data["responseBody"] = part_url_response.text

                part_status_response = self.requester.POST(
                    f"/projects/{self.project_id}/multipartassetuploads/"
                    f"{multipart_upload_session_response.id}/parts/"
                    f"{part.part_number}/complete",
                    request_body=gcs_upload_response_data,
                    response_type=MultipartPartStatus,
                )

                if not part_status_response.completed:
                    raise error.Error(
                        f"Part {part.part_number} upload completion "
                        f"not registered by server for {asset_upload.metadata.filename}"
                    )

                logger.debug(
                    "Uploaded part %d/%d for %s",
                    part.part_number,
                    multipart_upload_session_response.part_count,
                    asset_upload.metadata.filename,
                )

                return

            except Exception as exc:
                if file_abort_event.is_set() or abort_event.is_set():
                    raise

                retry_count += 1
                if retry_count >= config.ASSET_UPLOAD_MAX_RETRIES:
                    logger.error(
                        "Failed to upload part %d for %s after %d retries: %s",
                        part.part_number,
                        asset_upload.metadata.filename,
                        config.ASSET_UPLOAD_MAX_RETRIES,
                        str(exc),
                    )

                    raise error.Error(
                        f"Failed to upload part {part.part_number} for "
                        f"{asset_upload.metadata.filename} after "
                        f"{config.ASSET_UPLOAD_MAX_RETRIES} retries: {str(exc)}"
                    )

                logger.warning(
                    "Error: %s, Retrying part %d upload for %s (attempt %d/%d)",
                    str(exc),
                    part.part_number,
                    asset_upload.metadata.filename,
                    retry_count + 1,
                    config.ASSET_UPLOAD_MAX_RETRIES,
                )

                time.sleep(2**retry_count)

    def _upload_multipart_file_through_signed_url(
        self,
        multipart_executor: concurrent.futures.ThreadPoolExecutor,
        upload_session_id: str,
        asset_upload: UploadSessionAssetItem,
        abort_event: threading.Event,
    ) -> Tuple[str, bool]:
        """
        Upload a large file to GCS using multipart upload.

        :param multipart_executor: The thread pool executor for multipart uploads.
        :param upload_session_id: The upload session ID
        :param asset_upload: The asset upload response containing metadata
        :param abort_event: Global event to signal abort (e.g. from keyboard interrupt)
        :return: A tuple of the filename and a boolean indicating if the upload was successful
        """
        file_path = self.file_name_map.get(asset_upload.metadata.filename, {}).get(
            "path"
        )

        logger.debug(
            "Starting multipart upload for %s (%.2f MB)",
            asset_upload.metadata.filename,
            asset_upload.metadata.size / (1024 * 1024),
        )

        part_abort_event = threading.Event()

        if abort_event.is_set():
            raise error.Error("Upload interrupted by user")

        self._init_http_session([abort_event, part_abort_event])

        multipart_upload_session_response = self.requester.POST(
            f"/projects/{self.project_id}/assetuploadsessions/{upload_session_id}/multipart",
            request_body={
                "filename": asset_upload.metadata.filename,
                "mime": asset_upload.metadata.mime,
                "size": asset_upload.metadata.size,
            },
            response_type=MultipartUploadSessionModel,
        )

        try:
            multipart_handler = MultipartHandler(
                file_path, multipart_upload_session_response.part_count
            )

            logger.debug(
                "File %s split into %d parts",
                asset_upload.metadata.filename,
                multipart_upload_session_response.part_count,
            )

            futures = []
            for part in multipart_handler.parts:
                futures.append(
                    multipart_executor.submit(
                        self._upload_part,
                        multipart_handler,
                        multipart_upload_session_response,
                        part,
                        asset_upload,
                        part_abort_event,
                        abort_event,
                    )
                )

            done, _ = concurrent.futures.wait(
                futures, return_when=concurrent.futures.FIRST_EXCEPTION
            )

            for future in done:
                exc = future.exception()
                if exc is not None:
                    part_abort_event.set()
                    raise error.Error("Upload interrupted by user") from exc

            complete_response = self.requester.POST(
                f"/projects/{self.project_id}/multipartassetuploads/"
                f"{multipart_upload_session_response.id}/complete",
                response_type=MultipartCompleteResponse,
            )

            logger.debug(
                "Completed multipart upload for %s: %s",
                asset_upload.metadata.filename,
                complete_response,
            )

            return asset_upload.metadata.filename, True

        except Exception as exc:
            logger.debug(
                "Error: %s, Aborting multipart upload for %s",
                str(exc),
                asset_upload.metadata.filename,
            )

            self.requester.DELETE(
                f"/projects/{self.project_id}/multipartassetuploads/"
                f"{multipart_upload_session_response.id}",
                response_type=MultipartAbortResponse,
                ignore_errno=[404],
            )

            return asset_upload.metadata.filename, False

    def _upload_assets(self, assets_to_upload: List[dict]):
        """Use ThreadPoolExecutor to upload asset files to GCS.

        :param assets_to_upload: List of asset metadata dictionaries to upload
        """
        # Block SIGINT in worker threads - signals should only be handled by main thread
        # This prevents KeyboardInterrupt from interrupting the POST request
        try:
            signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT})
        except (AttributeError, ValueError):
            # pthread_sigmask not available on all platforms or not in worker thread
            pass

        # Check if abort was requested before starting POST
        if self.abort_event.is_set():
            raise KeyboardInterrupt()

        retry_count = 0
        max_retries = 5
        # Base wait time of 60 seconds gives the rate limit window time to clear
        base_wait_time = 60

        while retry_count < max_retries:
            try:
                # Acquire rate limit token before creating session
                # This blocks until we're allowed to proceed
                (
                    current_usage,
                    max_usage,
                ) = self.session_creation_rate_limiter.get_current_usage()
                if current_usage >= max_usage:
                    logger.debug(
                        f"Rate limit: {current_usage}/{max_usage} sessions used, waiting for available slot..."
                    )

                self.session_creation_rate_limiter.acquire()

                (
                    current_usage,
                    max_usage,
                ) = self.session_creation_rate_limiter.get_current_usage()
                logger.debug(
                    f"Rate limit token acquired: {current_usage}/{max_usage} sessions in window"
                )

                # Mark that we're starting a critical POST request
                with self.inflight_posts_condition:
                    self.inflight_posts_count += 1

                # Execute POST - KeyboardInterrupt should only be handled by main thread
                upload_session_response = self.requester.POST(
                    f"/projects/{self.project_id}/assetuploadsessions",
                    request_body={
                        "groups": self.groups,
                        "assets": assets_to_upload,
                    },
                    response_type=UploadSessionModel,
                )

                # Store session ID immediately after successful POST
                with self.assets_lock:
                    self.upload_session_ids.append(upload_session_response.id)

                # Mark that POST is complete and notify waiters
                # This MUST happen after session ID is stored to avoid race condition
                with self.inflight_posts_condition:
                    self.inflight_posts_count -= 1
                    self.inflight_posts_condition.notify_all()

                break
            except (
                error.TooManyRequestsError,
                error.InternalServerError,
                error.ServiceUnavailableError,
                error.GatewayTimeoutError,
            ) as exc:
                # Decrement counter since POST failed
                with self.inflight_posts_condition:
                    self.inflight_posts_count -= 1
                    self.inflight_posts_condition.notify_all()

                retry_count += 1
                if retry_count >= max_retries:
                    logger.debug(
                        "Server error after %d retries, failing batch upload: %s",
                        max_retries,
                        str(exc),
                    )
                    raise

                # Exponential backoff: 60, 120, 240 seconds (1min, 2min, 4min)
                wait_time = base_wait_time * (2 ** (retry_count - 1))

                # Add jitter: randomize wait time by ±20% to prevent thundering herd
                jitter = random.uniform(0.8, 1.2)
                final_wait_time = wait_time * jitter

                logger.debug(
                    "Server error (attempt %d/%d), waiting %.2f seconds before retry: %s",
                    retry_count,
                    max_retries,
                    final_wait_time,
                    str(exc),
                )
                time.sleep(final_wait_time)
            except Exception:
                # Decrement counter for any other exception
                with self.inflight_posts_condition:
                    self.inflight_posts_count -= 1
                    self.inflight_posts_condition.notify_all()
                raise

        # Check if abort was requested - session ID is already stored, we can exit cleanly
        if self.abort_event.is_set():
            raise KeyboardInterrupt()

        large_assets = []
        small_assets = []

        for asset, asset_response in zip(
            assets_to_upload, upload_session_response.assets
        ):
            if asset["size"] > config.ASSET_UPLOAD_SESSION_MULTIPART_MIN_SIZE:
                large_assets.append((asset, asset_response))
            else:
                small_assets.append((asset, asset_response))

        cpu_count = int(os.cpu_count() or 1)
        multipart_executor = None
        futures = []

        try:
            # Create multipart executor only if needed (for large files)
            if large_assets:
                multipart_workers = max(
                    int(cpu_count * config.ASSET_UPLOAD_SESSION_WORKERS_RATIO / 2), 1
                )
                multipart_executor = concurrent.futures.ThreadPoolExecutor(
                    initializer=self._init_http_session, max_workers=multipart_workers
                )

            # Use shared upload executor instead of creating one per batch
            # This limits total concurrent connections across all parallel batches
            # Process large assets with multipart upload
            for asset, asset_response in large_assets:
                if multipart_executor is None:
                    raise RuntimeError(
                        "Multipart executor not initialized for large assets"
                    )
                futures.append(
                    self.shared_upload_executor.submit(
                        self._upload_multipart_file_through_signed_url,
                        multipart_executor,
                        upload_session_response.id,
                        asset_response,
                        self.abort_event,
                    )
                )

            # Process small assets with normal upload
            for asset, asset_response in small_assets:
                futures.append(
                    self.shared_upload_executor.submit(
                        self._upload_file_through_signed_url,
                        asset_response,
                        self.abort_event,
                    )
                )

            # Use as_completed for better progress feedback
            success_count = 0
            failed_count = 0
            for future in concurrent.futures.as_completed(futures):
                try:
                    filename, uploaded = future.result()

                    if uploaded:
                        logger.debug("Finished Uploading: %s", filename)
                        success_count += 1
                        # Update global progress tracker
                        if self.global_progress_tracker is not None:
                            self.global_progress_tracker.update_success()
                    else:
                        logger.debug("Failed to upload %s", filename)
                        failed_count += 1
                        # Update global progress tracker
                        if self.global_progress_tracker is not None:
                            self.global_progress_tracker.update_failure()
                except Exception as exc:
                    logger.error("Error processing upload result: %s", exc)
                    failed_count += 1
                    # Update global progress tracker
                    if self.global_progress_tracker is not None:
                        self.global_progress_tracker.update_failure()

            logger.debug(
                "Upload session finished: %d success, %d failed",
                success_count,
                failed_count,
            )

        except KeyboardInterrupt as exc:
            self.abort_event.set()

            # Cancel all pending futures
            cancelled_count = 0
            for future in futures:
                if not future.done():
                    if future.cancel():
                        cancelled_count += 1

            if cancelled_count > 0:
                logger.debug("Cancelled %d pending uploads", cancelled_count)

            self._cancel_upload_session()
            raise KeyboardInterrupt("Upload interrupted by user") from exc
        except Exception as exc:
            self.abort_event.set()

            # Cancel all pending futures on error
            for future in futures:
                if not future.done():
                    future.cancel()

            self._cancel_upload_session()
            raise

        finally:
            if multipart_executor:
                multipart_executor.shutdown(wait=False)

        # Upload completed successfully - remove session ID from tracking list
        # so it won't be cancelled if a later batch fails
        with self.assets_lock:
            if upload_session_response.id in self.upload_session_ids:
                self.upload_session_ids.remove(upload_session_response.id)

        return upload_session_response

    def wait_until_done(
        self,
        raise_exception_if: Union[
            OperationStatusOverview, str
        ] = OperationStatusOverview.ERRORED,
    ):
        """
        Wait for all operations to be done.
        This function only works when background is set to False.
        It functions the same as Operation.wait_until_done.

        :param raise_exception_if: The condition to raise error.
        :return: The operation status metadata if the operation has finished,
        """
        assert isinstance(raise_exception_if, (str, OperationStatusOverview))

        if isinstance(raise_exception_if, str):
            raise_exception_if = OperationStatusOverview(raise_exception_if)

        if len(self.operation_ids) == 0:
            logger.debug("All operations finished")
            return True

        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Submit tasks to the executor
            futures = [
                executor.submit(
                    self.operation.wait_until_done,
                    op_id,
                    raise_exception_if=raise_exception_if,
                    abort_event=self.abort_event,
                )
                for op_id in self.operation_ids
            ]

            # Optionally, you can handle the results of the uploads here
            try:
                for future in futures:
                    res = future.result()

                    logger.debug("Finished operation: % s", res)

                logger.debug("All operations finished")

            except KeyboardInterrupt:
                self.abort_event.set()
                for future in futures:
                    if not future.done():
                        future.cancel()
                raise
            except Exception as exc:
                raise exc

        return True

    def _check_current_asset_size(self):
        """Check if the current asset size is greater than the batch size.
        If so, upload the assets and clear the current batch.
        """
        with self.assets_lock:
            if len(self.assets) >= config.ASSET_UPLOAD_SESSION_BATCH_SIZE:
                if not self._batched_upload_warning_flag:
                    logger.warning(
                        f"Detected more than {config.ASSET_UPLOAD_SESSION_BATCH_SIZE} assets. "
                        f"Uploads are batched in groups of {config.ASSET_UPLOAD_SESSION_BATCH_SIZE}, "
                        "subsequent batches will be uploaded in parallel."
                    )
                    self._batched_upload_warning_flag = True

                # Get current total of all assets added so far
                current_total = len(self.file_name_map)

                # Initialize progress tracker on first batch if not already done
                if self.global_progress_tracker is None:
                    self.global_progress_tracker = UploadProgressTracker(
                        total_assets=current_total,
                        show_progress=self.show_progress,
                    )
                    self.global_progress_tracker.start()
                    logger.debug(
                        f"Progress tracker initialized with {current_total} assets"
                    )
                else:
                    # Update total dynamically as more assets are added
                    self.global_progress_tracker.update_total(current_total)

                # Make a copy of current assets to upload
                assets_batch = self.assets[:]

                # Submit upload to thread pool
                # Rate limiting is now handled at the API call level in _upload_assets()
                future = self.batch_upload_executor.submit(
                    self._upload_assets, assets_batch
                )
                self.batch_upload_futures.append(future)

                logger.info(f"Submitted batch of {len(assets_batch)} assets for upload")

                # clear current batch
                self.assets = []

    def _cancel_upload_session(self) -> None:
        """Cancel upload session"""
        # Make a copy to avoid issues with concurrent modifications
        with self.assets_lock:
            session_ids = self.upload_session_ids[:]

        if not session_ids:
            return

        for upload_session_id in session_ids:
            try:
                self.requester.POST(
                    f"/projects/{self.project_id}/assetuploadsessions/{upload_session_id}:cancel",
                    response_type=CancelResponse,
                    ignore_errno=[409],
                )
            except Exception as exc:
                logger.debug(
                    "Failed to cancel session %s: %s", upload_session_id, str(exc)
                )

    def get_operation_ids(self):
        """
        A list of operation IDs. Because some dependency limits,
        each operation allows a maximum of 1000 assets.
        So if the total number of assets goes up over 1000,
        it will return a list of operation IDs.

        If you want to control the operations manually,
        you can use this function to get the operation ids.
        And the call project.operation.wait_until_done or project.operation.get
        to wait for the operations to finish.

        :return: A list of operation ids.

        :example:
            .. code-block:: python

                ['op_1', 'op_2', 'op_3']

        """
        return self.operation_ids
