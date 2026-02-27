#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   label_map.py
@Author  :   Wei Loon Cheng
@Version :   1.0
@Contact :   hello@datature.io
@License :   Datature Outpost License 1.0
@Desc    :   Label map utilities.
"""

# pylint: disable=C0103

from dataclasses import dataclass
from typing import Dict, Generator, List, Optional, TextIO, Tuple, Union

import google.protobuf.text_format as pb_text_format

from datature.nexus.cli.deploy.local.types.prediction_response import Tag
from datature.nexus.cli.deploy.local.utils.colors import get_color_for_label_id

# pylint: disable=no-name-in-module
from datature.nexus.cli.deploy.local.utils.label_map_pb2 import LabelMap as PBLabelMap


class LabelMapParseError(Exception):
    """Error parsing a label map."""


@dataclass
class LabelMapEntry:
    """Entry in a label map."""

    label_id: int
    name: str
    color: str


class LabelMap:
    """Label map for a model."""

    _by_id: Dict[int, LabelMapEntry]
    _by_name: Dict[str, LabelMapEntry]

    def __init__(self, entries: List[LabelMapEntry]):
        self._by_id = {}
        self._by_name = {}

        for entry in entries:
            if entry.label_id in self._by_id:
                raise LabelMapParseError(
                    f"Tag ID {entry.label_id} already defined as "
                    f"'{self._by_id[entry.label_id].name}'"
                )

            if entry.name in self._by_name:
                raise LabelMapParseError(
                    f"Tag Name {entry.name} already defined as "
                    f"{self._by_name[entry.name].label_id}"
                )

            self._by_id[entry.label_id] = entry
            self._by_name[entry.name] = entry

    @property
    def names(self) -> Dict[str, LabelMapEntry]:
        """Get a dictionary of tag names to LabelMapEntries."""
        return self._by_name

    @property
    def ids(self) -> Dict[int, LabelMapEntry]:
        """Get a dictionary of tag IDs to LabelMapEntries."""
        return self._by_id

    def to_dict(self) -> Dict[str, Tag]:
        """Convert the label map to a dictionary of tag names to Tag objects."""
        return {
            str(entry.label_id): Tag(name=entry.name, color=entry.color)
            for entry in self._by_id.values()
        }

    def __getitem__(self, key: Union[int, str]) -> LabelMapEntry:
        if isinstance(key, int):
            return self._by_id[key]

        if isinstance(key, str):
            return self._by_name[key]

        return None

    def __len__(self) -> int:
        return len(self._by_id)

    def __iter__(self) -> Generator[Tuple[int, str, str], None, None]:
        return (
            (label_id, entry.name, entry.color)
            for label_id, entry in self._by_id.items()
        )


def LabelMapFromPbtxt(
    pbtxt_file_obj: TextIO, color_map: Optional[Dict[str, str]]
) -> LabelMap:
    """Read a label map from a file in PBTXT format."""

    try:
        pbtxt_file_text = pbtxt_file_obj.read()
    except IOError as e:
        raise LabelMapParseError("Unable to read label map from pbtxt") from e

    pb_label_map = PBLabelMap()
    entries: List[LabelMapEntry] = []
    have_background: bool = False
    have_class_zero: bool = False

    try:
        pb_text_format.Parse(pbtxt_file_text, pb_label_map)
    except pb_text_format.ParseError as e:
        raise LabelMapParseError("Could not load label map from pbtxt") from e

    for entry in pb_label_map.item:  # pylint: disable=E1101
        if len(entry.name) < 1:
            raise LabelMapParseError(
                f"Label map entry with ID {entry.id} has an empty name"
            )

        if entry.name.lower() == "background":
            have_background = True

        if entry.id == 0:
            have_class_zero = True

        entries.append(
            LabelMapEntry(
                label_id=entry.id,
                name=entry.name,
                color=(color_map or {}).get(
                    entry.name, get_color_for_label_id(entry.id)
                ),
            )
        )

    if not have_background and not have_class_zero:
        entries.append(LabelMapEntry(label_id=0, name="background", color="#000000"))

    if len(entries) < 1:
        raise ValueError("Label map has no entries")

    return LabelMap(entries)
