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

        model = loader.load(input=test_file)

        assert model

    def test_load_0_1_3(self, resource_path_root):

        schema_version = self.__class__.VERSION
        assert schema_version == VERSION  # Mostly to silence flake8

        loader = Loader(version=schema_version)

        test_file = resource_path_root / "actor-data-0.1.3.json"

        model = loader.load(input=test_file)

        assert model
