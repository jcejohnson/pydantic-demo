import importlib
from pathlib import PosixPath
from typing import Optional, Union

from pydantic import FilePath, validate_arguments, validator
from pydantic.dataclasses import dataclass

# In v0.1.x SchemaVersion was a string.
# Loader needs to support this type until v0.1.x is no longer suported
from .schema_version import SchemaVersion
from .v0_1_0 import SchemaVersion as SchemaVersionV01x


@dataclass
class Loader:

    # The prefix is used to build the module name and when validating
    # the schema_version element.
    version_prefix: Optional[str] = "v"

    # The version must be semver compliant. (See validate_version().)
    version: Optional[SchemaVersion] = None

    @validator("version", pre=True)
    @classmethod
    def validate_version(cls, version, values):
        """
        If the version is not a SchemaVersion parse it to extract an
        optional prefix and the semver-compliant version.
        """
        if not isinstance(version, SchemaVersion):
            values.update(SchemaVersion.parse_alt(version=version, **values))
            return values["version"]
        return version

    @validate_arguments
    def model(self):

        version = str(self.version).replace(".", "_")
        module = importlib.import_module(f".{self.version_prefix}{version}", package=__package__)

        return getattr(module, "Model")

    @validate_arguments
    def load(self, *, input: Union[str, dict, FilePath], verify_version: Optional[bool] = True):

        model = self.model()

        if isinstance(input, FilePath) or isinstance(input, PosixPath):
            data = model.parse_file(input)
        elif isinstance(input, dict):
            data = model.parse_obj(input)
        elif isinstance(input, str):
            data = model.parse_raw(input)
        else:
            raise TypeError(f"Unexpected input type {input.__class__}")

        if verify_version:
            self._verify_version(data)

        return data

    def _verify_version(self, data):

        # TODO: Do a real semver compatibility check.

        def m1():
            return str(data.schema_version) == str(self.version)

        def m2():
            return str(data.schema_version) == self.version_prefix + str(self.version)

        if m1() or m2():
            return True

        raise Exception(
            f"{data.schema_version} != {self.version}"
            " and "
            f"{data.schema_version} != {self.version_prefix}{self.version}"
        )
