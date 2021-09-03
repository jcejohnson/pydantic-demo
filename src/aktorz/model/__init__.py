
import importlib
from pydantic import (FilePath)
# from typing import (NewType)


class Loader:

    def __init__(self, *, version: str):
        self.version = version

    def model(self, *, version: str = None):
        if not version:
            version = self.version

        module = importlib.import_module('.' + version.replace('.', '_'), package=__package__)

        return module.Model

    def load(self, *, input_file: FilePath, version: str = None, verify_version: bool = True):
        model = self.model(version=version)
        data = model.parse_file(input_file)
        if verify_version:
            self._verify_version(data, version=version)
        return data

    def loads(self, *, json_string: str, version: str = None, verify_version: bool = True):
        model = self.model(version=version)
        data = model.parse_obj(json_string)
        if verify_version:
            self._verify_version(data, version=version)
        return data

    def _verify_version(self, data, *, version: str):
        if not version:
            version = self.version
        # TODO: Do a real semver compatibility check.
        assert data.schema_version == version
        is_valid = data.schema_version == version
        if not is_valid:
            raise Exception(f"{data.schema_version} != {version}")
        return is_valid
