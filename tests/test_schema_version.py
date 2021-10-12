import pytest
from semver import VersionInfo as Version  # type: ignore

# We are testing the public interface so we will import from
# the package rather than the underlying modules.
from aktorz.model import BaseModel, SchemaVersion, SemVer


class VersionedThing(BaseModel):
    version: SchemaVersion
    name: str

    def dict(self, *args, **kwargs):
        result = super().dict(*args, **kwargs)
        result["version"] = str(self.version)
        return result


class TestSchemaVersion:
    @pytest.fixture
    def versioned_thing(self):
        return VersionedThing(version=SchemaVersion(prefix="v", semver="1.2.3"), name="Thing One")

    def test_versioned_thing(self):

        semver = SemVer(major=1, minor=2, patch=3, prerelease=None, build=None)
        semver = SemVer(version="1.2.3")

        schema_version = SchemaVersion(prefix="v", semver=semver)

        VersionedThing(version=schema_version, name="Thing One")

    def test_construction(self, versioned_thing: VersionedThing):
        # Redundant
        assert VersionedThing(version=SchemaVersion(prefix="v", semver="1.2.3"), name="Thing One") == versioned_thing

        assert VersionedThing(version=SchemaVersion(semver="1.2.3"), name="Thing One") == versioned_thing

        assert VersionedThing(version=SchemaVersion.create("v1.2.3"), name="Thing One") == versioned_thing

        assert VersionedThing(version=SchemaVersion.create("1.2.3"), name="Thing One") == versioned_thing

    def test_copy(self, versioned_thing: VersionedThing):

        new_thing = versioned_thing.copy(deep=True)
        assert new_thing == versioned_thing

        new_thing.version.prefix = "x"
        assert VersionedThing(version=SchemaVersion.create("x1.2.3"), name="Thing One") == new_thing
        assert VersionedThing(version=SchemaVersion.create("1.2.3"), name="Thing One") != new_thing

    def test_to_str(self, versioned_thing: VersionedThing):

        assert str(versioned_thing.version) == "v1.2.3"
        assert str(versioned_thing.version.prefix) == "v"
        assert str(versioned_thing.version.semver) == "1.2.3"
        assert str(versioned_thing) == "version=v1.2.3 name='Thing One'"

    def test_can_compare(self, versioned_thing: VersionedThing):

        assert versioned_thing.version.semver == Version(1, minor=2, patch=3)
        assert versioned_thing.version.semver >= Version(1, minor=2, patch=3)
        assert versioned_thing.version.semver <= Version(1, minor=2, patch=3)

        assert Version(1, minor=2, patch=3) == versioned_thing.version.semver
        assert Version(1, minor=2, patch=3) >= versioned_thing.version.semver
        assert Version(1, minor=2, patch=3) <= versioned_thing.version.semver

    def test_to_dict(self, versioned_thing: VersionedThing):

        assert isinstance(versioned_thing.version, SchemaVersion)

        data = versioned_thing.dict()
        assert data == {"version": "v1.2.3", "name": "Thing One"}

        # Verify that SchemaVersion's dict() method isn't mangling the actual version property.
        assert isinstance(versioned_thing.version, SchemaVersion)
        assert isinstance(versioned_thing.version.prefix, str)
        assert isinstance(versioned_thing.version.semver, SemVer)

        assert isinstance(data["version"], str)

    def test_to_json(self, versioned_thing: VersionedThing):

        assert versioned_thing.json() == '{"version": "v1.2.3", "name": "Thing One"}'

        # Verify that SchemaVersion's json() method isn't mangling the actual version property.
        assert isinstance(versioned_thing.version, SchemaVersion)
        assert isinstance(versioned_thing.version.prefix, str)
        assert isinstance(versioned_thing.version.semver, SemVer)

    def test_coercion(self):

        # pydantic cannot coerce a string into a SchemaVersion
        with pytest.raises(ValueError) as exc_info:
            VersionedThing(version="v1.2.3", name="VersionedThing One")
        assert exc_info.value.errors() == [
            {"loc": ("version",), "msg": "value is not a valid dict", "type": "type_error.dict"},
        ]
