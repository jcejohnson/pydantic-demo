"""
This is to explore lazy-loading of dict data.

The schema here is a modified version of the v0.2.0 schema.
"""

import os
import json
import pytest

from tests.lazy_model import Model


class TestLazyLoading:
    @pytest.fixture
    def expansion_base(self, resource_path_root):
        return str(resource_path_root / "expanded/root.json")

    @pytest.fixture
    def raw_data(self, expansion_base):
        with open(expansion_base) as f:
            raw_data = json.load(f)
            raw_data["$root_path"] = expansion_base
            return raw_data

    @pytest.fixture
    def model_instance(self, raw_data):
        return Model.parse_obj(raw_data)

    def test_basic_assumptions(self):

        from collections.abc import MutableMapping
        from tests.lazy_dict import LazyDict

        d = LazyDict(**{"$ref": "foo/bar"})

        # LazyDict is _not_ a dict but it _is_ a MutableMapping
        assert not isinstance(d, dict)
        assert isinstance(d, MutableMapping)

        # dicts are also MutableMappings

        d = dict()
        assert isinstance(d, MutableMapping)

        d = {}
        assert isinstance(d, MutableMapping)

    def test_basic_parse(self, expansion_base, raw_data):

        assert isinstance(raw_data, dict)
        assert "$root_path" in raw_data

        m = Model.parse_obj(raw_data)

        assert m.lazy_root == os.path.dirname(expansion_base)
        assert m.schema_version == "v0.2.0"
        assert m.actors.lazy_ref == "root/actors.json"
        assert m.movies.lazy_ref == "root/movies.json"

    def test_lazy_root(self, expansion_base, raw_data):

        m = Model.parse_obj(raw_data)

        expansion_base_dir = os.path.dirname(expansion_base)

        assert m.lazy_root == expansion_base_dir
        assert m.actors.lazy_root == expansion_base_dir
        assert m.movies.lazy_root == expansion_base_dir

    def test_lazy_actors(self, resource_path_root):

        from tests.lazy_model import ActorsById

        actors_file = str(resource_path_root / "expanded/root/actors.json")
        with open(actors_file) as f:
            actors_data = json.load(f)
            actors_data["$ref"] = os.path.dirname(actors_file)

        aid = ActorsById.parse_obj(actors_data)
        import pdb ; pdb.set_trace()


    def test_get_actor(self, model_instance):

        from collections.abc import MutableMapping
        from tests.lazy_model import Actor

        m = model_instance

        assert m.actors is not None
        assert isinstance(m.actors, MutableMapping)

        assert "charlie_chaplin" in m.actors

        charlie_chaplin = m.actors["charlie_chaplin"]
        assert charlie_chaplin

        assert isinstance(charlie_chaplin, Actor)
