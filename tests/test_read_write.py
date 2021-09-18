"""
Test that all modules can read and write the things they say they can.
"""

import json
import os

import pytest

from .base_test import BaseTest
from .version_modules import CONFIG_DATA

# We are testing the public interface so we will import from
# the package rather than the underlying modules.
# isort & black fight over this one so we tell isort to skip it.
from aktorz.model import (  # isort:skip
    BaseModel,
    BaseVersionedModel,
    Exporter,
    Loader,
    LoaderValidations,
    SchemaVersion,
    SUPPORTED_VERSIONS,
)


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


class TestImportExportBaseclass(BaseTest):
    def test_loader_create(self):

        version = SUPPORTED_VERSIONS[0]
        Loader(version=version)
        loader = Loader(version=SchemaVersion.create(version))

        assert Loader.create(version) == loader
        assert Loader.create(SchemaVersion.create(version)) == loader
        assert Loader.create(version=version) == loader
        assert Loader.create(version=SchemaVersion.create(version)) == loader

        assert Loader.create(loader) == loader
        assert Loader.create(other=loader) == loader
        assert Loader.create(other=Loader.create(version)) == loader

    def test_exporter_create(self):

        version = SUPPORTED_VERSIONS[0]
        Exporter(version=version)
        exporter = Exporter(version=SchemaVersion.create(version))

        assert Exporter.create(version) == exporter
        assert Exporter.create(version=version) == exporter
        assert Exporter.create(version=SchemaVersion.create(version)) == exporter


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

    def get_data_path(self, supported_version: str, resource_path_root: str) -> str:
        dotted_version = supported_version.replace("v", "")
        file_name = f"actor-data-{dotted_version}.json"
        data_path = os.path.join(resource_path_root, file_name)
        return data_path

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
    def test_can_read_and_export(
        self, implemented_version, supported_version, version_modules_by_version, resource_path_root
    ):
        """
        For any Model having a SchemaVersion that thinks it can read data of a supported version,
        verify that the Model actually can read data of that version.

        We also verify that we can serialize the data. We don't need to explicitly test writing to
        a file since that is simply json.dump().
        """

        data_path = self.get_data_path(supported_version, resource_path_root)
        loader = Loader(version=implemented_version)
        data = loader.load(input=data_path, update_version=False)

        # Because the model may have default values not present in the input we cannot assert
        # that the raw input data and parsed model data are identical. The best we can do at
        # this level is ensure that the schema version matches what we expected to read.

        assert data.schema_version == supported_version

        # Serialization to json should not throw any exceptions.
        as_json = data.json()  # Delegates to data.dict()

        # Creating a new model from the exported json should be identical to the original.
        assert loader.model.parse_raw(as_json) == data

        # Creating a deep copy will give us an identical Model that is a new instance.
        duplicate = data.copy(deep=True)
        assert duplicate == data
        assert not (duplicate is data)

    @skip_incompatible_combinations
    def test_write_read(self, implemented_version, supported_version, version_modules_by_version, resource_path_root):
        """
        Combine the two above tests to verify that when a Model's data is exported to a supported version another
        Model can read that exported data.
        """

        data_path = self.get_data_path(supported_version, resource_path_root)
        loader = Loader(version=implemented_version)
        input_data = loader.load(input=data_path, update_version=True)
        assert input_data.schema_version == implemented_version

        if implemented_version >= SchemaVersion(prefix="v", semver="0.2.0"):
            assert isinstance(input_data, BaseVersionedModel)
        else:
            assert not isinstance(input_data, BaseVersionedModel)
        assert isinstance(input_data, BaseModel)

        # If the target version is missing fields that are present in the input version
        # then those will be dropped during the export. This is as intended because the
        # exported version must be compatible with the target version.
        exporter = Exporter(version=supported_version)
        exported_data = exporter.export(input=input_data, update_version=False)
        assert exported_data.schema_version == implemented_version

        # If the target version is missing fields that are present in the input version
        # then they will not be present in exported_data.
        # Note that new required fields requires a major bump (or minor if major is zero)
        # and that skip_incompatible_combinations should filter out those scenarios.

        imported_data = loader.load(input=exported_data.dict(), update_version=True)
        assert imported_data.schema_version == implemented_version

        # There is no guarantee that input_data will be identical to the round-tripped data
        # because optional fields filter out of exported_data will now have their default values.
        # TODO : Craft a test case specifically for this scenario.
        assert imported_data.dict() == input_data.dict()

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
