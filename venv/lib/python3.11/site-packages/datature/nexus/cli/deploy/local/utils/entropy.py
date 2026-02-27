#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   entropy.py
@Author  :   Wei Loon Cheng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Entropy calculation utility functions.
"""

from typing import Dict, List

import numpy as np

from datature.nexus.cli.deploy.local.types.prediction_response import Prediction
from datature.nexus.cli.deploy.local.utils.label_map import LabelMap


def calculate_avg_entropy(predictions: List[Prediction]) -> float:
    """Calculate average entropy across all prediction scores.

    Args:
        predictions: Dictionary containing prediction data with 'scores' key.
        threshold: Minimum score threshold for entropy calculation.

    Returns:
        Average entropy value.
    """
    scores = [prediction.confidence for prediction in predictions]
    if len(scores) == 0:
        return 0.0

    valid_scores = [score for score in scores if 0 < score <= 1]

    if len(valid_scores) == 0:
        return 0.0

    entropies = [
        -score * np.log2(score) - (1 - score) * np.log2(1 - score)
        for score in valid_scores
    ]

    return float(np.mean(entropies))


def calculate_avg_entropy_per_class(
    predictions: List[Prediction], label_map: LabelMap
) -> Dict[str, float]:
    """Calculate average entropy per class based on prediction scores.

    Args:
        predictions: Dictionary containing prediction data with 'scores' and 'classes' keys.
        label_map: Label map object.
        threshold: Minimum score threshold for entropy calculation.

    Returns:
        Dictionary containing average entropy per class.
    """
    scores = np.array([prediction.confidence for prediction in predictions])
    classes = np.array([prediction.tag.id for prediction in predictions])

    if len(scores) == 0 or len(classes) == 0:
        return {}

    unique_classes = np.unique(classes)
    unique_class_names = [label_map[int(class_id)].name for class_id in unique_classes]

    class_entropies = []

    for class_id in unique_classes:
        # Get scores for this class
        class_mask = classes == class_id
        class_scores = scores[class_mask]

        if len(class_scores) == 0:
            continue

        valid_scores = [score for score in class_scores if 0 < score <= 1]

        if len(valid_scores) == 0:
            continue

        entropies = [
            -score * np.log2(score) - (1 - score) * np.log2(1 - score)
            for score in valid_scores
        ]

        class_entropies.append(np.mean(entropies))

    if len(class_entropies) == 0:
        return {}

    return {
        class_name: float(entropy)
        for class_name, entropy in zip(unique_class_names, class_entropies)
    }
