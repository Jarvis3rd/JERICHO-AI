#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   upload_session_fixture.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Datature Upload Session Test Data
"""

# pylint: disable=C0301
upload_assets_response = {
    "id": "up_057963cb-b945-4fff-9d9e-20adaab82ad5",
    "opId": "op_057963cb-b945-4fff-9d9e-20adaab82ad5",
    "assets": [
        {
            "metadata": {
                "filename": "test.jpeg",
                "mime": "image/jpeg",
                "size": 5613,
                "crc32c": -384617082,
            },
            "upload": {
                "method": "POST",
                "url": "https://storage.googleapis.com/transient.staging.datature.io/593526c7bfd916be7faa8465728f988f/ingestions/37a65f26-3439-472d-af3d-74a4c9767cc6/e42e4eb7-e3a2-4d50-91bf-a829a624b62a/assets/test.jpeg?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=gcs-asset-signer%40datature-nexus-staging.iam.gserviceaccount.com%2F45dd6b856ade00802a00dc6d7b4c5ac27a62e1a963fdb7455adf826af85a96ada4ff350daf4c4ea076fa4c18c360296781b66d8a958cb262b45ef1f848fa71c811ec910f8c745f5c46b48c4c41c5dda2c3fce0c702f6558b52872048ddbd2bf752561c7f88eb20346bdc8918b8a8c1b7f45494571399963335286163944c4ee9f31743320ca21c93b0459f3121cd5fc2b5c56232986422acba5a2781127bd738bbf8379e8b7314254922bf76f3773c5193a97acb658a75aabb8bff8ade1c258158d",
                "headers": {
                    "content-type": "image/jpeg",
                    "x-goog-meta-datature-upload": "eyJmaWxlm1haW4iXX0=",
                    "x-goog-hash": "crc32c=6RM1hg==",
                },
                "expiryDate": 1669011530693,
            },
        }
    ],
}
