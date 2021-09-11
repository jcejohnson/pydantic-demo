import importlib
from enum import Enum, auto
from pathlib import PosixPath
from types import ModuleType
from typing import Optional, Union

from pydantic import FilePath, validate_arguments, validator
from pydantic.dataclasses import dataclass

from .base_model import BaseExporter, BaseModel
from .schema_version import SchemaVersion


class Validations(Enum):
    """Ways in which Loader.load() can validate the incoming data against the Model."""

    NONE = None
    READABLE = auto()
    WRITABLE = auto()
    IDENTICAL = auto()


@dataclass
class Loader:
    """Load data and create Models."""

    """The version of the Model created.
    This also implies that the data is compatible with that Model.
    """
    version: Optional[Union[SchemaVersion, str]] = None

    @validator("version")
    @classmethod
    def validate_version(cls, v):
        if isinstance(v, str):
            return SchemaVersion(v)
        return v

    def export(self, *args, **kwargs) -> BaseExporter:
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
        Get the Exporter class which implements the schema version provided to Loader().

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
        validate_version: Optional[Validations] = Validations.READABLE,
        update_version: Optional[bool] = True,
    ) -> BaseModel:
        """
        Create a Model instance from the input data.

        When `input` is a dict, load() is similar to:
            loader = Loader(...)
            Model = loader.model()
            model = Model(**input)

        input : json string, dict or FilePath

        TODO: Document this properly.

        if validate_version is not Validations.NONE
            if data.schema_version is not valid against self.version
                raise ValueError
            if update_version is True
                data.schema_version = self.version
            else
                data.schema_version = SchemaVersion(data.schema_version)

        """
        return self._load(input=input, validate_version=validate_version, update_version=update_version)

    def model(self):
        """
        Get the Model class which implements the schema version provided to Loader().

        loader = Loader(...)
        Model = loader.model()
        model = Model(**{...})
        """
        module = self.module()
        return getattr(module, "Model")

    def module(self) -> ModuleType:
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
        self, *, input: Union[str, dict, FilePath], validate_version: Validations, update_version: bool
    ) -> BaseModel:

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

        if self._validate_version(data=data, validate_version=validate_version, update_version=update_version):
            return data

        raise ValueError(f"Input schema version [{data.schema_version}] is invalid.")

    def _validate_version(self, *, data: BaseModel, validate_version: Validations, update_version: bool) -> bool:

        # Note: validate_version() ensures that self.version is always a SchemaVersion()
        assert isinstance(self.version, SchemaVersion)
        assert isinstance(validate_version, Validations)

        if validate_version == Validations.NONE:
            return True

        data_version = data.schema_version if isinstance(
            data.schema_version, SchemaVersion) else SchemaVersion(data.schema_version)

        if validate_version == Validations.IDENTICAL:
            if self.version != data_version:
                raise ValueError(
                    f"Input of version [{data_version}] does not match Model version [{self.version}]."
                )

        if validate_version == Validations.READABLE:
            if not self.version.can_read(data_version):
                raise ValueError(
                    f"Input of version [{data_version}] cannot be read by Model version [{self.version}]."
                )

        if validate_version == Validations.WRITABLE:
            if not self.version.can_write(data_version):
                raise ValueError(
                    f"Input of version [{data_version}] cannot be written by Model version [{self.version}]."
                )

        data.schema_version = self.version if update_version else data_version

        return True
