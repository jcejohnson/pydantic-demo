import importlib
from pathlib import PosixPath
from typing import Optional, Union

from pydantic import FilePath, validate_arguments, validator
from pydantic.dataclasses import dataclass

from .schema_version import SchemaVersion


@dataclass
class Loader:

    # The prefix is used to build the module name and when validating
    # the schema_version element.
    version_prefix: Optional[str] = "v"

    # The version must be semver compliant. (See validate_version().)
    # We prefer a SchemaVersion instance but can tolerate anything
    # SchemaVersion.parse_alt() can handle.
    version: Optional[Union[SchemaVersion, str]] = None

    @validator("version", pre=True)
    @classmethod
    def validate_version(cls, version, values):
        """
        If the version is not a SchemaVersion parse it to extract an
        optional prefix and the semver-compliant version.
        """
        if isinstance(version, SchemaVersion):
            return version
        values.update(SchemaVersion.parse_alt(version=version, **values))
        return values["version"]

    @validate_arguments
    def model(self):

        version = str(self.version).replace(".", "_")
        module = importlib.import_module(f".{self.version_prefix}{version}", package=__package__)

        return getattr(module, "Model")

    @validate_arguments
    def load(
        self,
        *,
        input: Union[str, dict, FilePath],
        verify_version: Optional[Union[bool, str]] = True,
        update_version: Optional[bool] = True,
    ):
        """
        TODO: Document properly.

        if verify_version is True
            raise ValueError if data.schema_version != self.version

        If verify_version is a str and update_version is True
            data.schema_version = self.version
        """

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
            self._verify_version(data, verify_version, update_version)

        return data

    def _verify_version(self, data, verify_version, update_version):

        # TODO: Do a real semver compatibility check.

        def m1():
            return str(data.schema_version) == str(self.version)

        def m2():
            return str(data.schema_version) == self.version_prefix + str(self.version)

        if m1() or m2():
            return True

        if isinstance(verify_version, bool):
            raise ValueError(
                f"{data.schema_version} != {self.version}"
                " and "
                f"{data.schema_version} != {self.version_prefix}{self.version}"
            )

        if str(data.schema_version) == verify_version:
            if update_version:
                data.schema_version = self.version
            return True

        raise ValueError(f"{data.schema_version} != {verify_version}")
