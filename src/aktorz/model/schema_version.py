from semver import VersionInfo as Version  # semver3 uses `Version`


class SchemaVersion(Version):
    """Make semver.Version compatible with pydantic."""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):

        if isinstance(v, str):
            if Version.isvalid(v):
                # Version.parse() will throw ValueError if `v` is not a valid semver.
                return Version.parse(v)
            raise ValueError("invalid SchemaVersion (semver.Version) format")

        if isinstance(v, Version):
            # This is redundant because there's no way to create an invalid Version.
            if v.isvalid(str(v)):
                return v
            raise ValueError("invalid SchemaVersion (semver.Version) format")

        raise TypeError("string or semver.Version required")
