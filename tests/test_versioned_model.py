import json
from typing import Union

import pytest
from pydantic import validator

# We are testing the public interface so we will import from
# the package rather than the underlying modules.
from aktorz.model import BaseModel, BaseVersionedModel, SchemaVersion


class VersionedThing(BaseModel):
    schema_version: Union[SchemaVersion, str]
    name: str

    @validator("schema_version", always=True)
    @classmethod
    def validate_schema_version(cls, schema_version):
        if isinstance(schema_version, SchemaVersion):
            return schema_version
        if isinstance(schema_version, str):
            return SchemaVersion.create(schema_version)
        raise TypeError("schema_version must be str or SchemaVersion")

    def dict(self, *args, **kwargs):
        result = super().dict(*args, **kwargs)
        result["schema_version"] = str(self.schema_version)
        return result


class VersionedModel(BaseVersionedModel):
    # BaseVersionedModel defines schema_version as a SchemaVersion
    # not as a Union[SchemaVersion,str] like VersionedThing above.
    name: str


class TestSchemaVersion:
    def test_export_schema(self, resource_path_root):

        # Verify that we can dump the json schema for our BaseVersionedModel subclass
        # and that it meets our expectations.

        schema = VersionedModel.schema()

        with open(resource_path_root / "test_versioned_model_schema.json") as f:
            expected_schema = json.load(f)

        assert schema == expected_schema

        # VersionedThing should also be able to dump its schema.
        # I didn't create an expectation file for this though.
        schema = VersionedThing.schema()

    @pytest.mark.parametrize("clazz", [(VersionedThing), (VersionedModel)])
    def test_versioned_model(self, clazz):

        data1 = {"schema_version": "v1.2.3", "name": "The Name"}

        model1 = clazz.parse_obj(data1)
        assert model1.schema_version == "v1.2.3"
        assert model1.name == "The Name"

        # Through the magic of pydantic field validation the input
        # string version becomes a SchemaVersion instance.
        assert type(model1.schema_version) == SchemaVersion

        # The dict() method of BaseVersionedModel converts the
        # SchemaVersion instance back to a string to keep the
        # dict and json representations simpler.
        schema_version = model1.dict()["schema_version"]
        assert isinstance(schema_version, str)
        assert schema_version == "v1.2.3"
        schema_version = json.loads(model1.json())["schema_version"]
        assert isinstance(schema_version, str)
        assert schema_version == "v1.2.3"

        data2 = {"schema_version": SchemaVersion.create("v1.2.3"), "name": "The Name"}

        model2 = clazz.parse_obj(data2)
        assert model2.schema_version == "v1.2.3"
        assert model2.name == "The Name"
        assert type(model2.schema_version) == SchemaVersion

        schema_version = model2.dict()["schema_version"]
        assert isinstance(schema_version, str)
        assert schema_version == "v1.2.3"
        schema_version = json.loads(model1.json())["schema_version"]
        assert isinstance(schema_version, str)
        assert schema_version == "v1.2.3"

        assert model1 == model2
