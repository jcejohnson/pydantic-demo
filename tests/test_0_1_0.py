import copy

import pytest
from pydantic import FilePath


# We are testing the public interface so we will import from
# the package rather than the underlying modules.
from aktorz.model import Loader
from aktorz.model.v0_1_0 import VERSION

from .base_test import BaseVersionModuleTest


class Test_0_1_0(BaseVersionModuleTest):  # noqa: N801
    """Schema Version 0.1.0 tests."""

    # Class constants required by BaseTest

    MODEL_MODULE = "aktorz.model.v0_1_0"
    TEST_FILE = "actor-data-0.1.0.json"
    VERSION = "v0.1.0"

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

    def test_basic_data(self, actor_data_json: str, test_data_dict: dict):
        """
        Test loading of v0.1.0 data from a json string into the model.
        Some concrete test classes will (and some will not) have have a similar test.
        """

        schema_version = self.__class__.VERSION
        loader = Loader(version=schema_version)
        model = loader.load(input=actor_data_json)

        assert model.schema_version == schema_version
        assert isinstance(model.schema_version, str)

        assert len(model.actors) == 2
        assert model.actors["charlie_chaplin"].birth_year == 1889

    def test_version_mismatch(self, actor_data_path: FilePath):
        """
        Test failure when doc schema version mismatches.

        Note that, unlike test_load_0_1_1(), we are not violating
        any pydantic constraints before load() has a chance to
        perform its own validation.

        Also, we do not explicitly pass the validate_version=True
        parameter to load() because we want the test to fail if
        load()'s default behavior changes (indicating a breaking
        change).
        """

        schema_version = self.__class__.VERSION
        loader = Loader(version=schema_version)

        with pytest.raises(ValueError) as exc_info:
            loader.load(input='{"schema_version":"v0.9.0", "actors":{}}')

        assert str(exc_info.value) == "Input of version [v0.9.0] cannot be read by Model version [v0.1.0]."

    def test_load_0_1_1(self, request, resource_path_root):
        """
        Verify that our v0.1.0 model will fail when trying to load a v0.1.1 document.

        We should get a pydantic exception because the v0.1.1 document has
        extra fields (first_name, last_name) for the `Mia Toretto` character.

        Note that this exception comes _before_ load(verify_version=True)
        comes into play.
        """

        # Fetch our v0.1.0 loader
        loader = Loader(version=self.__class__.VERSION)

        from .test_0_1_1 import Test_0_1_1 as v0_1_1  # noqa:  N814

        with pytest.raises(ValueError) as exc_info:
            # Construct the v0.1.0 test file path
            input = resource_path_root / v0_1_1.TEST_FILE
            # Load it
            loader.load(input=input)

        self.verify_exception(request, exc_info)

    def test_mappable(self, test_data_dict: dict):
        """
        Test the ability to treat model objects as maps.
        - Reference
        - Update
        - Add (forbidden)
        - Remove
        """

        schema_version = self.__class__.VERSION
        loader = Loader(version=schema_version)
        model = loader.load(input=test_data_dict)

        # Reference

        # The model will insert default values for missing elements.
        # test_data_dict is raw data from the input file and will not
        # have these defaults until we add them here.
        # Adding the default values and mutating relevant types lets
        # us then assert that the model's dict is equivalent to the
        # input model.
        target = copy.deepcopy(test_data_dict)

        # Our model specifies that filmography is a list of tuples
        # but json.load() will give us a list of lists. Convert.

        # mypy complains about these so we silence it with the `type: ignore` comment
        #   error: Invalid index type "str" for "str"; expected type "Union[int, slice]"
        #   error: Unsupported target for indexed assignment ("str")

        assert type(model.dict()["actors"]["charlie_chaplin"]["filmography"][0]) == tuple  # type: ignore
        assert type(target["actors"]["charlie_chaplin"]["filmography"][0]) == list  # type: ignore

        for i, value in enumerate(target["actors"]["charlie_chaplin"]["filmography"]):  # type: ignore
            target["actors"]["charlie_chaplin"]["filmography"][i] = tuple(value)  # type: ignore

        target["actors"]["charlie_chaplin"]["hobbies"] = None  # type: ignore
        target["actors"]["charlie_chaplin"]["movies"]["modern_times"]["cast"] = None  # type: ignore

        target["actors"]["dwayne_johnson"]["birth_year"] = None  # type: ignore
        target["actors"]["dwayne_johnson"]["filmography"] = None  # type: ignore
        target["actors"]["dwayne_johnson"]["is_funny"] = None  # type: ignore
        target["actors"]["dwayne_johnson"]["movies"][0]["budget"] = None  # type: ignore
        target["actors"]["dwayne_johnson"]["movies"][0]["run_time_minutes"] = None  # type: ignore
        target["actors"]["dwayne_johnson"]["movies"][0]["year"] = None  # type: ignore
        target["actors"]["dwayne_johnson"]["spouses"] = None  # type: ignore

        # Now, convert the model to a dict and compare it with our direct-from-json dict.

        assert isinstance(target["schema_version"], str)
        assert target["schema_version"] == self.__class__.VERSION

        assert isinstance(model.schema_version, str)

        data = model.dict()
        assert type(data["schema_version"]) == str  # SchemaVersion
        assert data["schema_version"] == self.__class__.VERSION

        assert data == target

        # Update

        # We can also manipulate the properties as though they were dicts.
        model["actors"]["dwayne_johnson"]["movies"][0]["cast"]["dominic_toretto"]["name"] = "Toretto"
        assert model.actors["dwayne_johnson"].movies[0].cast["dominic_toretto"].name == "Toretto"

        # #### Add (forbidden)

        # But we cannot add arbitrary elements as we could with a dict.
        with pytest.raises(ValueError) as exc_info:
            model["actors"]["dwayne_johnson"]["movies"][0]["cast"]["dominic_toretto"]["nickname"] = "Toretto"
        assert str(exc_info.value) == '"CastMember" object has no field "nickname"'

        # Remove

        assert model["actors"]["dwayne_johnson"]["movies"][0]["cast"]["dominic_toretto"].pop("name") == "Toretto"
        # The mia_toretto character still has a name property
        assert model.actors["dwayne_johnson"].movies[0].cast["mia_toretto"].name == "Mia Toretto"
        # But the dominic_toretto's name has been removed
        assert "name" not in model.actors["dwayne_johnson"].movies[0].cast["dominic_toretto"]
        with pytest.raises(AttributeError) as exc_info:  # type: ignore
            assert model.actors["dwayne_johnson"].movies[0].cast["dominic_toretto"].name == "Toretto"
        assert str(exc_info.value) == "'CastMember' object has no attribute 'name'"
        # Neither of these wil throw an exception even though the dominic_toretto CastMember
        # no longer has its required `name` property.
        model["actors"]["dwayne_johnson"]["movies"][0]["cast"]["dominic_toretto"].dict()
        model["actors"]["dwayne_johnson"]["movies"][0]["cast"]["dominic_toretto"].json()

    def xtest_mappable_recursively(self, actor_data_dict: str):
        """Recursively test the ability to access model objects' properties as maps."""

        schema_version = self.__class__.VERSION
        loader = Loader(version=schema_version)
        model = loader.load(input=actor_data_dict)

        assert model.schema_version == schema_version

        assert len(model["actors"]) == 2
        assert type(model["actors"]) == dict
        assert type(model["actors"]["charlie_chaplin"]["movies"]) == dict
        assert type(model["actors"]["dwayne_johnson"]["movies"]) == list

        assert model["actors"]["charlie_chaplin"]["birth_year"] == 1889
        assert model["actors"]["charlie_chaplin"]["spouses"]["lita_grey"]["first_name"] == "Lita"

        # Brute-force recurse the model using Mappable syntax.
        self._recurse(model)

    # Helpers

    def _recurse(self, d):

        if d is None:
            return d

        if isinstance(d, list) or isinstance(d, tuple):
            return [self._recurse(v) for v in d]

        if isinstance(d, dict):
            return [self._recurse(v) for k, v in d.items()]

        return d

    _expected_errors = {
        "test_load_0_1_1": [
            {
                "loc": ("actors", "dwayne_johnson", "movies", "cast"),
                "msg": "value is not a valid dict",
                "type": "type_error.dict",
            },
            {
                "loc": ("actors", "dwayne_johnson", "movies", 0, "cast", "dominic_toretto", "name"),
                "msg": "field required",
                "type": "value_error.missing",
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
        ]
    }
