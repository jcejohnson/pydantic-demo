"""
Test that all modules can read and write the things they say they can.
"""

import json
import os

import pytest

# We are testing the public interface so we will import from
# the package rather than the underlying modules.
from aktorz.model import SUPPORTED_VERSIONS, Loader, LoaderValidations, SchemaVersion

from .base_test import BaseTest
from .version_modules import CONFIG_DATA

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
        data["schema_version"] = "v0.1.2"
        with open(target, "w") as o:
            json.dump(data, o)


def teardown_module(module):
    basename = os.path.join(os.path.dirname(module.__file__), "testresources", "actor-data-0.1.")
    os.remove(f"{basename}2.json")


def skip_incompatible_combinations(func):
    """
    A simple decorator that will only delegate if implemented_version is expected to be compatible
    with supported_version. That is, where implemented_version >= supported_version.
    """

    def filter(self, implemented_version, supported_version, version_modules_by_version, resource_path_root):

        schema_version = SchemaVersion.create(implemented_version)
        assert schema_version == implemented_version

        if schema_version >= supported_version:
            return func(self, schema_version, supported_version, version_modules_by_version, resource_path_root)

        m = (
            f"Implementation version [{schema_version}] is not required to "
            f" read/writesupported version [{supported_version}]."
        )
        # warnings.warn(m, ExpectedWarning)
        return pytest.skip(m)

    return filter


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

    @skip_incompatible_combinations
    def test_can_x(self, implemented_version, supported_version, version_modules_by_version, resource_path_root):
        """
        Verify that any SchemaVersion representing a version greater-than or equal-to some supported version
        _thinks_ that its mdel can read and write data of that supported version.

        Note that compatibility (can read/write) across major versions (or minor if major is zero) is handled
        by SchemaVersion as is compatibility based on prefixes. Those things are tested elsewhere, this test
        is only concerned with the '>=' condition.

        TL;DR - Validate the can_read/can_write methods of SchemaVersion.
        """

        iv = implemented_version
        sv = supported_version

        assert iv.can_read(sv), f"[{iv}] can read [{sv}]"
        assert iv.can_write(sv), f"[{iv}] can write [{sv}]"

    @skip_incompatible_combinations
    def test_can_read(self, implemented_version, supported_version, version_modules_by_version, resource_path_root):
        """
        For any Model having a SchemaVersion that thinks it can read data of a supported version, verify that the
        Model actually can read data of that version.
        """
        pass

    @skip_incompatible_combinations
    def test_can_write(self, implemented_version, supported_version, version_modules_by_version, resource_path_root):
        """
        For any Model having a SchemaVersion that thinks it can read data of a supported version, verify that the
        Model actually can write data of that version.
        """
        pass

    @skip_incompatible_combinations
    def test_write_read(self, implemented_version, supported_version, version_modules_by_version, resource_path_root):
        """
        Combine the two above tests to verify that when a Model's data is exported to a supported version another
        Model can read that exported data.
        """
        pass

    @skip_incompatible_combinations
    def xtest_foo(self, implemented_version, supported_version, version_modules_by_version, resource_path_root):

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
        model = loader.load(input=data_path, validate_version=LoaderValidations.WRITABLE, update_version=True)
        assert model

        # TODO: ask the loader to export `model` in `supported_version` format
