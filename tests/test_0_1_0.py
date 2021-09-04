import copy
import json
import os

import jsonref  # type: ignore
import pytest
from pydantic import FilePath

from aktorz.model import Loader


class TestSchemaVersion_0_1_0:
    """Schema Version 0.1.0 tests."""

    # Our raw test data.
    _actor_data_dict: dict = None
    _actor_data_json: json = None

    # Fixtures to provide copies of the raw data to each test function.
    @pytest.fixture
    def actor_data_path(self, resource_path_root) -> FilePath:
        """Returns a fully qualified PosixPath to the actor-data.json file"""
        return resource_path_root / "actor-data-0.1.0.json"

    @pytest.fixture
    def actor_data_dict(self, actor_data_path):
        """Returns the raw actor data as a dict."""
        if not TestSchemaVersion_0_1_0._actor_data_dict:
            TestSchemaVersion_0_1_0._actor_data_dict = json.loads(actor_data_path.read_text())
        return TestSchemaVersion_0_1_0._actor_data_dict

    @pytest.fixture
    def actor_data_json(self, actor_data_path):
        """Returns the raw (directly from the file) actor data as a json string.
        For assertions you should use test_data_json instead.
        """
        if not TestSchemaVersion_0_1_0._actor_data_json:
            TestSchemaVersion_0_1_0._actor_data_json = actor_data_path.read_text()
        return TestSchemaVersion_0_1_0._actor_data_json

    @pytest.fixture
    def test_data_dict(self, actor_data_dict):
        """Returns a normalized version of actor_data_dict."""
        return actor_data_dict

    @pytest.fixture
    def test_data_json(self, actor_data_dict):
        """Returns a normalized version of actor_data_json."""
        return json.dumps(actor_data_dict)

    # Tests...

    def test_model(self):
        """Test loading of the v0.1.0 model"""

        model = Loader(version="v0.1.0").model()
        assert model.__module__ == "aktorz.model.v0_1_0"

    def test_load_file(self, actor_data_path: FilePath):
        """Test loading of v0.1.0 data from a file into the model."""

        loader = Loader(version="v0.1.0")
        data = loader.load(input=actor_data_path)

        assert data.schema_version == "v0.1.0"

        assert len(data.actors) == 2
        assert data.actors["charlie_chaplin"].birth_year == 1889

    def test_load_dict(self, actor_data_dict: dict):
        """Test loading of v0.1.0 data from a json string into the model."""

        loader = Loader(version="v0.1.0")
        data = loader.load(input=actor_data_dict, verify_version=True)

        assert data.schema_version == "v0.1.0"

        assert len(data.actors) == 2
        assert data.actors["charlie_chaplin"].birth_year == 1889

    def test_load_string(self, actor_data_json: str, test_data_dict: str):
        """Test loading of v0.1.0 data from a json string into the model."""

        loader = Loader(version="v0.1.0")
        data = loader.load(input=actor_data_json, verify_version=True)

        assert data.schema_version == "v0.1.0"

        assert len(data.actors) == 2
        assert data.actors["charlie_chaplin"].birth_year == 1889

    def test_load_equivalence(self, actor_data_path: FilePath, actor_data_dict: dict, actor_data_json: str):
        """Verify that loading from file, dict and string give equal results."""

        loader = Loader(version="v0.1.0")

        d1 = loader.load(input=actor_data_path, verify_version=True)
        d2 = loader.load(input=actor_data_dict, verify_version=True)
        d3 = loader.load(input=actor_data_json, verify_version=True)

        assert d1 == d2
        assert d1 == d3
        assert d2 == d3

    def test_load_dict_equivalence(self, actor_data_json: str, test_data_dict: str):
        """Load the data into the model and compare against the raw file data."""

        loader = Loader(version="v0.1.0")
        data = loader.load(input=actor_data_json, verify_version=True)

        # The model will insert default values for missing elements.
        # test_data_dict is raw data from the input file and will not
        # have these defaults until we add them here.
        # Adding the default values and mutating relevant types lets
        # us then assert that the model's dict is equivalent to the
        # input data.
        target = copy.deepcopy(test_data_dict)

        # Our model specifies that filmography is a list of tuples
        # but json.load() will give us a list of lists. Convert.
        assert type(data.dict()["actors"]["charlie_chaplin"]["filmography"][0]) == tuple
        assert type(target["actors"]["charlie_chaplin"]["filmography"][0]) == list

        for i, value in enumerate(target["actors"]["charlie_chaplin"]["filmography"]):
            target["actors"]["charlie_chaplin"]["filmography"][i] = tuple(value)

        target["actors"]["charlie_chaplin"]["hobbies"] = None
        target["actors"]["charlie_chaplin"]["movies"]["modern_times"]["cast"] = None

        target["actors"]["dwayne_johnson"]["birth_year"] = None
        target["actors"]["dwayne_johnson"]["filmography"] = None
        target["actors"]["dwayne_johnson"]["is_funny"] = None
        target["actors"]["dwayne_johnson"]["movies"][0]["budget"] = None
        target["actors"]["dwayne_johnson"]["movies"][0]["run_time_minutes"] = None
        target["actors"]["dwayne_johnson"]["movies"][0]["year"] = None
        target["actors"]["dwayne_johnson"]["spouses"] = None

        assert data.dict() == target

    def test_mappable(self, actor_data_dict: str):
        """Test the ability to treat model objects as maps."""

        loader = Loader(version="v0.1.0")
        data = loader.load(input=actor_data_dict, verify_version=True)

        assert data.schema_version == "v0.1.0"

        assert len(data["actors"]) == 2
        assert type(data["actors"]) == dict
        assert type(data["actors"]["charlie_chaplin"]["movies"]) == dict
        assert type(data["actors"]["dwayne_johnson"]["movies"]) == list

        assert data["actors"]["charlie_chaplin"]["birth_year"] == 1889
        assert data["actors"]["charlie_chaplin"]["spouses"]["lita_grey"]["first_name"] == "Lita"

        # Brute-force recurse the model using Mappable syntax.
        self._recurse(data)

    def _recurse(self, d):

        if (d == None) or isinstance(d, int) or isinstance(d, str):
            return d

        if isinstance(d, list) or isinstance(d, tuple):
            return [self._recurse(v) for v in d]

        return [self._recurse(v) for k, v in d.items()]
