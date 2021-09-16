"""
Test that all modules can read and write the things they say they can.
"""

import json
import os
import pytest

from aktorz.model import (
    BaseModel,
    Loader,
    LoaderValidations,
    SchemaVersion,
    SUPPORTED_VERSIONS
)

from .version_modules import CONFIG_DATA
import warnings

from .base_test import BaseTest, ExpectedWarning

"""
setup/teardown are a quick hack to create v0.1.2 data.
I need to extract the similar code from test_0_1_2 for reusability.
"""


def setup_module(module):
    basename = os.path.join(os.path.dirname(module.__file__), "testresources", "actor-data-0.1.")
    source = f"{basename}1.json"
    target = f"{basename}2.json"
    with open(source) as i:
        data = json.load(i)
        data["schema_version"] = 'v0.1.2'
        with open(target, "w") as o:
            json.dump(data, o)


def teardown_module(module):
    basename = os.path.join(os.path.dirname(module.__file__), "testresources", "actor-data-0.1.")
    os.remove(f"{basename}2.json")


class TestReadWrite(BaseTest):

    @pytest.fixture
    def version_modules_by_name(self):
        return CONFIG_DATA.version_modules_by_name

    @pytest.fixture
    def version_modules_by_version(self):
        return CONFIG_DATA.version_modules_by_version

    @pytest.fixture(params=CONFIG_DATA.version_modules_by_version.keys())
    def implemented_version(self, request):
        return request.param

    @pytest.fixture(params=SUPPORTED_VERSIONS)
    def supported_version(self, request):
        return request.param

    # Tests...

    def test_foo(self, implemented_version, supported_version, version_modules_by_version, resource_path_root):

        schema_version = SchemaVersion.create(implemented_version)
        assert schema_version == implemented_version

        if schema_version < supported_version:
            warnings.warn(
                f"Implementation version [{schema_version}] is not required to read/write "
                f"supported version [{supported_version}].",
                ExpectedWarning,
            )
            return

        assert schema_version.can_read(supported_version), f"[{schema_version}] can read [{supported_version}]"
        assert schema_version.can_write(supported_version), f"[{schema_version}] can write [{supported_version}]"

        # I need to rename the test data files to include the prefix.
        # Until then I'll strip it out when building the filename
        file_name = f"actor-data-{supported_version.replace('v','')}.json"
        data_path = resource_path_root / file_name
        assert os.path.exists(data_path), f"Test file [{data_path}] missing."

        loader = Loader(version=implemented_version)
        assert loader

        # Load the data into a Model.
        # Validate that the model is capable of creating output compatible with the data's version.
        # Update the schema_version in the model to match the model's version.
        model = loader.load(
            input=data_path,
            validate_version=LoaderValidations.WRITABLE,
            update_version=True
        )
        assert model

        # TODO: ask the loader to export `model` in `supported_version` format
