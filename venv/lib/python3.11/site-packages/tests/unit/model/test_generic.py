import os
import re
import unittest

from datature.utils.experimental.model.utils import verify_yaml_config


class VerifyConfig(unittest.TestCase):

    dir_path = os.path.dirname(__file__)

    def test_empty_file(self):
        with self.assertRaisesRegex(
            AssertionError, "YAML file is empty. Please provide a valid YAML file."
        ):
            config_path = os.path.join(self.dir_path, "configs/empty_file.yaml")
            verify_yaml_config(config_path)

    def test_missing_task(self):
        with self.assertRaisesRegex(
            AssertionError,
            re.compile(
                "Config field .* is missing from the YAML file. Please provide the missing field."
            ),
        ):
            config_path = os.path.join(self.dir_path, "configs/missing_task.yaml")
            verify_yaml_config(config_path)

    def test_invalid_task(self):
        with self.assertRaisesRegex(
            AssertionError,
            re.compile("Task type .* needs to be one of .*"),
        ):
            config_path = os.path.join(self.dir_path, "configs/invalid_task.yaml")
            verify_yaml_config(config_path)

    def test_missing_inputs(self):
        with self.assertRaisesRegex(
            AssertionError,
            "No input fields found in the YAML file. Please provide at least one input field.",
        ):
            config_path = os.path.join(self.dir_path, "configs/missing_inputs.yaml")
            verify_yaml_config(config_path)

    def test_missing_outputs(self):
        with self.assertRaisesRegex(
            AssertionError,
            "No output fields found in the YAML file. Please provide at least one output field.",
        ):
            config_path = os.path.join(self.dir_path, "configs/missing_outputs.yaml")
            verify_yaml_config(config_path)


if __name__ == "__main__":
    unittest.main()
