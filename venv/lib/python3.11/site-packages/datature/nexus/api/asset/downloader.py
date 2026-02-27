#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
 ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   downloader.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Asset downloader module
"""

import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, Iterator, List, Optional, Tuple, Union

import requests
from tqdm import tqdm

from datature.nexus.config import (
    ASSET_DEFAULT_SAVE_DIR,
    ASSET_DOWNLOAD_DEFAULT_BATCH_SIZE,
)


def create_progress_bar(desc: str, total: int, unit: str = "files", ncols: int = 100):
    """Create a tqdm progress bar with consistent styling."""
    return tqdm(
        total=total,
        desc=desc,
        unit=unit,
        ncols=ncols,
        bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]",
    )


class AssetBatchDownloadProgressTracker:
    """Progress tracker for batch asset downloads with real-time updates.

    Tracks and displays progress across multiple batches of asset downloads,
    providing users with detailed status including current batch number,
    files downloaded, and completion status.

    """

    def __init__(self, progress_bar, total_assets: int, total_batches: int):
        """Initialize the progress tracker.

        Args:
            progress_bar: tqdm progress bar instance for display updates.
            total_assets: Total number of assets across all batches.
            total_batches: Total number of batches to process.

        """
        self.progress_bar = progress_bar
        self.total_assets = total_assets
        self.total_batches = total_batches
        self.downloaded_count = 0
        self.batch_count = 0

    def start_batch(self):
        """Increment batch counter and update progress display."""
        self.batch_count += 1
        self._update_description()

    def update(self, files_completed: int):
        """Update progress with number of newly completed files.

        Args:
            files_completed: Number of files that have completed downloading.

        """
        self.downloaded_count += files_completed
        self.progress_bar.update(files_completed)
        self._update_description()

    def _update_description(self):
        """Update progress bar description with current download status."""
        self.progress_bar.set_description(
            f"Downloading {self.downloaded_count} / {self.total_assets} "
            f"assets (batch {self.batch_count} / {self.total_batches})"
        )

    def finish_success(self):
        """Mark download as successfully completed with success indicator."""
        self.progress_bar.set_description(
            f"✓ Downloaded {self.downloaded_count} / {self.total_assets} "
            "assets complete!"
        )

    def finish_cancelled(self):
        """Mark download as cancelled with cancellation indicator."""
        self.progress_bar.set_description("✗ Download cancelled")


class AssetDownloader:
    """Download dataset assets with parallel downloads and batch processing.

    Downloads asset files (images, videos, etc.) from the Datature platform
    using concurrent workers for optimal performance. Processes assets in batches
    to handle large datasets efficiently while managing memory usage.

    """

    def __init__(self, overwrite: bool = False, show_progress: bool = True):
        """Initialize the asset downloader.

        Args:
            overwrite: Whether to overwrite existing files. Defaults to False.
            show_progress: Whether to display progress bars during download.
                Defaults to True.

        """
        self._overwrite = overwrite
        self._show_progress = show_progress
        self._max_workers = min(max((8 or 4) * 2, 8), 64)  # Based on CPU cores

    def download(
        self,
        url_batches: Iterator[List[Tuple[str, str]]],
        save_dir: Union[Path, str],
        total_assets: int = 0,
        total_batches: int = 0,
    ) -> None:
        """Download multiple batches of assets with concurrent workers.

        Processes assets in batches using parallel workers to download multiple
        files simultaneously. Supports progress tracking across batches and
        graceful cancellation via interrupt signals.

        Args:
            url_batches: Iterator yielding lists of pre-signed URLs to download.
                Each list is processed as a batch.
            save_dir: Base directory where assets will be saved.
            total_assets: Total number of assets across all batches for progress
                calculation. Required for progress display.
            total_batches: Total number of batches to process for progress
                calculation. Required for progress display.

        Raises:
            InterruptedError: If download is cancelled by user via signal.

        """
        if self._show_progress and total_assets > 0:
            self._download_batches_with_progress(
                url_batches, save_dir, total_assets, total_batches
            )
        else:
            self._download_batches_simple(url_batches, save_dir)

    def _download_batches_with_progress(
        self,
        url_batches: Iterator[List[Tuple[str, str]]],
        save_dir: Union[Path, str],
        total_assets: int,
        total_batches: int,
    ) -> None:
        """Download batches with real-time progress tracking and status updates.

        Creates a progress bar showing download status including current batch,
        files completed, and time elapsed. Updates progress as each file completes.

        Args:
            url_batches: Iterator yielding lists of URLs to download.
            save_dir: Directory where assets will be saved.
            total_assets: Total number of assets for progress calculation.
            total_batches: Total number of batches for progress display.

        Raises:
            InterruptedError: If download is cancelled by user.

        """
        with tqdm(
            total=total_assets,
            desc="Downloading assets",
            unit="files",
            ncols=100,
        ) as progress_bar:
            progress_tracker = AssetBatchDownloadProgressTracker(
                progress_bar, total_assets, total_batches
            )

            try:
                for batch_urls in url_batches:
                    progress_tracker.start_batch()

                    self._download_single_batch(
                        batch_urls,
                        save_dir,
                        progress_callback=progress_tracker.update,
                    )

            except InterruptedError:
                progress_tracker.finish_cancelled()
                raise

            progress_tracker.finish_success()

    def _download_batches_simple(
        self,
        url_batches: Iterator[List[Tuple[str, str]]],
        save_dir: Union[Path, str],
    ) -> None:
        """Download batches without progress tracking for silent operation.

        Processes all batches sequentially without any UI updates. Useful for
        background operations or when progress display is disabled.

        Args:
            url_batches: Iterator yielding lists of URLs to download.
            save_dir: Directory where assets will be saved.

        """
        for batch_urls in url_batches:
            self._download_single_batch(batch_urls, save_dir)

    def _download_single_batch(
        self,
        download_urls: List[Tuple[str, str]],
        save_dir: Union[Path, str] = ASSET_DEFAULT_SAVE_DIR,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> None:
        """Download a single batch of assets using concurrent workers.

        Submits download tasks to a thread pool executor and waits for completion.
        Handles cancellation, errors, and optional progress callbacks for each
        completed file.

        Args:
            download_urls: List of pre-signed URLs to download in this batch.
            save_dir: Directory where assets will be saved.
            progress_callback: Optional callback function invoked after each
                successful download. Receives the number of completed files (1).

        Raises:
            InterruptedError: If download is cancelled by user.

        """
        absolute_save_path = Path(save_dir).resolve()
        absolute_save_path.mkdir(parents=True, exist_ok=True)

        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            future_to_url = {
                executor.submit(
                    self._download_file_worker, url, group, absolute_save_path
                ): (url, group)
                for url, group in download_urls
            }

            for future in as_completed(future_to_url):
                try:
                    future.result()

                    # Call progress callback if provided
                    if progress_callback:
                        progress_callback(1)

                except (OSError, ValueError, RuntimeError) as e:
                    # Log error but continue with other downloads
                    # Could be file system errors, invalid URLs, runtime errors
                    print(f"Download failed for {future_to_url[future]}: {e}")

    def _download_file_worker(
        self, download_url: str, group: str, file_path: Path
    ) -> None:
        """Worker function for downloading a single asset file.

        Extracts the filename from the URL, streams the file in chunks, and
        saves it to disk. Skips download if file already exists and overwrite
        is disabled.

        Args:
            download_url: Pre-signed URL to download from.
            file_path: Directory where the file will be saved.

        Raises:
            InterruptedError: If download is cancelled during streaming.

        """
        filename = download_url.split("/")[-1].split("?")[0]
        os.makedirs(file_path / group, exist_ok=True)
        target_file = file_path / group / filename

        if target_file.exists() and not self._overwrite:
            return

        # Retry logic for transient network errors
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(download_url, stream=True, timeout=30)
                response.raise_for_status()

                with open(target_file, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                # Download successful, exit retry loop
                return

            except requests.RequestException:
                # Clean up partial file on error
                if target_file.exists():
                    target_file.unlink()

                # If this was the last attempt, re-raise the exception
                if attempt == max_retries - 1:
                    raise

                # Exponential backoff
                backoff_time = min(2**attempt, 10)  # Max 10 seconds
                time.sleep(backoff_time)

    def generate_download_url_batches(
        self, asset_client, batch_size: int = ASSET_DOWNLOAD_DEFAULT_BATCH_SIZE
    ) -> Iterator[List[Tuple[str, str]]]:
        """Generate batches of download URLs using paginated response iterator.

        Args:
            asset_client: Asset client instance to query assets
            batch_size: Number of URLs per batch.

        Yields:
            List[str]: Batch of download URLs and groups.

        """
        # Collect URLs in batches from all pages using while loop
        batch = []
        page_cursor = None

        while True:
            pagination = {"limit": batch_size}
            if page_cursor:
                pagination["page"] = page_cursor

            assets_response = asset_client.list(pagination=pagination)

            # Process assets from current page
            for asset in assets_response.data:
                if asset.url:
                    batch.append((asset.url, asset.metadata.groups[0]))

                # Yield batch when it reaches the desired size
                if len(batch) >= batch_size:
                    yield batch
                    batch = []

            # Check if there's a next page
            if assets_response.next_page:
                page_cursor = assets_response.next_page
            else:
                # No more pages, exit loop
                break

        # Yield any remaining URLs in the final batch
        if batch:
            yield batch
