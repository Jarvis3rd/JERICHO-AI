#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   projects_fixture.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Datature Assets Test Data
"""

# pylint: disable=C0301
list_projects_response = [
    {
        "id": "proj_b705a30ae26671657f1fd51eb2d4739d",
        "object": "project",
        "name": "New Test Nam",
        "workspaceId": "ws_1c8aab980f174b0296c7e35e88665b13",
        "type": "ObjectDetection",
        "createDate": 1669185404836,
        "localization": "MULTI",
        "tags": ["boat"],
        "groups": ["main", "t", "group1", "gourp2", "1", "dataset"],
        "statistic": {
            "tagsCount": [{"name": "boat", "count": 240}],
            "totalAssets": 10272,
            "annotatedAssets": 142,
            "totalAnnotations": 240,
        },
    }
]

workspace_info_response = {
    "id": "ws_1c8aab980f174b0296c7e35e88665b13",
    "object": "workspace",
    "name": "Raighne's Workspace",
    "owner": "user_6323fea23e292439f31c58cd",
    "tier": "Developer",
    "createDate": 1694771445182,
}
