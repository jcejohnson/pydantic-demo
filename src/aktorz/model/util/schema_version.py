"""
This module provides extended semver support which allows for prefixed versions.
"""

import re
from typing import Union, cast

from pydantic import BaseModel as PydanticBaseModel
from pydantic import validator
from semver import VersionInfo as Version  # type: ignore

from .mixin_arbitrary_type import ArbitraryTypeMixin

__regex__ = r"""
    ^
    (?P<prefix>[^\d]+)?
    # See https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string
    (?P<semver>((?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?))
    $
"""

DEFAULT_PREFIX = "v"

VERSION_REGEX = "".join([re.sub(r"#.*", "", x).strip() for x in __regex__.split("\n")])

VERSION_PATTERN = re.compile(VERSION_REGEX, re.VERBOSE)


class SemVer(ArbitraryTypeMixin, Version):
    """
    A subclass of semver.VersionInfo providing pydantic compatibility.

    Added in 0.1.2
    """

    NONE = Version(0, 0, 0)

    def __init__(self, version=None, *args, **kwargs):
        if version is None:
            super().__init__(*args, **kwargs)
        elif isinstance(version, Version):
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


class SchemaVersionBase(PydanticBaseModel):
    """
    A subclass of BaseModel containing version prefix and semver properties.

    The properties and validator were originally a part of SchemaVersion but
    issues with mypy forced these to be extracted into SchemaVersionBase.
    This separation of concerns (data vs behavior) is actually a good thing.

    Added in v0.1.2
    """

    prefix: str = DEFAULT_PREFIX
    semver: SemVer = SemVer.NONE

    class Config:
        # json_encoders are only used by the class on which model.json() is
        # invoked. If you have a class with a SchemaVersion element, you will
        # need this same json_encoders=...
        # See mixin_versioned_model.py
        json_encoders = {SemVer: lambda v: str(v)}

    @validator("semver")
    @classmethod
    def validate_version(cls, v: Union[SemVer, str]):
        """
        This validator ensures that the semver property will always be a
        SemVer instance.
        """
        assert isinstance(v, (str, SemVer)), f"{cls}.validate_version() expected [SemVer, str] got [{type(v)}]"

        if isinstance(v, str):
            return SemVer(version=v)

        return v


class SchemaVersion(SchemaVersionBase):
    """
    Extemds SchemaVersionBase to provide semver-like functionality.

    Providers operators: = != > >= <= <

    SchemaVersion instances are not required to (but may) be compatible if:
    - thier prefixes are not identical
    - their major values (minor if major is zero) are not identical

    See also: can_read() and can_write()

    v0.1.0 : SchemaVersion(BaseModel)
    v0.1.2 : SchemaVersion(SchemaVersionBase)
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

        assert isinstance(self.prefix, str), f"SchemaVersion prefix must be a str. Got [{type(self.prefix)}]."
        assert isinstance(self.semver, SemVer), f"SchemaVersion semver must be a str. Got [{type(self.semver)}]."

    @classmethod
    def create(cls, version: Union[SchemaVersionBase, str]):
        """Create a SchemaVersion from either SchemaVersionBase or str."""
        parts = cls.get_parts(schema_version=version)
        return cls.parse_obj(parts)

    @classmethod
    def get_parts(cls, schema_version: Union[SchemaVersionBase, str], default_prefix: str = DEFAULT_PREFIX):
        """Return a dict containing the prefix and semver of a SchemaVersionBase or str."""
        if not schema_version:
            raise ValueError("get_parts(cls, schema_version=__falsy__, default_prefix={default_prefix}")
        if isinstance(schema_version, SchemaVersionBase):
            return {"prefix": schema_version.prefix, "semver": str(schema_version.semver)}
        match = VERSION_PATTERN.match(str(schema_version))
        parts = match.groupdict()  # type: ignore
        prefix = parts["prefix"] or default_prefix
        semver = parts["semver"] or schema_version
        return {"prefix": prefix, "semver": semver}

    def __eq__(self, other):
        if not isinstance(other, SchemaVersion):
            other = SchemaVersion.create(other)
        return self.prefix == other.prefix and self.semver == other.semver

    def __gt__(self, other):
        if not isinstance(other, SchemaVersion):
            other = SchemaVersion.create(other)
        return self.prefix == other.prefix and self.semver >= other.semver

    def __lt__(self, other):
        if not isinstance(other, SchemaVersion):
            other = SchemaVersion.create(other)
        return self.prefix == other.prefix and self.semver < other.semver

    def __ne__(self, other):
        return not self.__eq__(other)

    def __ge__(self, other):
        return self == other or self > other

    def __le__(self, other):
        return self == other or self < other

    def __repr__(self) -> str:
        """So that BaseModels' using us will get our string representation during their str()."""
        return self.__str__()

    def __str__(self) -> str:
        return f"{self.prefix}{self.semver}"

    # @classmethod
    # def _get_value(cls, v: Any, **kwargs):
    #     return v.__str__() if v != None else None

    def can_read(self, other: Union[SchemaVersionBase, str]):
        """
        This SchemaVersion can read data of other's version if:
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
        """
        This SchemaVersion can write data of other's version if:
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

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(
            comment=f"A string representation of {cls}. Default prefix is [{DEFAULT_PREFIX}].",
            pattern=VERSION_REGEX,
        )
