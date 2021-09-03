import json
import os

import jsonref  # type: ignore
import pytest

from aktorz.model import Loader


class TestSimple:
    """Test the basics."""

    # Our raw test data.
    _actor_data_json: str = None

    # Fixtures to provide copies of the raw data to each test function.

    @pytest.fixture
    def actor_data_path(self, resource_path_root):
        '''Returns a fully qualified PosixPath to the actor-data.json file'''
        return resource_path_root / "actor-data-0.1.0.json"

    @pytest.fixture
    def actor_data_json(self, actor_data_path):
        if not TestSimple._actor_data_json:
            TestSimple._actor_data_json = json.loads(actor_data_path.read_text())
        return TestSimple._actor_data_json

    @pytest.fixture
    def test_data(self, actor_data_json):
        return json.loads(json.dumps(actor_data_json))

    @pytest.fixture
    def original_data(self, actor_data_json):
        return json.loads(json.dumps(actor_data_json))

    # Tests...

    def test_equivalency(self, test_data, original_data):
        '''Assert that independent copies of the raw data are equivalent.'''
        assert test_data == original_data

    def test_model(self):
        '''Test loading of the v0.1.0 model'''

        model = Loader(version='v0.1.0').model()
        assert model.__module__ == 'aktorz.model.v0_1_0'

    def test_load(self, actor_data_path):
        '''Test loading of v0.1.0 data from a file into the model.'''

        data = Loader(version='v0.1.0').load(input_file=actor_data_path)

        assert data.schema_version == 'v0.1.0'
        assert len(data.actors) == 2
        assert data.actors['charlie_chaplin'].birth_year == 1889

    def test_loads(self, actor_data_json: str):
        '''Test loading of v0.1.0 data from a json string into the model.'''

        data = Loader(version='v0.1.0').loads(json_string=actor_data_json)

        assert data.schema_version == 'v0.1.0'
        assert len(data.actors) == 2
        assert data.actors['charlie_chaplin'].birth_year == 1889
