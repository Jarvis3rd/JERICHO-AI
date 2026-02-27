#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   config.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   SDK config module
"""

from pathlib import Path

# Default configurations
ASSET_UPLOAD_SESSION_BATCH_SIZE: int = 5000
IMAGE_MAX_SIZE: int = 256 * 1024 * 1024  # 256MB
MEDICAL_3D_MAX_SIZE: int = 1024 * 1024 * 1024  # 1GB
VIDEO_MAX_SIZE: int = 512 * 1024 * 1024 * 1024  # 512GB
ASSET_UPLOAD_SESSION_MULTIPART_MIN_SIZE: int = 1 * 1024 * 1024 * 1024  # 1GB
ASSET_UPLOAD_SESSION_WORKERS_RATIO: float = 0.6
ASSET_UPLOAD_MAX_RETRIES: int = 3

# Rate limiting configuration for session creation
# Server limit: 15 sessions per 5 minutes (300 seconds)
ASSET_UPLOAD_SESSION_RATE_LIMIT_MAX_REQUESTS: int = 15
ASSET_UPLOAD_SESSION_RATE_LIMIT_WINDOW_SECONDS: float = 300.0

# Maximum number of parallel batches (session creations + uploads)
# Set to 0 for unlimited (will use cpu_count * WORKERS_RATIO)
# Note: Actual parallelism is constrained by rate limit
ASSET_UPLOAD_SESSION_MAX_PARALLEL_BATCHES: int = 10

# File upload parallelism per batch
# Higher values = more concurrent GCS uploads per batch
ASSET_UPLOAD_PER_BATCH_WORKERS_RATIO: float = 2.0

ASSET_DOWNLOAD_DEFAULT_BATCH_SIZE: int = 1000
ASSET_DEFAULT_SAVE_DIR: str = Path.home() / ".datature" / "nexus" / "assets"

ANNOTATION_IMPORT_SESSION_MAX_SIZE: int = 100000
ANNOTATION_IMPORT_SESSION_BATCH_SIZE: int = 1000
ANNOTATION_IMPORT_SESSION_BATCH_BYTES: int = 1024 * 1024 * 1024  # 1GB
OPERATION_LOOPING_TIMEOUT_SECONDS: int = 36000
OPERATION_LOOPING_DELAY_SECONDS: int = 8
REQUEST_TIME_OUT_SECONDS = (60, 3600)
FILE_CHUNK_SIZE = 8 * 1024 * 1024  # 8MB

# Retry configuration
REQUEST_MAX_RETRIES: int = 3
REQUEST_RETRY_DELAY_SECONDS: float = 1.0
REQUEST_RETRY_BACKOFF_MULTIPLIER: float = 2.0
REQUEST_RETRY_MAX_DELAY_SECONDS: float = 60.0
