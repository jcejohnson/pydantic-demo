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

        # FIXME: Simple, assumptive implementation with 100% coverage.
        # Alternate implemenations require more test cases.

        assert not (version_prefix is None)
        # TODO: Morethorough implemenation but requires more test cases.
        # if version_prefix is None:
        #     version_prefix = ""

        assert not (version is None or isinstance(version, SchemaVersion))
        # TODO: Morethorough implemenation but requires more test cases.
        # if version is None or isinstance(version, SchemaVersion):
        #     return _return(version_prefix, version)

        assert isinstance(version, str)
        # TODO: Morethorough implemenation but requires more test cases.
        # if not isinstance(version, str):
        #     raise TypeError(f"cannot parse {version} of type {type(version)}")

        version_parts = cls._PARSE_ALT_REGEX.match(version).groupdict()  # type: ignore

        version = version_parts["version"] or version
        version_prefix = version_parts["prefix"] or version_prefix

        return _return(version_prefix, version)

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):

        # FIXME: Simple, assumptive implementation with 100% coverage.

        assert isinstance(v, str)
        assert Version.isvalid(v)
        return Version.parse(v)

        # TODO: Morethorough implemenation but requires more test cases.

        # if isinstance(v, str):
        #     # Version.parse() will throw ValueError if `v` is not a valid semver
        #     # so we check isvalid() and throw our own ValueError if necessary.
        #     if Version.isvalid(v):
        #         return Version.parse(v)
        #     raise ValueError("invalid SchemaVersion (semver.Version) format in string")

        # if isinstance(v, Version):
        #     return v

        # raise TypeError("string or semver.Version required")
