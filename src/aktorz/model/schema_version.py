import re

from semver import VersionInfo as Version  # type: ignore

from .base_model import BaseModel

DEFAULT_PREFIX = "v"

SCHEMA_VERSION_REGEX = re.compile(
    r"""
        ^
        (?P<prefix>[^\d]+)?
        (?P<semver>\d[\d\.].*)
    """,
    re.VERBOSE,
)


def get_parts(schema_version: str, default_prefix: str = DEFAULT_PREFIX):
    parts = SCHEMA_VERSION_REGEX.match(schema_version).groupdict()  # type: ignore
    prefix = parts["prefix"] or default_prefix
    semver = parts["semver"] or schema_version
    return {"prefix": prefix, "semver": semver}


class SemVer(Version):
    def __init__(self, version, **kwargs):
        if isinstance(version, str):
            super().__init__(**Version.parse(version).to_dict())
        else:
            super().__init__(version, **kwargs)

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        return v


class SchemaVersion(BaseModel):
    """Make semver.Version compatible with pydantic."""

    prefix: str = DEFAULT_PREFIX
    semver: SemVer

    def __init__(self, *args, **kwargs):
        if args and isinstance(args[0], str):
            super().__init__(**get_parts(args[0], default_prefix=DEFAULT_PREFIX))
        else:
            super().__init__(**kwargs)

    def __str__(self):
        return f"{self.prefix}{self.semver}"
