import importlib
from dataclasses import dataclass
from pathlib import PosixPath
from typing import Union

from pydantic import FilePath, validate_arguments

from .schema_version import SchemaVersion


@dataclass
class Loader:

    version: SchemaVersion

    @validate_arguments
    def model(self, *, version: SchemaVersion = None):
        if not version:
            version = self.version

        module = importlib.import_module("." + str(version).replace(".", "_"), package=__package__)

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
