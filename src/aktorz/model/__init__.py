
import importlib

from dataclasses import dataclass
from semver import VersionInfo as Version  # semver3 uses `Version`
from typing import Union
from pathlib import PosixPath

from pydantic import (
    FilePath,
    #
    validate_arguments
)


class SchemaVersion(Version):
    '''Make semver.Version compatible with pydantic.
    '''

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):

        if isinstance(v, str):
            if Version.isvalid(v):
                # Version.parse() will throw ValueError if `v` is not a valid semver.
                return Version.parse(v)
            raise ValueError('invalid SchemaVersion (semver.Version) format')

        if isinstance(v, Version):
            # This is redundant because there's no way to create an invalid Version.
            if v.isvalid(str(v)):
                return v
            raise ValueError('invalid SchemaVersion (semver.Version) format')

        raise TypeError('string or semver.Version required')


@dataclass
class Loader:

    version: SchemaVersion

    @validate_arguments
    def model(self, *, version: SchemaVersion = None):
        if not version:
            version = self.version

        module = importlib.import_module('.' + str(version).replace('.', '_'), package=__package__)

        return module.Model

    @validate_arguments
    def load(self, *, input: Union[str, dict, FilePath], version: SchemaVersion = None, verify_version: bool = True):
        model = self.model(version=version)
        if isinstance(input, FilePath) or isinstance(input, PosixPath):
            data = model.parse_file(input)
        elif isinstance(input, dict):
            data = model.parse_obj(input)
        elif isinstance(input, str):
            data = model.parse_raw(input)
        else:
            raise TypeError(f"Unexpected input type {input.__class__}")
        if verify_version:
            self._verify_version(data, version=version)
        return data

    def _verify_version(self, data, *, version: SchemaVersion):
        if not version:
            version = self.version
        # TODO: Do a real semver compatibility check.
        assert data.schema_version == version
        is_valid = data.schema_version == version
        if not is_valid:
            raise Exception(f"{data.schema_version} != {version}")
        return is_valid
