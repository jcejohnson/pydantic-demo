import importlib
from pathlib import PosixPath
from typing import Optional, Union

from pydantic import FilePath, validate_arguments, validator
from pydantic.dataclasses import dataclass

from .schema_version import SchemaVersion


@dataclass
class Loader:
    """Load data and create Models."""

    # The version of the data to be loaded and of the model created from that data.
    version: Optional[Union[SchemaVersion, str]] = None

    @validator("version")
    @classmethod
    def validate_version(cls, v):
        if isinstance(v, str):
            return SchemaVersion(v)
        return v

    def export(self, *args, **kwargs):
        """
        Construct and return an Exporter for the model.

        export() is intended as a convenience method when you want a one-use Exporter.
        It'll save you a little typing, but not much.

        loader = Loader(...)
        d_1_2_3 = loader.export(**eargs).dict({"model": model, "version": "v1.2.3"})
        j_2_3_4 = loader.export(**eargs).json({"model": model, "version": "v2.3.4"})

        ** Note that not all models can export all versions.

        """
        return self.exporter()(*args, **kwargs)

    def exporter(self):
        """
        Get the Exporter implementing implements the schema version provided to Loader().

        loader = Loader(...)
        Exporter = loader.exporter()
        exporter = Exporter(**{...})

        """
        module = self.module()
        return getattr(module, "Exporter")

    @validate_arguments
    def load(
        self,
        *,
        input: Union[str, dict, FilePath],
        verify_version: Optional[Union[bool, str]] = True,
        update_version: Optional[bool] = True,
        # TODO : Implement input_version:Optional[Union[SchemaVersion, str]] = None
    ):
        """
        Create a Model instance from the input data.

        When `input` is a dict, load() is similar to:
            loader = Loader(...)
            Model = loader.model()
            model = Model(**input)

        input : json string, dict or FilePath

        TODO: Document this properly.

        If verify_version is True
            raise ValueError if data.schema_version != self.version

        If verify_version is a str and update_version is True
            data.schema_version = self.version
        """
        return self._load(input=input, verify_version=verify_version, update_version=update_version)

    def model(self):
        """
        Get the Model implementing implements the schema version provided to Loader().

        loader = Loader(...)
        Model = loader.model()
        model = Model(**{...})
        """
        module = self.module()
        return getattr(module, "Model")

    def module(self):
        """
        Get the module containing the objects implementing the schema version provided to Loader().

        loader = Loader(...)
        module = loader.module()

        Model = module.Model
        model = Model(**{...})

        Exporter = module.Exporter
        exporter = Exporter(model=model, version=...)
        old_data = exporter.dict()
        """
        version = str(self.version.semver).replace(".", "_")
        module = importlib.import_module(f".{self.version.prefix}{version}", package=__package__)
        return module

    # #### Implementation details

    def _load(
        self,
        *,
        input: Union[str, dict, FilePath],
        verify_version: Optional[Union[bool, str]] = True,
        update_version: Optional[bool] = True,
        # TODO : Implement input_version:Optional[Union[SchemaVersion, str]] = None
    ):
        model = self.model()

        # FIXME: Simple, assumptive implementation with 100% coverage.
        input_type = type(input)
        assert input_type in [FilePath, PosixPath, dict, str]

        if input_type in [FilePath, PosixPath]:
            data = model.parse_file(input)
        elif input_type is dict:
            data = model.parse_obj(input)
        elif input_type is str:
            data = model.parse_raw(input)
        else:
            # TODO: Create a test case for this.
            raise TypeError(f"Unexpected input type {input.__class__}")

        if verify_version:
            self._verify_version(data, verify_version, update_version)

        return data

    def _verify_version(self, data, verify_version, update_version):

        # TODO: Do a real semver compatibility check.

        def m1():
            return str(data.schema_version) == str(self.version)

        def m2():
            return str(data.schema_version) == self.version.prefix + str(self.version.semver)

        if m1() or m2():
            return True

        if isinstance(verify_version, bool):
            raise ValueError(
                f"{data.schema_version} != {self.version.semver}"
                " and "
                f"{data.schema_version} != {self.version.prefix}{self.version.semver}"
            )

        # FIXME: Simple, assumptive implementation with 100% coverage.

        assert str(data.schema_version) == verify_version
        if update_version:
            data.schema_version = self.version
        return True

        # TODO: More thorough implemenation but requires more test cases.

        # if str(data.schema_version) == verify_version:
        #     if update_version:
        #         data.schema_version = self.version
        #     return True

        # raise ValueError(f"{data.schema_version} != {verify_version}")
