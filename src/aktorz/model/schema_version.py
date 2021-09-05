# semver3 uses `Version`
import re

from semver import VersionInfo as Version  # type: ignore


class SchemaVersion(Version):
    """Make semver.Version compatible with pydantic."""

    _PARSE_ALT_REGEX = re.compile(
        r"""
        ^
        (?P<prefix>[^\d*])
        (?P<version>\d.*)
        """,
        re.VERBOSE,
    )

    @classmethod
    def parse_alt(cls, version, version_prefix=None, as_dict=True):
        """
        Parse a version identifier of some alternate datatype that
        is not compatible with semver.Version.
        """

        def _return(p, v):
            return {"version_prefix": p, "version": v} if as_dict else [p, v]

        if version_prefix is None:
            version_prefix = ""

        if version is None or isinstance(version, SchemaVersion):
            return _return(version_prefix, version)

        if not isinstance(version, str):
            raise TypeError(f"cannot parse {version} of type {type(version)}")

        version_parts = cls._PARSE_ALT_REGEX.match(version).groupdict()  # type: ignore

        version = version_parts["version"] or version
        version_prefix = version_parts["prefix"] or version_prefix

        return _return(version_prefix, version)

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):

        if isinstance(v, str):
            # Version.parse() will throw ValueError if `v` is not a valid semver
            # so we check isvalid() and throw our own ValueError if necessary.
            if Version.isvalid(v):
                return Version.parse(v)
            raise ValueError("invalid SchemaVersion (semver.Version) format in string")

        if isinstance(v, Version):
            # This is redundant because there's no way to create an invalid Version.
            if v.isvalid(str(v)):
                return v
            raise ValueError("invalid SchemaVersion (semver.Version) format")

        raise TypeError("string or semver.Version required")
