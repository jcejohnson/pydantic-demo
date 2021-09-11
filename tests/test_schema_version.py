
import pytest
from pydantic import BaseModel as PydanticBaseModel
from aktorz.model.base_model import BaseModel
from aktorz.model.schema_version import SchemaVersion


class Thing(BaseModel):
    version: SchemaVersion
    name: str


class TestSchemaVersion:

    def test_to_json(self):

        schema_version = SchemaVersion(prefix='v', semver='1.2.3')
        assert str(schema_version) == 'v1.2.3'
        assert issubclass(schema_version.__class__, PydanticBaseModel)
        assert isinstance(schema_version, BaseModel)

        assert SchemaVersion('v1.2.3') == schema_version

        json = schema_version.json()
        assert json == '{"prefix": "v", "semver": "1.2.3"}'

        # pydantic cannot coerce a string into a SchemaVersion
        with pytest.raises(ValueError) as exc_info:
            Thing(version='v1.2.3', name='Thing One')
        assert str(exc_info.value).endswith("value is not a valid dict (type=type_error.dict)")

        thing = Thing(version=SchemaVersion('v1.2.3'), name='Thing One')
        assert thing.version == schema_version

        json = thing.json()
