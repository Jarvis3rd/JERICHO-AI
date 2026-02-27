#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
  ████
██    ██   Datature
  ██  ██   Powering Breakthrough AI
    ██

@File    :   test_medical.py
@Author  :   Raighne.Weng
@Contact :   developers@datature.io
@License :   Apache License 2.0
@Desc    :   Datature Medical Test Cases
"""
# pylint: disable=W0703,W0012,W0212

import os
import unittest
from pathlib import Path

from datature.nexus.error import BadRequestError
from datature.nexus.medical import get_processor
from datature.nexus.medical.dicom_processor import DicomProcessor
from datature.nexus.medical.nii_processor import NiiProcessor


class TestMedicalProcessor(unittest.TestCase):
    """Datature Medical Processor Test Cases."""

    def test_dcm_file(self):
        """Test DCM files."""
        processor = get_processor("../fixture/data/medical/0002.DCM")

        assert isinstance(processor, DicomProcessor)

    def test_dcm_valid_function(self):
        """Test DCM files."""
        processor = get_processor("../fixture/data/medical/0002.DCM")
        try:
            processor.valid({})
        except Exception as e:
            assert isinstance(e, BadRequestError)

    def test_not_supported_file(self):
        """Test DCM files."""
        try:
            get_processor("../fixture/data/artifact_fixture.py")
        except Exception as e:
            assert isinstance(e, NotImplementedError)

    def test_dcm_file_output(self):
        """Test DCM files."""
        path = os.path.join(
            Path(__file__).parent.resolve(), "fixture/data/medical/0002.DCM"
        )

        processor = get_processor(path)

        process_data = {"file": path}

        processor.valid(process_data)
        resp = processor.process(process_data)

        assert len(resp) == 1

    def test_single_file_dcm_file_output(self):
        """Test DCM files."""
        path = os.path.join(
            Path(__file__).parent.resolve(), "fixture/data/medical/0015.DCM"
        )

        processor = get_processor(path)

        process_data = {"file": path}

        processor.valid(process_data)
        resp = processor.process(process_data)

        assert len(resp) == 1

    def test_nii_file(self):
        """Test NIfTI files."""
        processor = get_processor("../fixture/data/medical/MR_Gd.nii")

        assert isinstance(processor, NiiProcessor)

    def test_nii_valid_function(self):
        """Test NIfTI files."""
        processor = get_processor("../fixture/data/medical/MR_Gd.nii")

        try:
            processor.valid({})
        except Exception as e:
            assert isinstance(e, BadRequestError)

    def test_nii_file_output(self):
        """Test NIfTI files."""
        path = os.path.join(
            Path(__file__).parent.resolve(), "fixture/data/medical/MR_Gd.nii"
        )

        processor = get_processor(path)

        process_data = {"file": path}

        processor.valid(process_data)
        resp = processor.process(process_data)

        assert len(resp) == 3

    def test_nii_file_output_with_orientation(self):
        """Test NIfTI files."""
        path = os.path.join(
            Path(__file__).parent.resolve(), "fixture/data/medical/MR_Gd.nii"
        )

        processor = get_processor(path)

        process_data = {"file": path, "options": {"nifti_orientation": "x"}}

        processor.valid(process_data)
        resp = processor.process(process_data)

        assert len(resp) == 1
