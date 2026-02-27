#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   artifact_fixture.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Datature Artifact Test Data
"""

# pylint: disable=C0301
artifacts_includes_exports_response = [
    {
        "id": "artifact_652e7022a70966c12f2203c1",
        "object": "artifact",
        "runId": "run_5cadcd5b-1590-4f2e-83b8-cb908c57087c",
        "projectId": "proj_ff801f417e7199e46a5c1eaa22052d56",
        "isTraining": False,
        "step": 5000,
        "flowTitle": "Yolov8 Workflow",
        "artifactName": "ckpt-23-datature-yolov8n-cls",
        "modelName": "fasterrcnn-inceptionv2-1024x1024",
        "createDate": 1697542178156,
        "metric": {"totalLoss": 0.0032949},
        "isDeployed": False,
        "exportOptions": [
            {
                "format": "ONNX",
                "optimizations": {"quantization": ["float32", "float16"]},
                "defaultOptimizations": {"quantization": "float32"},
            },
            {
                "format": "TensorFlow",
                "optimizations": {"quantization": ["float32"]},
                "defaultOptimizations": {"quantization": "float32"},
            },
            {
                "format": "PyTorch",
                "optimizations": {"quantization": ["float32"]},
                "defaultOptimizations": {"quantization": "float32"},
            },
            {
                "format": "TFLite",
                "optimizations": {"quantization": ["float32"]},
                "defaultOptimizations": {"quantization": "float32"},
            },
        ],
    },
    {
        "id": "artifact_652e7022a70966c12f2203c0",
        "object": "artifact",
        "runId": "run_5cadcd5b-1590-4f2e-83b8-cb908c57087b",
        "projectId": "proj_ff801f417e7199e46a5c1eaa22052d56",
        "isTraining": False,
        "step": 5000,
        "flowTitle": "Yolov8 Workflow",
        "artifactName": "ckpt-23-datature-yolov8n-cls",
        "modelName": "fasterrcnn-inceptionv2-1024x1024",
        "createDate": 1697542178156,
        "metric": {"totalLoss": 0.0032949},
        "isDeployed": False,
        "exportOptions": [
            {
                "format": "ONNX",
                "optimizations": {"quantization": ["float32", "float16"]},
                "defaultOptimizations": {"quantization": "float32"},
            },
            {
                "format": "TensorFlow",
                "optimizations": {"quantization": ["float32"]},
                "defaultOptimizations": {"quantization": "float32"},
            },
            {
                "format": "PyTorch",
                "optimizations": {"quantization": ["float32"]},
                "defaultOptimizations": {"quantization": "float32"},
            },
            {
                "format": "TFLite",
                "optimizations": {"quantization": ["float32"]},
                "defaultOptimizations": {"quantization": "float32"},
            },
        ],
        "exports": [
            {
                "id": "model_x4qq70769621y5rrv007447q7y5xw279",
                "object": "model",
                "artifactId": "artifact_652e7022a70966c12f2203c0",
                "status": "Finished",
                "format": "Onnx",
                "quantization": "float32",
                "createDate": 1699584021867,
                "download": {
                    "method": "GET",
                    "expiryDate": 1706263764534,
                    "url": "https://storage.googleapis.com/exports.staging.datature.io/ff801f417e7199e46a5c1eaa22052d56/models/5cadcd5b-1590-4f2e-83b8-cb908c57087b-ckpt-23-datature-yolov8n-cls-onnx.zip?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=artifact-services%40datature-nexus-staging.iam.gserviceaccount.com%2F20240125%2Fauto%2Fstorage%2Fgoog4_request&X-Goog-Date=20240125T100924Z&X-Goog-Expires=86400&X-Goog-SignedHeaders=host&X-Goog-Signature=17b63f5804b6dcf20693e956704151d0c0720df7c182833ff96c67219b2f8966274008ba872192c160fc0b00ac11f39789bf01152d03e7a81185903d7f4c027d5675795dfcae36ebb93709fca96bc1872993c1f251ac7cadbeb14fcd5e112c4df8af053462072db403b20d551019c5248ac94d0c7cda652db40033d4adeefa882e5f6b52de1153426a4b08d8e54560b7a02b1769171ea2a02fd9f0bf91cd4f877a25e538316222f0eb534a28e038247786a07c552c515229404d2aa02264807bbe3b6163485770deeb90934b22be4c7cdfcfd8ba436f429de45bfc7f9131e576fb75181ab1bcfec8054753a0ba2633a2a696ce6aa6ea1a2812fcbbd26b0eec31",
                },
            }
        ],
    },
]
