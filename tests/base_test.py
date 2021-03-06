import json
import os
import sys
import warnings
from typing import Any, cast

import pytest
from pydantic import FilePath, ValidationError

# We are testing the public interface so we will import from
# the package rather than the underlying modules.
from aktorz.model import Loader, SchemaVersion, SemVer

V020 = SchemaVersion.create("v0.2.0")
V030 = SchemaVersion.create("v0.3.0")

from aktorz.model import Loader

# Tell Loader where to find models
Loader.default_package = "aktorz.model"


class ExpectedWarning(Warning):
    pass


class BaseTest:

    # Setup (and tear down)

    @classmethod
    def setup_class(cls):
        # This doesn't work.
        # warnings.filterwarnings('ignore', category=ExpectedWarning)
        pass

    def setup_method(self, test_method):
        # Suppress the expected warnings when running under tox.
        if os.environ.get("TOX_ACTIVE", "false").upper() == "TRUE":
            warnings.filterwarnings("ignore", category=ExpectedWarning)

    # Utility methods

    def expected_errors(self, request, *other):
        key = "-".join([request.node.name, "_".join(other)]) if other else request.node.name
        return self.__class__._expected_errors[key]

    def verify_exception(self, request, exc_info, *other):
        expected_errors = self.expected_errors(request, *other)
        actual_errors = exc_info.value.errors()
        if expected_errors != actual_errors:
            pytest.fail(f"Actual errors: {actual_errors}\nExpected errors: {expected_errors}")


