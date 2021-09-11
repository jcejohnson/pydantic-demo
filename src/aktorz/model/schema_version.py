import re
from typing import ForwardRef, Union

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


SchemaVersion = ForwardRef("SchemaVersion")


class SchemaVersion(BaseModel):
    """Make semver.Version compatible with pydantic.

    SchemaVersion instances are not required to (but may) be compatible if:
    - thier prefixes are not identical
    - their major values (minor if major is zero) are not identical

    See also: can_read() and can_write()
    """

    prefix: str = DEFAULT_PREFIX
    semver: SemVer

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            SemVer: lambda v: str(v),
            Version: lambda v: str(v),
        }

    def __init__(self, *args, **kwargs):
        if args:
            if isinstance(args[0], str):
                super().__init__(**get_parts(args[0], default_prefix=kwargs.get('default_prefix', DEFAULT_PREFIX)))
            elif isinstance(args[0], dict):
                super().__init__(**args[0])
        else:
            super().__init__(**kwargs)

        if not isinstance(self.semver, SemVer):
            self.semver = SemVer(self.semver)

        assert isinstance(self.prefix, str)
        assert isinstance(self.semver, SemVer)

    def __eq__(self, other: SchemaVersion):
        if not isinstance(other, SchemaVersion):
            other = SchemaVersion(other)
        return self.prefix == other.prefix and self.semver == other.semver

    def __str__(self):
        return f"{self.prefix}{self.semver}"

    def can_read(self, other: Union[SchemaVersion, str]):
        """This SchemaVersion can read data of other's version if:
        - prefixes are identical
        - major values are identical (minor values if major is zero)
        """
        if isinstance(other, str):
            other = SchemaVersion(other)
        if self.prefix != other.prefix:
            return False
        if self.semver.major != other.semver.major:
            return False
        if (self.semver.major == 0) and (self.semver.minor != other.semver.minor):
            return False
        return True

    def can_write(self, other: Union[SchemaVersion, str]):
        """This SchemaVersion can write data of other's version if:
        - can_read
        - other.semver <= self.semver
        """
        if isinstance(other, str):
            other = SchemaVersion(other)
        if not self.can_read(other):
            return False
        if other.semver > self.semver:
            return False
        return True


SchemaVersion.update_forward_refs()
