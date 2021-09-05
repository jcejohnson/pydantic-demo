from pathlib import PosixPath

import pytest
from pydantic import FilePath, ValidationError

from aktorz.model import Loader
from aktorz.model.v0_1_1 import VERSION

from .base_test import BaseTest


class TestSchemaVersionMajor0Minor1Patch1(BaseTest):
    """Schema Version 0.1.1 tests."""

    # Class constants required by BaseTest

    MODEL_MODULE = "aktorz.model.v0_1_1"
    TEST_FILE = "actor-data-0.1.1.json"
    VERSION = "v0.1.1"

    # Fixtures to provide copies of the raw data to each test function.

    # Tests...

    # Every concrete test class needs this test to ensure that we don't
    # have typos in our constants.
    def test_constants(self, model_module, schema_version, test_file_basename):
        """
        Verify that our class constants are correctly provided by
        BaseTest's fixtures.
        """
        assert model_module == self.__class__.MODEL_MODULE
        assert schema_version == self.__class__.VERSION
        assert test_file_basename == self.__class__.TEST_FILE

        assert VERSION == self.__class__.VERSION

    def test_character_full_name(self, actor_data_path: FilePath):
        """Verify that attempting to parse a badly formed character fails as expected."""

        loader = Loader(version=VERSION)

        with pytest.raises(ValidationError) as exc_info:
            # Document A:
            #     "mia_toretto": {
            #       "actor": "jordana_brewster",
            #       "name": "Mia Toretto",
            #       "first_name": "Mia"
            #     }
            loader.load(input=PosixPath(str(actor_data_path).replace(".json", ".a.json")))

        expected_errors = [
            {
                "loc": ("actors", "dwayne_johnson", "movies", "cast"),
                "msg": "value is not a valid dict",
                "type": "type_error.dict",
            },
            {
                "loc": ("actors", "dwayne_johnson", "movies", 0, "cast", "mia_toretto", "name"),
                "msg": "name [Mia Toretto] != full_name [Mia]",
                "type": "value_error",
            },
        ]
        actual_errors = exc_info.value.errors()
        if expected_errors != actual_errors:
            pytest.fail(f"Actual errors: {actual_errors}\nExpected errors: {expected_errors}")

        with pytest.raises(ValidationError) as exc_info:
            # Document B:
            #     "mia_toretto": {
            #       "actor": "jordana_brewster",
            #       "name": "Mia Toretto",
            #       "last_name": "Toretto"
            #     }
            loader.load(input=PosixPath(str(actor_data_path).replace(".json", ".b.json")))

        expected_errors = [
            {
                "loc": ("actors", "dwayne_johnson", "movies", "cast"),
                "msg": "value is not a valid dict",
                "type": "type_error.dict",
            },
            {
                "loc": ("actors", "dwayne_johnson", "movies", 0, "cast", "mia_toretto", "name"),
                "msg": "name [Mia Toretto] != full_name [Toretto]",
                "type": "value_error",
            },
        ]
        actual_errors = exc_info.value.errors()
        if expected_errors != actual_errors:
            pytest.fail(f"Actual errors: {actual_errors}\nExpected errors: {expected_errors}")

    def test_load_0_1_0(self, resource_path_root):
        """
        Verify that our v0.1.1 model will load a v0.1.0 document.
        """

        # Fetch our v0.1.1 loader
        loader = Loader(version=self.__class__.VERSION)

        # Construct the v0.1.0 test file path
        from .test_0_1_0 import TestSchemaVersionMajor0Minor1Patch0 as v0_1_0  # noqa:  N814

        input = resource_path_root / v0_1_0.TEST_FILE

        # Load it
        loader.load(input=input, verify_version=v0_1_0.VERSION)
