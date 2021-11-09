import pytest

from aktorz.model import Loader

from .base_test import BaseVersionModuleTest


@pytest.mark.skip
class Test_0_2_0(BaseVersionModuleTest):  # noqa: N801
    """Schema Version 0.2.0 tests."""

    # Class constants required by BaseTest

    MODEL_MODULE = "aktorz.model.v0_2_0"
    TEST_FILE = "actor-data-0.2.0.json"
    VERSION = "v0.2.0"

    def test_load_0_1_3(self, resource_path_root):

        test_file = resource_path_root / "actor-data-0.1.3.json"

        model = Loader().load(input=test_file)

        assert model
