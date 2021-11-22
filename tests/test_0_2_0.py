import pytest

from aktorz.model import Loader
from aktorz.model.v0_2_0 import VERSION

from .base_test import BaseVersionModuleTest


class Test_0_2_0(BaseVersionModuleTest):  # noqa: N801
    """Schema Version 0.2.0 tests."""

    # Class constants required by BaseTest

    MODEL_MODULE = "aktorz.model.v0_2_0"
    TEST_FILE = "actor-data-0.2.0.json"
    VERSION = "v0.2.0"

    def test_load_0_1_1(self, resource_path_root):

        schema_version = self.__class__.VERSION
        assert schema_version == VERSION  # Mostly to silence flake8

        loader = Loader(version=schema_version)

        test_file = resource_path_root / "actor-data-0.1.1.json"

        # We cannot load v0.1.2 data. Only v0.1.3.
        with pytest.raises(ValueError) as exc_info:
            model = loader.load(input=test_file)


    def test_load_0_1_3(self, resource_path_root):

        schema_version = self.__class__.VERSION
        assert schema_version == VERSION  # Mostly to silence flake8

        loader = Loader(version=schema_version)

        test_file = resource_path_root / "actor-data-0.1.3.json"

        model = loader.load(input=test_file)

        assert model

        # Because I'm lazy... create the initial v0.2.0 sample data from the migrated v0.1.3 data
        #
        # with open("tests/testresources/actor-data-0.2.0.json","w") as f:
        #     import json
        #     json.dump(model.dict(by_alias=True, exclude_none=True, exclude_defaults=True), f, indent='\t', sort_keys=True)

        # TODO: 
        # - Manually verify that the generated v0.2.0 data is valid (do this once so that we can use it as legit test data going forward)
        # - Load the v0.2.0 test data and compare it to the model's data