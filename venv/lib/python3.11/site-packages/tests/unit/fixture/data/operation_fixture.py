#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   operation_fixture.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Datature Operation Test Data
"""

pending_operation_response = {
    "id": "op_c26ea31d-599c-4a03-8b0d-b2bc9995fa8a",
    "object": "operation",
    "kind": "nexus.annotations.export",
    "status": {
        "overview": "Running",
        "message": "Operation running",
        "progress": {
            "unit": "asset",
            "withStatus": {
                "Queued": 10,
                "Running": 0,
                "Finished": 436,
                "Errored": 0,
                "Cancelled": 0,
            },
        },
    },
    "createDate": 1701755214003,
    "updateDate": 1701755215476,
}

finished_operation_response = {
    "id": "op_c26ea31d-599c-4a03-8b0d-b2bc9995fa8a",
    "object": "operation",
    "kind": "nexus.annotations.export",
    "status": {
        "overview": "Finished",
        "message": "Operation running",
        "payload": "",
        "progress": {
            "unit": "asset",
            "withStatus": {
                "Queued": 0,
                "Running": 0,
                "Finished": 436,
                "Errored": 0,
                "Cancelled": 0,
            },
        },
    },
    "createDate": 1701755214003,
    "updateDate": 1701755215476,
}

errored_operation_response = {
    "id": "op_c26ea31d-599c-4a03-8b0d-b2bc9995fa8a",
    "object": "operation",
    "kind": "nexus.annotations.export",
    "status": {
        "overview": "Errored",
        "message": "Operation running",
        "payload": "",
        "progress": {
            "unit": "asset",
            "withStatus": {
                "Queued": 0,
                "Running": 0,
                "Finished": 436,
                "Errored": 0,
                "Cancelled": 0,
            },
        },
    },
    "createDate": 1701755214003,
    "updateDate": 1701755215476,
}

annotation_operation_response = {
    "opId": "op_8e794c4d-47b4-460c-bcd1-173ab5d109d7",
    "status": "Finished",
    "download": {
        "method": "GET",
        "url": "https://nexus.datature.io/projects",
        "expiryDate": 1706183829833,
    },
}

annotation_export_error_response = {
    "opId": "op_8e794c4d-47b4-460c-bcd1-173ab5d109d7",
    "status": "Errored",
}

annotation_import_finished_response = {
    "id": "annotsess_de40cabf-8275-4844-9d29-1ae3f7af5ca8",
    "object": "annotation_import_session",
    "projectId": "proj_cd067221d5a6e4007ccbb4afb5966535",
    "status": {
        "overview": "Finished",
        "message": "Annotation Imported successfully.",
        "updateDate": 1705465365932,
        "files": {
            "totalSizeBytes": 63368,
            "pageCount": 1,
            "withStatus": {"Processing": 0, "Processed": 1, "FailedProcess": 0},
        },
        "annotations": {"withStatus": {"Processed": 1549, "Committed": 1549}},
    },
    "expiryDate": 1705468620676,
    "createDate": 1705465320781,
    "updateDate": 1705465365945,
}

annotation_import_errored_response = {
    "id": "annotsess_a2c771e8-6b85-47a2-b844-d25ee18e6ae3",
    "object": "annotation_import_session",
    "projectId": "proj_cd067221d5a6e4007ccbb4afb5966535",
    "status": {
        "overview": "Errored",
        "message": "AnnotationsCommitted errored, please contract support.",
        "updateDate": 1701772558131,
        "files": {
            "totalSizeBytes": 0,
            "pageCount": 1,
            "withStatus": {"Processing": 0, "Processed": 0, "FailedProcess": 0},
        },
        "annotations": {"withStatus": {"Processed": 0, "Committed": 0}},
    },
    "expiryDate": 1701768467656,
    "createDate": 1701765173451,
    "updateDate": 1701772558150,
}

annotation_import_running_response = {
    "id": "annotsess_a2c771e8-6b85-47a2-b844-d25ee18e6ae3",
    "object": "annotation_import_session",
    "projectId": "proj_cd067221d5a6e4007ccbb4afb5966535",
    "status": {
        "overview": "Running",
        "message": "Running.",
        "updateDate": 1701772558131,
        "files": {
            "totalSizeBytes": 0,
            "pageCount": 1,
            "withStatus": {"Processing": 0, "Processed": 0, "FailedProcess": 0},
        },
        "annotations": {"withStatus": {"Processed": 0, "Committed": 0}},
    },
    "expiryDate": 1701768467656,
    "createDate": 1701765173451,
    "updateDate": 1701772558150,
}
