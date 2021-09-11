from pathlib import PosixPath

import pytest
from pydantic import FilePath, ValidationError

from aktorz.model import Loader  # type: ignore
from aktorz.model.v0_1_1 import VERSION  # type: ignore

from .base_test import BaseTest


class TestSchemaVersionMajor0Minor1Patch1(BaseTest):
    """Schema Version 0.1.1 tests."""

    # Class constants required by BaseTest

    MODEL_MODULE = "aktorz.model.v0_1_1"
    TEST_FILE = "actor-data-0.1.1.json"
    VERSION = "v0.1.1"

    # Fixtures to provide copies of the raw data to each test function.

    # Tests...

    # Every concrete test class needs this test to ensure that we don't
    # have typos in our constants.
    def test_constants(self, model_module, schema_version, test_file_basename):
        """
        Verify that our class constants are correctly provided by
        BaseTest's fixtures.
        """
        assert model_module == self.__class__.MODEL_MODULE
        assert schema_version == self.__class__.VERSION
        assert test_file_basename == self.__class__.TEST_FILE

        assert VERSION == self.__class__.VERSION

    def test_character_full_name(self, request, actor_data_path: FilePath):
        """Verify that cast character name is handled properly"""

        # FIXME: Break this into several smaller tests.

        loader = Loader(version=VERSION)

        model = loader.load(input=actor_data_path)
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

    def test_load_0_1_0(self, resource_path_root):
        """
        Verify that our v0.1.1 model will load a v0.1.0 document.
        """

        # Fetch our v0.1.1 loader
        loader = Loader(version=self.__class__.VERSION)

        # Construct the v0.1.0 test file path
        from .test_0_1_0 import TestSchemaVersionMajor0Minor1Patch0 as v0_1_0  # noqa:  N814

        input = resource_path_root / v0_1_0.TEST_FILE

        # Load it
        loader.load(input=input, verify_version=v0_1_0.VERSION)

    def test_loader_module_and_ctors(self, actor_data_dict: str):
        """
        Verify that loader.foo() and module.foo() and Foo() all behave identically.
        """

        loader = Loader(version=self.__class__.VERSION)

        module = loader.module()  # aktorz.model.v0_1_1
        assert module.Model == loader.model()
        assert module.Exporter == loader.exporter()

        Model = module.Model  # noqa:  N806

        assert Model(**actor_data_dict) == module.model(**actor_data_dict)
        assert Model(**actor_data_dict) == loader.model()(**actor_data_dict)
        assert Model(**actor_data_dict) == loader.load(input=actor_data_dict)

        Exporter = module.Exporter  # noqa:  N806
        eargs = {"model": Model(**actor_data_dict), "version": "v0.1.0"}

        assert Exporter(**eargs) == module.exporter(**eargs)
        assert Exporter(**eargs) == loader.exporter()(**eargs)
        assert Exporter(**eargs) == loader.export(**eargs)

    def test_loadable_by_0_1_0(self, request, actor_data_dict: str):
        """
        Attempting to load v0.1.1 data with some of the new optional properties set
        into a v0.1.0 model should fail.
        """

        schema_version = self.__class__.VERSION
        loader = Loader(version=schema_version)

        model = loader.load(input=actor_data_dict)
        json = model.json()

        from .test_0_1_0 import TestSchemaVersionMajor0Minor1Patch0 as v0_1_0  # noqa:  N814

        old_loader = Loader(version=v0_1_0.VERSION)
        with pytest.raises(ValidationError) as exc_info:
            old_model = old_loader.load(input=json)

        self.verify_exception(request, exc_info)

        # Get an aktorz.model.v0_1_1.Exporter instance
        # capable of exporting `data` in v0.1.0 format.
        exporter = loader.module().exporter(model=model, version=v0_1_0.VERSION)
        assert exporter.__module__ == "aktorz.model.v0_1_1"
        assert exporter.__class__.__name__ == "Exporter"

        # Export it as a dict
        data = exporter.dict()
        assert isinstance(data, dict)

        # Load it with the v0.1.0 loader
        old_model = old_loader.load(input=data)
        assert old_model.schema_version == v0_1_0.VERSION

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
