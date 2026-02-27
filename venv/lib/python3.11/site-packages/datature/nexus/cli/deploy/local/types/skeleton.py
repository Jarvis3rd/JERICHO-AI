#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   skeleton.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Keypoint skeleton types.
"""
# pylint: disable=C0103

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import TypedDict
from uuid import uuid4


class SkeletonParsingError(ValueError):
    """An error occurred while parsing a skeleton."""

    def __init__(self, message: str):
        super().__init__(f"Error parsing skeleton: {message}")


class KeypointJson(TypedDict):
    """Keypoint json type."""

    id: str
    name: str
    category: list[str]


class ConnectionJson(TypedDict):
    """Connection json type."""

    pair: list[str]  # keypoint names


class SkeletonJson(TypedDict):
    """Skeleton json type."""

    skeletonId: str
    name: str
    keypoints: list[KeypointJson]
    connections: list[ConnectionJson]


@dataclass
class Keypoint:
    """Keypoint object."""

    name: str
    id_: str = field(default_factory=lambda: str(uuid4()))
    category: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not isinstance(self.name, str):
            raise SkeletonParsingError(
                f"The keypoint name "
                f"{self.name} is not a string. "
                "Please ensure all keypoint names are strings."
            )

        if not isinstance(self.category, list):
            raise SkeletonParsingError(
                f"The keypoint category "
                f"{self.category} is not a list. "
                "Please ensure all keypoint categories are lists."
            )

        for category in self.category:
            if not isinstance(category, str):
                raise SkeletonParsingError(
                    f"The keypoint category "
                    f"{self.category} is not a list of strings. "
                    "Please ensure all keypoint categories are lists of "
                    "strings."
                )

    def to_json(self):
        """Convert keypoint object to json."""
        return {
            "name": self.name,
            "category": self.category,
        }

    @classmethod
    def from_json(cls, input_json: KeypointJson):
        """Create a keypoint object from a keypoint json."""
        if "name" not in input_json:
            raise SkeletonParsingError(
                "The keypoint "
                f"{input_json} does not have a 'name' field. "
                "Please ensure all keypoints have a "
                f"'name' field."
            )

        id_ = input_json.get("id", str(uuid4()))
        name = input_json["name"]
        category = input_json.get("category", [])

        return cls(
            id_=id_,
            name=name,
            category=category,
        )


@dataclass
class Connection:
    """Connection object."""

    pair: list  # keypoint names / indices

    def __post_init__(self):
        if not isinstance(self.pair, list):
            raise SkeletonParsingError(
                f"A given keypoint connection pair "
                f"{self.pair} is not a list. "
                "Please ensure all keypoint connection pairs are lists."
            )

        if len(self.pair) != 2:
            raise SkeletonParsingError(
                f"A given keypoint connection pair "
                f"{self.pair} is not a list of length 2. "
                "Please ensure all keypoint connection pairs are lists of "
                "length 2."
            )

        for name in self.pair:
            if not isinstance(name, (str, int)):
                raise SkeletonParsingError(
                    f"A given keypoint connection pair "
                    f"{self.pair} is not a list of strings or ints."
                    "Please ensure all keypoint connection pairs are "
                    "lists of strings."
                )

    def to_json(self):
        """Convert connection object to json."""
        return {
            "pair": self.pair,
        }

    @classmethod
    def from_json(cls, input_json):
        """Create a connection object from a connection json."""
        if not isinstance(input_json, dict):
            raise TypeError(
                f"The keypoint connection "
                f"{input_json} is not a dictionary. "
                "Please ensure all keypoint connections are dictionaries."
            )

        if "pair" not in input_json:
            raise SkeletonParsingError(
                "The keypoint connection "
                f"{input_json} does not have a 'pair' field. "
                "Please ensure all keypoint connections have a 'pair' field."
            )

        pair = input_json["pair"]
        return cls(pair=pair)


@dataclass
class Skeleton:
    """Skeleton object."""

    name: str
    keypoints: list[Keypoint]
    connections: list[Connection]

    @classmethod
    def from_json(cls, json: SkeletonJson):
        """Create a skeleton object from a skeleton json.

        Performs type checking to ensure sanity of skeleton.
        If connection key is "id", the connections are converted to named
        connections.
        """
        if not isinstance(json, dict):
            raise TypeError(
                "The skeleton json "
                "provided is not a dictionary. "
                "Please ensure all skeleton jsons are dictionaries."
            )

        for skeleton_field in ["name", "connections"]:
            if skeleton_field not in json:
                raise SkeletonParsingError(
                    "The skeleton "
                    f"provided does not have a '{skeleton_field}' field. "
                    "Please ensure all skeletons have a "
                    f"{skeleton_field} field."
                )

        name = json["name"]
        if not isinstance(name, str):
            raise SkeletonParsingError(
                "The skeleton name "
                f"{name} is not a string. "
                "Please ensure all skeleton names are strings."
            )

        return cls(
            name=json["name"],
            keypoints=[Keypoint.from_json(kp) for kp in json["keypoints"]],
            connections=[Connection.from_json(con) for con in json["connections"]],
        )

    def index_connections(self, offset=0) -> list[Connection]:
        """Convert named connections to index connections.

        Args:
            offset: The offset to add to the indices.
            NOTE: this is used for coco reupload because it starts at 1.
        """
        keypoint_names = [kp.name for kp in self.keypoints]

        return [
            replace(con, pair=[keypoint_names.index(i) + offset for i in con.pair])
            for con in self.connections
        ]

    def compare(self, other: Skeleton) -> str:
        """Compare two skeletons and return differences."""
        differences = ""

        if not isinstance(other, Skeleton):
            differences += "Skeletons are not the same type.\n"

        if self.name != other.name:
            differences += (
                "Skeletons have different names " f"{self.name} and {other.name}.\n"
            )

        self_kp_names = [kp.name for kp in self.keypoints]
        other_kp_names = [kp.name for kp in other.keypoints]

        for position, (self_kp_name, other_kp_name) in enumerate(
            zip(self_kp_names, other_kp_names)
        ):
            if self_kp_name != other_kp_name:
                differences += (
                    f"Keypoint at position {position} have different names "
                    f"{self_kp_name} and "
                    f"{other_kp_name}.\n"
                )

        self_connections = [
            frozenset(connection.pair) for connection in self.connections
        ]

        other_connections = [
            frozenset(connection.pair) for connection in other.connections
        ]

        self_connections.sort(key=hash)
        other_connections.sort(key=hash)

        for self_connection, other_connection in zip(
            self_connections, other_connections
        ):
            if self_connection != other_connection:
                differences += (
                    f"Connection {self_connection} and {other_connection} "
                    "are not the same.\n"
                )

        if len(differences) > 0:
            differences = differences[:-1]  # Remove last newline
        return differences

    def get_ids(self, other: Skeleton) -> list[int]:
        """Get the indices of the keypoints in the other skeleton."""
        self_kp_names = [kp.name for kp in self.keypoints]
        indices = [self_kp_names.index(kp.name) for kp in other.keypoints]

        return indices

    def to_json(self):
        """Convert skeleton object to json."""
        json_keypoints = [keypoint.to_json() for keypoint in self.keypoints]
        json_connections = [connection.to_json() for connection in self.connections]

        return {
            "name": self.name,
            "keypoints": json_keypoints,
            "connections": json_connections,
        }
