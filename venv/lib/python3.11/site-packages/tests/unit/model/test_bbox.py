import os
import re
import unittest

from datature.utils.experimental.model.utils import verify_yaml_config


class VerifyConfig(unittest.TestCase):

    dir_path = os.path.dirname(__file__)

    def test_missing_input_field(self):
        with self.assertRaisesRegex(
            AssertionError,
            re.compile(
                "Input field .* is missing from the YAML file. Please provide the missing field."
            ),
        ):
            config_path = os.path.join(
                self.dir_path, "configs/bbox/missing_input_field.yaml"
            )
            verify_yaml_config(config_path)

    def test_missing_output_field(self):
        with self.assertRaisesRegex(
            AssertionError,
            re.compile(
                "Output field .* is missing from the YAML file. Please provide the missing field."
            ),
        ):
            config_path = os.path.join(
                self.dir_path, "configs/bbox/missing_output_field.yaml"
            )
            verify_yaml_config(config_path)

    def test_invalid_input_format(self):
        with self.assertRaisesRegex(
            AssertionError,
            re.compile("Input format .* needs to be one of .*"),
        ):
            config_path = os.path.join(
                self.dir_path, "configs/bbox/invalid_input_format.yaml"
            )
            verify_yaml_config(config_path)

    def test_invalid_output_format(self):
        with self.assertRaisesRegex(
            AssertionError,
            re.compile("Output format .* needs to be one of .*"),
        ):
            config_path = os.path.join(
                self.dir_path, "configs/bbox/invalid_output_format.yaml"
            )
            verify_yaml_config(config_path)

    def test_pristine(self):
        config_path = os.path.join(self.dir_path, "configs/bbox/pristine.yaml")
        verify_yaml_config(config_path)


if __name__ == "__main__":
    unittest.main()
