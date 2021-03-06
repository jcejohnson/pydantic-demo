from pathlib import PosixPath
from typing import Any, cast

import pytest
from pydantic import FilePath, ValidationError

# We are testing the public interface so we will import from
# the package rather than the underlying modules.
from aktorz.model import Loader
from aktorz.model.v0_1_1 import VERSION

from .base_test import BaseVersionModuleTest


class Test_0_1_1(BaseVersionModuleTest):  # noqa: N801
    """Schema Version 0.1.1 tests."""

    # Class constants required by BaseTest

    MODEL_MODULE = "aktorz.model.v0_1_1"
    TEST_FILE = "actor-data-0.1.1.json"
    VERSION = "v0.1.1"

    # Fixtures to provide copies of the raw data to each test function.

    # Tests...

    def test_character_full_name(self, request, actor_data_path: FilePath):
        """Verify that cast character name is handled properly"""

        # FIXME: Break this into several smaller tests.

        loader = Loader(version=VERSION)

        # Loader.load() returns a BaseVersionedModel.
        # That will trigger mypy when we try to get the `actors` property from it
        # since BaseVersionedModel has no such property.
        # Casting load's return value silences mypy
        model = cast(Any, loader.load(input=actor_data_path))

        # The Data:
        #    "dominic_toretto": {
        #      "actor": "vin_diesel",
        #      "first_name": "Dominic",
        #      "last_name": "Toretto"
        #    }
        assert model.actors["dwayne_johnson"].movies[0].cast["dominic_toretto"].name == "Dominic Toretto"
        assert model.actors["dwayne_johnson"].movies[0].cast["dominic_toretto"]["name"] == "Dominic Toretto"
        assert model.actors["dwayne_johnson"].movies[0].cast["dominic_toretto"].dict() == {
            "actor": "vin_diesel",
            "first_name": "Dominic",
            "last_name": "Toretto",
            "name": "Dominic Toretto",
        }

        # ####

        test_model = model.copy(deep=True)
        test_model.actors["dwayne_johnson"].movies[0].cast["mia_toretto"].last_name = None

        assert test_model.actors["dwayne_johnson"].movies[0].cast["mia_toretto"].name == "Mia Toretto"
        assert test_model.actors["dwayne_johnson"].movies[0].cast["mia_toretto"].first_name == "Mia"
        assert test_model.actors["dwayne_johnson"].movies[0].cast["mia_toretto"].last_name is None

        with pytest.raises(ValidationError) as exc_info:
            loader.load(input=test_model.json())

        self.verify_exception(request, exc_info, "a")
        assert exc_info.value.errors()[-1]["msg"] == "name [Mia Toretto] != full_name [Mia]"

        # ####

        test_model = model.copy(deep=True)
        test_model.actors["dwayne_johnson"].movies[0].cast["mia_toretto"] = {
            "actor": "jordana_brewster",
            "name": "Mia Toretto",
            "first_name": "Mia",
        }
        assert test_model.actors["dwayne_johnson"].movies[0].cast["mia_toretto"]["name"] == "Mia Toretto"
        assert test_model.actors["dwayne_johnson"].movies[0].cast["mia_toretto"]["first_name"] == "Mia"
        assert "last_name" not in test_model.actors["dwayne_johnson"].movies[0].cast["mia_toretto"]

        with pytest.raises(ValidationError) as exc_info:
            loader.load(input=test_model.json())

        self.verify_exception(request, exc_info, "a")
        assert exc_info.value.errors()[-1]["msg"] == "name [Mia Toretto] != full_name [Mia]"

        # ####

        with pytest.raises(ValidationError) as exc_info:
            # Document B:
            #     "mia_toretto": {
            #       "actor": "jordana_brewster",
            #       "name": "Mia Toretto",
            #       "last_name": "Toretto"
            #     }
            loader.load(input=PosixPath(str(actor_data_path).replace(".json", ".b.json")))

        self.verify_exception(request, exc_info, "b")
        assert exc_info.value.errors()[-1]["msg"] == "name [Mia Toretto] != full_name [Toretto]"

        # ####

        with pytest.raises(ValidationError) as exc_info:
            # Document C:
            #     "brian_oconner": {
            #       "actor": "paul_walker"
            #     }
            loader.load(input=PosixPath(str(actor_data_path).replace(".json", ".c.json")))

        self.verify_exception(request, exc_info, "c")
        assert exc_info.value.errors()[-1]["msg"] == "Either `name` or `first/last_name` must be provided."

    def test_loader_module_and_ctors(self, actor_data_dict: dict):
        """
        Verify that loader.foo() and module.foo() and Foo() all behave identically.
        """

        # Loader.load() returns a BaseVersionedModel.
        # That will trigger mypy when we try to get the `actors` property from it
        # since BaseVersionedModel has no such property.
        # Casting load's return value silences mypy
        loader = cast(Any, Loader(version=self.__class__.VERSION))

        module = loader.module  # aktorz.model.v0_1_1
        assert module.Model == loader.model

        Model = module.Model  # noqa:  N806

        assert Model(**actor_data_dict) == loader.load(input=actor_data_dict)

    # Define expected pydantic errors keyed by test name and optional qualifiers.
    # This helps reduce the noise level of each test and makes it easier to reuse
    # the expected errors.
    _expected_errors = {
        "test_character_full_name-a": [
            {
                "loc": ("actors", "dwayne_johnson", "movies"),
                "msg": "value is not a valid dict",
                "type": "type_error.dict",
            },
            {
                "loc": ("actors", "dwayne_johnson", "movies", 0, "cast", "mia_toretto", "name"),
                "msg": "name [Mia Toretto] != full_name [Mia]",
                "type": "value_error",
            },
        ],
        "test_character_full_name-b": [
            {
                "loc": ("actors", "dwayne_johnson", "movies", "cast"),
                "msg": "value is not a valid dict",
                "type": "type_error.dict",
            },
            {
                "loc": ("actors", "dwayne_johnson", "movies", 0, "cast", "mia_toretto", "name"),
                "msg": "name [Mia Toretto] != full_name [Toretto]",
                "type": "value_error",
            },
        ],
        "test_character_full_name-c": [
            {
                "loc": ("actors", "dwayne_johnson", "movies", "cast"),
                "msg": "value is not a valid dict",
                "type": "type_error.dict",
            },
            {
                "loc": ("actors", "dwayne_johnson", "movies", 0, "cast", "brian_oconner", "name"),
                "msg": "Either `name` or `first/last_name` must be provided.",
                "type": "value_error",
            },
        ],
        "test_loadable_by_0_1_0": [
            {
                "loc": ("actors", "dwayne_johnson", "movies"),
                "msg": "value is not a valid dict",
                "type": "type_error.dict",
            },
            {
                "loc": ("actors", "dwayne_johnson", "movies", 0, "cast", "brian_oconner", "first_name"),
                "msg": "extra fields not permitted",
                "type": "value_error.extra",
            },
            {
                "loc": ("actors", "dwayne_johnson", "movies", 0, "cast", "brian_oconner", "last_name"),
                "msg": "extra fields not permitted",
                "type": "value_error.extra",
            },
            {
                "loc": ("actors", "dwayne_johnson", "movies", 0, "cast", "dominic_toretto", "first_name"),
                "msg": "extra fields not permitted",
                "type": "value_error.extra",
            },
            {
                "loc": ("actors", "dwayne_johnson", "movies", 0, "cast", "dominic_toretto", "last_name"),
                "msg": "extra fields not permitted",
                "type": "value_error.extra",
            },
            {
                "loc": ("actors", "dwayne_johnson", "movies", 0, "cast", "mia_toretto", "first_name"),
                "msg": "extra fields not permitted",
                "type": "value_error.extra",
            },
            {
                "loc": ("actors", "dwayne_johnson", "movies", 0, "cast", "mia_toretto", "last_name"),
                "msg": "extra fields not permitted",
                "type": "value_error.extra",
            },
        ],
    }
