import json

import pytest
from pydantic import FilePath

from aktorz.model import Loader, SchemaVersion  # type: ignore
from aktorz.model.schema_version import get_parts as schema_version_parts  # type: ignore


class BaseTest:
    """Schema Version 0.1.1 tests."""

    # Class constants required by BaseTest must be provided by each derived class

    MODEL_MODULE = ""
    TEST_FILE = ""
    VERSION = ""

    # Our raw test data.
    _actor_data_dict: dict = {}
    _actor_data_json: str = ""

    # Tests common to all versions

    def test_schema_version(self, schema_version):

        assert str(SemVer("1.2.3")) == "1.2.3"
        assert str(SemVer(1, minor=2, patch=3)) == "1.2.3"
        assert str(SemVer(version=1, minor=2, patch=3)) == "1.2.3"

        assert str(SchemaVersion("1.2.3")) == "v1.2.3"
        assert str(SchemaVersion("x1.2.3")) == "x1.2.3"
        assert str(SchemaVersion("ver1.2.3")) == "ver1.2.3"
        assert str(SchemaVersion(prefix="x", semver="1.2.3")) == "x1.2.3"

        parts = schema_version_parts(schema_version)
        semver = parts["semver"]
        assert str(SemVer(semver)) == semver

        assert str(SchemaVersion(schema_version)) == schema_version

        Loader(version=SchemaVersion(schema_version))
        Loader(version=schema_version).version == SchemaVersion(schema_version)

    def test_model(self, model_module, schema_version):
        """Test loading of a versioned model"""

        model = Loader(version=schema_version).model()
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
        # if not self.__class__._actor_data_dict:
        #     self.__class__._actor_data_dict = json.loads(actor_data_path.read_text())
        # return self.__class__._actor_data_dict

    @pytest.fixture
    def actor_data_json(self, actor_data_path):
        """Returns the raw (directly from the file) actor data as a json string.
        For assertions you should use test_data_json instead.
        """
        return actor_data_path.read_text()
        # if not self.__class__._actor_data_json:
        #     self.__class__._actor_data_json = actor_data_path.read_text()
        # return self.__class__._actor_data_json

    @pytest.fixture
    def test_data_dict(self, actor_data_dict):
        """Returns a normalized version of actor_data_dict."""
        return actor_data_dict

    @pytest.fixture
    def test_data_json(self, actor_data_dict):
        """Returns a normalized version of actor_data_json."""
        return json.dumps(actor_data_dict)

    # Utility methods

    def expected_errors(self, request, *other):
        key = "-".join([request.node.name, "_".join(other)]) if other else request.node.name
        return self.__class__._expected_errors[key]

    def verify_exception(self, request, exc_info, *other):
        expected_errors = self.expected_errors(request, *other)
        actual_errors = exc_info.value.errors()
        if expected_errors != actual_errors:
            pytest.fail(f"Actual errors: {actual_errors}\nExpected errors: {expected_errors}")
