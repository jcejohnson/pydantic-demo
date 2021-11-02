"""
Test that all modules can read and write the things they say they can.
"""

import json
import os
import warnings
from pathlib import Path

import pytest

from .base_test import BaseTest, ExpectedWarning
from .version_modules import CONFIG_DATA

# We are testing the public interface so we will import from
# the package rather than the underlying modules.
# isort & black fight over this one so we tell isort to skip it.
from aktorz.model import (  # isort:skip
    BaseModel,
    VersionedModelMixin,
    Exporter,
    Loader,
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

    Passes Loader instance and Path(data_path) to the wrapped function instead of `resource_path_root`
    """

    def filter(self, implemented_version, supported_version, version_modules_by_version, resource_path_root):

        schema_version = SchemaVersion.create(implemented_version)
        assert schema_version == implemented_version

        if schema_version < supported_version:
            m = (
                f"Older implementation version [{schema_version}] is not required to "
                f"read/write newer supported version [{supported_version}]."
            )
            warnings.warn(m, ExpectedWarning)
            return pytest.skip(m)

        if not schema_version.can_read(supported_version):
            m = (
                f"Implementation version [{schema_version}] reports that it cannot "
                f"read supported version [{supported_version}]."
            )
            warnings.warn(m, ExpectedWarning)
            return pytest.skip(m)

        if not schema_version.can_write(supported_version):
            m = (
                f"Implementation version [{schema_version}] reports that it cannot "
                f"write supported version [{supported_version}]."
            )
            warnings.warn(m, ExpectedWarning)
            return pytest.skip(m)

        loader = Loader(version=implemented_version)
        assert loader

        dotted_version = supported_version.replace("v", "")
        file_name = f"actor-data-{dotted_version}.json"
        data_path = Path(os.path.join(resource_path_root, file_name))
        if not data_path.exists() and "-rc" in dotted_version:
            dotted_version = dotted_version[0 : dotted_version.index("-rc")]
            file_name = f"actor-data-{dotted_version}.json"
            data_path = Path(os.path.join(resource_path_root, file_name))
        assert data_path.exists()

        return func(
            self,
            implemented_version=schema_version,
            supported_version=supported_version,
            version_modules_by_version=version_modules_by_version,
            loader=loader,
            data_path=data_path,
        )

    return filter


class TestImportExportBaseclass(BaseTest):
    def test_loader_create(self):

        version = SUPPORTED_VERSIONS[0]
        print(f"version = {version}")
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

    # Tests...

    @skip_incompatible_combinations
    def test_can_x(self, implemented_version, supported_version, version_modules_by_version, *args, **kwargs):
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
        self, implemented_version, supported_version, version_modules_by_version, loader, data_path
    ):
        """
        For any Model having a SchemaVersion that thinks it can read data of a supported version,
        verify that the Model actually can read data of that version.

        We also verify that we can serialize the data. We don't need to explicitly test writing to
        a file since that is simply json.dump().
        """

        data = loader.load(input=data_path, update_version=False)

        # Because the model may have default values not present in the input we cannot assert
        # that the raw input data and parsed model data are identical. The best we can do at
        # this level is ensure that the schema version matches what we expected to read.

        if implemented_version >= SchemaVersion(prefix="v", semver="0.2.0"):
            assert isinstance(data, VersionedModelMixin)
            assert isinstance(data.schema_version, SchemaVersion)
            assert data.schema_version == supported_version  # because update_version=False
        else:
            assert isinstance(data, BaseModel)
            assert not isinstance(data.schema_version, SchemaVersion)
            assert SchemaVersion.create(data.schema_version) == supported_version  # because update_version=False

        # Serialization to json should not throw any exceptions.
        as_json = data.json()  # Delegates to data.dict()

        # Creating a new model from the exported json should be identical to the original.
        assert loader.model.parse_raw(as_json) == data

        # Creating a deep copy will give us an identical Model that is a new instance.
        duplicate = data.copy(deep=True)
        assert duplicate == data
        assert not (duplicate is data)

    @skip_incompatible_combinations
    def test_write_read(self, implemented_version, supported_version, version_modules_by_version, loader, data_path):
        """
        Verify that a Model of can export itself into a new Model of a supported version.

        Exporter.export() does a very non-threadsafe thing to make this work!
        """

        input_data = loader.load(input=data_path, update_version=True)
        assert input_data.schema_version == implemented_version

        assert isinstance(input_data, BaseModel)
        if implemented_version >= SchemaVersion(prefix="v", semver="0.2.0"):
            assert isinstance(input_data, VersionedModelMixin)
        else:
            assert not isinstance(input_data, VersionedModelMixin)

        # If the target version is missing fields that are present in the input version
        # then those will be dropped during the export. This is as intended because the
        # exported version must be compatible with the target version.
        # Exporter does this by tweaking BaseModel.Config.extra which affects _all_
        # subclasses of BaseModel. This is extremely not threadsafe.
        exporter = Exporter(version=supported_version)

        # exporter.export() may internally create a subclass of Exporter and delegate
        # to its export_model() method. We do not have direct access to this subclass
        # instance.

        if (os.environ.get("TOX_ACTIVE", "false").upper() == "TRUE") and (implemented_version == supported_version):
            with pytest.raises(UserWarning):
                exported_data = exporter.export(input=input_data, update_version=False)
            return

        assert isinstance(input_data, (VersionedModelMixin, BaseModel))

        exported_data = exporter.export(input=input_data, update_version=False)

        assert isinstance(exported_data, BaseModel)
        if implemented_version >= SchemaVersion(prefix="v", semver="0.2.0"):
            assert isinstance(exported_data, VersionedModelMixin)
            assert isinstance(exported_data.schema_version, SchemaVersion)
            assert exported_data.schema_version == implemented_version
        else:
            # v0.1.x Model modules must provide their own Exporter
            custom_exporter = exporter.exporter()
            assert isinstance(custom_exporter, Exporter)
            assert type(custom_exporter) != Exporter
            # These mirror the v0.2.0 assertions
            assert not isinstance(exported_data, VersionedModelMixin)
            assert isinstance(exported_data.schema_version, str)
            assert SchemaVersion.create(exported_data.schema_version) == implemented_version

        # Now we use the original Loader (for the implemented version) to re-read the
        # data that we just exported to the supported version. Since exports are generally
        # newer-version-to-older-version there is a chance that the exported data will be
        # missing optional fields and that the new implemented version's Model will not be
        # identical to the original implemented version's Model (input_data).
        # Note that new required fields requires a major bump (or minor if major is zero)
        # and that skip_incompatible_combinations should filter out those scenarios.

        imported_data = loader.load(input=exported_data.dict(), update_version=True)
        assert imported_data.schema_version == implemented_version

        # There is no guarantee that input_data will be identical to the round-tripped data
        # because optional fields filter out of exported_data will now have their default values.
        # TODO : Craft a test case specifically for this scenario.
        assert imported_data.dict() == input_data.dict()
