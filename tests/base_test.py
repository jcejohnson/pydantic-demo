import json
import os
import warnings

import pytest
from pydantic import FilePath, ValidationError

# We are testing the public interface so we will import from
# the package rather than the underlying modules.
from aktorz.model import Loader, SchemaVersion, SemVer


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

        schema_version = self.__class__.VERSION
        loader = Loader(version=schema_version)

        model = loader.load(input=actor_data_dict)
        json = model.json()

        with pytest.raises(ValidationError) as exc_info:
            Loader(version=v0_1_0.VERSION).load(input=json)

        self.verify_exception(request, exc_info)

    def xtest_can_export_0_1_0(self, request, actor_data_dict: dict):

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
