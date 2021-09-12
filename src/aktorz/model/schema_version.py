import re
from typing import Any, ForwardRef, Union

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


def get_parts(schema_version: str, default_prefix: str = DEFAULT_PREFIX):
    parts = SCHEMA_VERSION_REGEX.match(schema_version).groupdict()  # type: ignore
    prefix = parts["prefix"] or default_prefix
    semver = parts["semver"] or schema_version
    return {"prefix": prefix, "semver": semver}


# class SemVer(Version):
#     def __init__(self, version, **kwargs):
#         if isinstance(version, str):
#             super().__init__(**Version.parse(version).to_dict())
#         else:
#             super().__init__(version, **kwargs)

#     @classmethod
#     def __get_validators__(cls):
#         yield cls.validate

#     @classmethod
#     def validate(cls, v):
#         return v


SchemaVersion = ForwardRef("SchemaVersion")


# def _json_dumps(obj, **kwargs):
#     raise Exception(obj)
#     return str(obj)


class SchemaVersion(BaseModel):
    """Make semver.Version compatible with pydantic.

    SchemaVersion instances are not required to (but may) be compatible if:
    - thier prefixes are not identical
    - their major values (minor if major is zero) are not identical

    See also: can_read() and can_write()
    """

    prefix: str = DEFAULT_PREFIX
    semver: str = None

    @validator("semver")
    @classmethod
    def validate_version(cls, v: str):
        if not Version.isvalid(v):
            raise ValueError(f"[{v}] is not a valid semver.")
        return str(Version.parse(v))

    def __init__(self, *args, **kwargs):
        if args:
            if isinstance(args[0], str):
                super().__init__(**get_parts(args[0], default_prefix=kwargs.get('default_prefix', DEFAULT_PREFIX)))
            elif isinstance(args[0], dict):
                super().__init__(**args[0])
        else:
            super().__init__(**kwargs)

        if isinstance(self.semver, Version):
            self.semver = str(self.semver)

        assert isinstance(self.prefix, str)
        assert isinstance(self.semver, str)

    def __eq__(self, other: SchemaVersion):
        if not isinstance(other, SchemaVersion):
            other = SchemaVersion(other)
        return self.prefix == other.prefix and self.semver == other.semver

    def __repr__(self) -> str:
        """So that BaseModels' using us will get our string representation during their str()."""
        return self.__str__()

    def __str__(self) -> str:
        return f"{self.prefix}{self.semver}"

    # @classmethod
    # def _get_value(cls, v: Any, **kwargs):
    #     print(f"----- [{v}] {kwargs}")
    #     return v.__str__() if v != None else None

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

    # class Config:
    #     json_dumps = _json_dumps


SchemaVersion.update_forward_refs()
