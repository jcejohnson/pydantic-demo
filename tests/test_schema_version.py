
import pytest
from pydantic import BaseModel as PydanticBaseModel
from aktorz.model.base_model import BaseModel
from aktorz.model.schema_version import SchemaVersion  # , _json_dumps


class VersionedThing(BaseModel):
    version: SchemaVersion
    name: str

    def dict(self, *args, **kwargs):
        result = super().dict(*args, **kwargs)
        result['version'] = str(self.version)
        return result


class Foo:
    prefix = 'v'
    semver = '3.4.5'

    def __str__(self):
        return f"{self.prefix}{self.semver}"


class TestSchemaVersion:

    def test_to_json(self):

        assert str(Foo()) == 'v3.4.5'
        # assert _json_dumps(Foo()) == 'v3.4.5'

        thing = VersionedThing(version=SchemaVersion('v1.2.3'), name='VersionedThing One')

        assert str(thing.version) == 'v1.2.3'
        # assert _json_dumps(thing.version) == 'v1.2.3'

        assert str(thing) == "version=v1.2.3 name='VersionedThing One'"

        assert thing.json() == '{"version": "v1.2.3", "name": "VersionedThing One"}'

        return

        schema_version = SchemaVersion(prefix='v', semver='1.2.3')
        assert str(schema_version) == 'v1.2.3'
        assert issubclass(schema_version.__class__, PydanticBaseModel)
        assert isinstance(schema_version, BaseModel)

        assert SchemaVersion('v1.2.3') == schema_version

        json = schema_version.json()
        assert json == '{"prefix": "v", "semver": "1.2.3"}'

        # pydantic cannot coerce a string into a SchemaVersion
        with pytest.raises(ValueError) as exc_info:
            VersionedThing(version='v1.2.3', name='VersionedThing One')
        assert str(exc_info.value).endswith("value is not a valid dict (type=type_error.dict)")

        thing = thing
        assert thing.version == schema_version

        json = thing.json()
        assert json == ''
