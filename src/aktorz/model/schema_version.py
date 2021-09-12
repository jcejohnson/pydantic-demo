import re
from typing import Union, cast

from pydantic import validator
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


class SemVer(Version):

    NONE = Version(0, 0, 0)

    def __init__(self, version, *args, **kwargs):
        if isinstance(version, Version):
            version = version.to_dict()
            version.update(kwargs)
            super().__init__(**version)
        elif isinstance(version, str) and not args and not kwargs:
            super().__init__(**Version.parse(version).to_dict())
        else:
            super().__init__(version, *args, **kwargs)

    def compare(self, other):
        if isinstance(other, Version):
            other = SemVer(other)
        return super().compare(other)

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        return v


# I had to jump through some hoops to make mypy happy but the end result
# of separating data (SchemaVersionBase) and behavior (SchemaVersion)
# was worth the effort.


class SchemaVersionBase(BaseModel):

    prefix: str = DEFAULT_PREFIX
    semver: SemVer = SemVer.NONE

    @validator("semver")
    @classmethod
    def validate_version(cls, v: str):
        if not Version.isvalid(v):
            raise ValueError(f"[{v}] is not a valid semver.")
        return str(Version.parse(v))


class SchemaVersion(SchemaVersionBase):
    """Make semver.Version compatible with pydantic.

    SchemaVersion instances are not required to (but may) be compatible if:
    - thier prefixes are not identical
    - their major values (minor if major is zero) are not identical

    See also: can_read() and can_write()
    """

    def __init__(self, *args, **kwargs):
        if args:
            if isinstance(args[0], str):
                super().__init__(
                    **self.__class__.get_parts(args[0], default_prefix=kwargs.get("default_prefix", DEFAULT_PREFIX))
                )
            elif isinstance(args[0], dict):
                super().__init__(**args[0])
        else:
            super().__init__(**kwargs)

        if not isinstance(self.semver, SemVer):
            self.semver = SemVer(self.semver)

        assert isinstance(self.prefix, str)
        assert isinstance(self.semver, SemVer)

    @classmethod
    def create(cls, v: str):
        return cls.parse_obj(cls.get_parts(schema_version=v))

    @classmethod
    def get_parts(cls, schema_version: str, default_prefix: str = DEFAULT_PREFIX):
        parts = SCHEMA_VERSION_REGEX.match(schema_version).groupdict()  # type: ignore
        prefix = parts["prefix"] or default_prefix
        semver = parts["semver"] or schema_version
        return {"prefix": prefix, "semver": semver}

    def __eq__(self, other):
        # if not isinstance(other, SchemaVersion):
        #     other = SchemaVersion(other)
        return self.prefix == other.prefix and self.semver == other.semver

    def __ge__(self, other):
        # if not isinstance(other, SchemaVersion):
        #     other = SchemaVersion(other)
        return self == other or self > other

    def __gt__(self, other):
        # if not isinstance(other, SchemaVersion):
        #     other = SchemaVersion(other)
        return self.prefix == other.prefix and self.semver >= other.semver

    def __le__(self, other):
        # if not isinstance(other, SchemaVersion):
        #     other = SchemaVersion(other)
        return self == other or self < other

    def __lt__(self, other):
        # if not isinstance(other, SchemaVersion):
        #     other = SchemaVersion(other)
        return self.prefix == other.prefix and self.semver < other.semver

    def __repr__(self) -> str:
        """So that BaseModels' using us will get our string representation during their str()."""
        return self.__str__()

    def __str__(self) -> str:
        return f"{self.prefix}{self.semver}"

    # @classmethod
    # def _get_value(cls, v: Any, **kwargs):
    #     print(f"----- [{v}] {kwargs}")
    #     return v.__str__() if v != None else None

    def can_read(self, other: Union[SchemaVersionBase, str]):
        """This SchemaVersion can read data of other's version if:
        - prefixes are identical
        - major values are identical (minor values if major is zero)
        """
        the_other = (
            self.__class__.create(cast(str, other)) if isinstance(other, str) else cast(SchemaVersionBase, other)
        )
        if self.prefix != the_other.prefix:
            return False
        if self.semver.major != the_other.semver.major:
            return False
        if (self.semver.major == 0) and (self.semver.minor != the_other.semver.minor):
            return False
        return True

    def can_write(self, other: Union[SchemaVersionBase, str]):
        """This SchemaVersion can write data of other's version if:
        - can_read
        - other.semver <= self.semver
        """
        the_other = (
            self.__class__.create(cast(str, other)) if isinstance(other, str) else cast(SchemaVersionBase, other)
        )
        if not self.can_read(the_other):
            return False
        if the_other.semver > self.semver:
            return False
        return True
