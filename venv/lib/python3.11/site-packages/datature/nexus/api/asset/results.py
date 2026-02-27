#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
 ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   results.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Result wrappers for asset operations
"""

from pathlib import Path
from typing import List

from tqdm import tqdm


class AssetDownloadResult:
    """Asset download result wrapper.

    Attributes:
        project_id: Project ID of downloaded assets
        count: Number of assets downloaded
        save_dir: Directory path where assets were saved

    Examples:
        ```python
        result = project.assets.download()
        print(f"Downloaded: {result.count} assets")
        ```

    """

    def __init__(self, project_id: str, count: int, save_dir: str):
        """Initialize asset download result.

        Args:
            project_id: Project ID of downloaded assets
            count: Number of assets downloaded
            save_dir: Directory path where assets were saved

        """
        self.project_id = project_id
        self.count = count
        self.save_dir = save_dir

    @property
    def save_path(self) -> Path:
        """Path object for save directory."""
        return Path(self.save_dir)

    @property
    def size_mb(self) -> float:
        """Total size of downloaded assets in MB (if available)."""
        try:
            files = list(self.save_path.rglob("*"))
            total_size = 0

            with tqdm(
                total=len(files),
                desc="Calculating size",
                unit="files",
                ncols=100,
                disable=len(files) < 100,
            ) as pbar:
                for f in files:
                    if f.is_file():
                        total_size += f.stat().st_size
                    pbar.update(1)

            return total_size / (1024 * 1024)
        except (OSError, ValueError):
            return 0.0

    @property
    def file_list(self) -> List[Path]:
        """List of all downloaded asset files."""
        try:
            files = list(self.save_path.rglob("*"))
            file_list = []

            with tqdm(
                total=len(files),
                desc="Scanning files",
                unit="files",
                ncols=100,
                disable=len(files) < 100,
            ) as pbar:
                for f in files:
                    if f.is_file():
                        file_list.append(f)
                    pbar.update(1)

            return file_list
        except (OSError, ValueError):
            return []
