#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   asset_fixture.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Datature Assets Test Data
"""

# pylint: disable=C0301
list_assets_response = {
    "next_page": "ZjY0YTdiYTI0NzAzNThlMDljZGNjYzY4Zg",
    "data": [
        {
            "id": "asset_e478b4d2-496b-4abe-a1d2-3cccad605002",
            "object": "asset",
            "filename": "boat180.png",
            "project": "proj_306c543ddd4ff1188a6e4b43a586b62a",
            "create_date": 1688713764134,
            "metadata": {
                "file_size": 186497,
                "mime_type": "image/png",
                "status": "annotated",
                "height": 243,
                "width": 400,
                "groups": ["main"],
                "custom_metadata": {},
            },
            "statistic": {
                "tags_count": [{"name": "boat", "count": 1}],
                "total_annotations": 1,
            },
            "url": "https://storage.googleapis.com/assets.datature.io/306c543ddd4ff1188a6e4b43a586b62a/assets/boat180.png?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=gcs-asset-signer%40datature-nexus.iam.gserviceaccount.com%2F20230707%2Fauto%2Fstorage%2Fgoog4_request&X-Goog-Date=20230707T071051Z&X-Goog-Expires=86400&X-Goog-SignedHeaders=host&generation=1688713773057960&X-Goog-Signature=81ed17f20a5af973c6c4a95e3ea454751f83abc91c0b95999329f68b85724f51f9df032789a7e29bb4bc09b6acffbbd4fca56b2e1c7ca133dff29c79088bbfcd123117ad31aacf7e146de6f98c90a9958985a1d38e781c4b2afae3a15c011404229d29445634b92f71468b78b50aec20bc8a10781305fac529d0c6b9b444c91536d95b2490acdc19341a2126aac40b1013514ef4b2082075c047bbcae1ffeb74044c6ec093d2dab6c391f4f3a886613c9faeb78e06ce4ccf7b428651623e4afc38a544fc4c8d934a9dbeb4ca61f68c103252e43a2248461613758e3421a4737707177ef16983e97aedd6aa36adfdd963c1b7a1d19c81abcdff0efd9373056c59",
        },
    ],
}

annotations_response = [
    {
        "id": "annot_1e1a0c12-cf6a-42cb-8347-6596006621b5",
        "object": "annotation",
        "bound_type": "rectangle",
        "bound": [
            [0.425, 0.49382716049382713],
            [0.425, 0.6419753086419753],
            [0.6, 0.6419753086419753],
            [0.6, 0.49382716049382713],
        ],
        "project_id": "proj_306c543ddd4ff1188a6e4b43a586b62a",
        "asset_id": "asset_e478b4d2-496b-4abe-a1d2-3cccad605002",
        "tag": "boat",
    }
]