class BaseVersionModuleTest(BaseTest):

    # Class constants required by BaseTest must be provided by each derived class

    MODEL_MODULE = ""
    TEST_FILE = ""
    VERSION = ""

    # Fixtures to provide derived class constants.

    @pytest.fixture
    def model_module(self):
        return self.__class__.MODEL_MODULE

    @pytest.fixture
    def schema_version(self):
        return self.__class__.VERSION

    @pytest.fixture
    def test_file_basename(self):
        return self.__class__.TEST_FILE

    # Fixtures to provide copies of the raw data.

    @pytest.fixture
    def actor_data_path(self, resource_path_root, test_file_basename) -> FilePath:
        """Returns a fully qualified PosixPath to the actor-data.json file"""
        return resource_path_root / test_file_basename

    @pytest.fixture
    def actor_data_dict(self, actor_data_path):
        """Returns the raw actor data as a dict."""
        return json.loads(actor_data_path.read_text())

    @pytest.fixture
    def actor_data_json(self, actor_data_path):
        """Returns the raw (directly from the file) actor data as a json string.
        For assertions you should use test_data_json instead.
        """
        return actor_data_path.read_text()

    @pytest.fixture
    def test_data_dict(self, actor_data_dict):
        """Returns a normalized version of actor_data_dict."""
        return actor_data_dict

    @pytest.fixture
    def test_data_json(self, actor_data_dict):
        """Returns a normalized version of actor_data_json."""
        return json.dumps(actor_data_dict)

    # Tests common to all versions

    # Every concrete test class needs this test to ensure that we don't
    # have typos in our constants.
    def test_constants(self, model_module, schema_version, actor_data_path):
        """
        Verify that our class constants are correctly provided by
        BaseTest's fixtures.
        """

        # Verify that self.__class__.MODEL_MODULE is a legit module.
        # If this fails either self.__class__.MODEL_MODULE is incorrect or
        # the test module did not import the implementation module.
        assert model_module in sys.modules

        # This is the VERSION constant in the model implementation module.
        implemented_version = sys.modules[model_module].VERSION

        # Verify that self.__class__.VERSION matches the implementation's VERSION.
        assert schema_version == implemented_version

        # This is the VERSION imported into the test class' module
        version_under_test = sys.modules[self.__class__.__module__].VERSION

        # Be sure that the test class' VERSION matches the implementation's VERSION.
        assert version_under_test == implemented_version

        # Verify that the test data exists
        assert os.path.exists(actor_data_path)

    def test_basic_data(self, actor_data_json: str, test_data_dict: dict):
        """
        Test loading of data from a json string into the model.
        Some concrete test classes will (and some will not) have have a similar test.
        """

        schema_version = SchemaVersion.create(self.__class__.VERSION)
        loader = Loader(version=schema_version)

        # Loader.load() returns a BaseVersionedModel.
        # That will trigger mypy when we try to get the `actors` property from it
        # since BaseVersionedModel has no such property.
        # Casting load's return value silences mypy
        model = cast(Any, loader.load(input=actor_data_json))

        assert model.schema_version == schema_version

        # In v0.1.x a Model's schema_version is a string.
        # After v0.1.x, schema_version is a SchemaVersion
        if schema_version < V020:
            assert isinstance(model.schema_version, str)
        else:
            assert isinstance(model.schema_version, SchemaVersion)

        if schema_version < V020:
            # In v0.1.3 model.actors becomes an ActorsById instance
            # which is dict-like and responds to len()
            assert len(model.actors) == 2
        elif schema_version < V030:
            # In v0.2.0 model.actors is now all humans.
            assert len(model.actors) == 9
        else:
            # In v0.3.0 we replace model.actors with a list of person_id
            #   who actually are actors and add model.people to track all
            #   humans.
            assert len(model.actors) == 2
            assert len(model.people) == 9

        assert model.actors["charlie_chaplin"].birth_year == 1889

    def test_schema_version(self, schema_version):

        assert str(SemVer("1.2.3")) == "1.2.3"
        assert str(SemVer(1, minor=2, patch=3)) == "1.2.3"
        assert str(SemVer(version=1, minor=2, patch=3)) == "1.2.3"

        assert str(SchemaVersion("1.2.3")) == "v1.2.3"
        assert str(SchemaVersion("x1.2.3")) == "x1.2.3"
        assert str(SchemaVersion("ver1.2.3")) == "ver1.2.3"
        assert str(SchemaVersion(prefix="x", semver="1.2.3")) == "x1.2.3"

        parts = SchemaVersion.get_parts(schema_version)
        semver = parts["semver"]
        assert str(SemVer(semver)) == semver

        assert str(SchemaVersion(schema_version)) == schema_version

        sv = SchemaVersion(schema_version)
        Loader(version=sv)
        Loader(version=schema_version).version == SchemaVersion(schema_version)

    def test_model(self, model_module, schema_version):
        """Test loading of a versioned model"""

        model = Loader(version=schema_version).model
        assert model.__module__ == model_module

    def test_load_file(self, schema_version, actor_data_path: FilePath):
        """Test loading of versioned data from a file into the model."""

        loader = Loader(version=schema_version)
        data = loader.load(input=actor_data_path)
        assert data.schema_version == schema_version

    def test_load_dict(self, schema_version, actor_data_dict: dict):
        """Test loading of versioned data from a json string into the model."""

        loader = Loader(version=schema_version)
        data = loader.load(input=actor_data_dict)
        assert data.schema_version == schema_version

    def test_load_string(self, schema_version, actor_data_json: str, test_data_dict: str):
        """Test loading of versioned data from a json string into the model."""

        loader = Loader(version=schema_version)
        data = loader.load(input=actor_data_json)
        assert data.schema_version == schema_version

    def test_load_equivalence(
        self, schema_version, actor_data_path: FilePath, actor_data_dict: dict, actor_data_json: str
    ):
        """Verify that loading from file, dict and string give equal results."""

        loader = Loader(version=schema_version)

        d1 = loader.load(input=actor_data_path)
        d2 = loader.load(input=actor_data_dict)
        d3 = loader.load(input=actor_data_json)

        assert d1 == d2
        assert d1 == d3
        assert d2 == d3

    # TODO: Make the loadable_by/can_export tests parameterized so that they
    # test read/write/export/whetever against all versions with which they
    # should be compatible.

    def test_loadable_by_0_1_0(self, request, actor_data_dict: dict):
        """
        Attempting to load v0.1.1 data with some of the new optional properties set
        into a v0.1.0 model should fail.
        """

        from .test_0_1_0 import Test_0_1_0 as v0_1_0  # noqa:  N814

        if self.__class__.VERSION == v0_1_0.VERSION:
            warnings.warn(
                f"Not going to validate that [{self.__class__.VERSION}] is loadable by its own Model. "
                f"Skipping [{request.node.name}].",
                ExpectedWarning,
            )
            return

        schema_version = SchemaVersion.create(version=self.__class__.VERSION)
        loader = Loader(version=schema_version)

        model = loader.load(input=actor_data_dict)
        json = model.json()

        # Models after v0.1.x cannot load v0.1.0 data
        if schema_version < V020:
            with pytest.raises(ValidationError) as exc_info:
                Loader(version=SchemaVersion.create(v0_1_0.VERSION)).load(input=json)
            self.verify_exception(request, exc_info)
        else:
            with pytest.raises(ValueError) as exc_info:
                Loader(version=SchemaVersion.create(v0_1_0.VERSION)).load(input=json)

    def xtest_can_export_0_1_0(self, request, actor_data_dict: dict):
        """

        from .test_0_1_0 import Test_0_1_0 as v0_1_0  # noqa:  N814

        if self.__class__.VERSION == v0_1_0.VERSION:
            warnings.warn(
                f"Not going to validate that [{self.__class__.VERSION}] is exportable by its own Model. "
                f"Skipping [{request.node.name}].",
                ExpectedWarning,
            )
            return

        schema_version = self.__class__.VERSION
        loader = Loader(version=schema_version)
        exporter = loader.exporter(return_none_if_missing=True)
        if not exporter:
            warnings.warn(f"No Exporter available for [{schema_version}]. " f"Skipping [{request.node.name}].")
            return

        model = loader.load(input=actor_data_dict)

        # Get an Exporter instance for our Model & ask it to export to v0.1.0
        # Version modules are not required to provide an Exporter so we will
        # bail out early if none can be found.
        exporter = exporter(model=model, version=v0_1_0.VERSION)
        assert exporter.__module__ == self.__class__.MODEL_MODULE
        assert exporter.__class__.__name__ == "Exporter"

        # Export it as a dict
        data = exporter.dict()
        assert isinstance(data, dict)

        # Load it with the v0.1.0 loader
        old_loader = Loader(version=v0_1_0.VERSION)
        old_model = old_loader.load(input=data)
        assert old_model.schema_version == v0_1_0.VERSION

        """

        pass
