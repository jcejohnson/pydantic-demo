import importlib
from enum import Enum, auto
from pathlib import PosixPath
from types import ModuleType
from typing import Optional, Union, cast

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
        Raises AttributeError if there is no Exporter for the version.

        export() is intended as a convenience method when you want a one-use Exporter.
        It'll save you a little typing, but not much.

        loader = Loader(...)
        d_1_2_3 = loader.export(**eargs).dict({"model": model, "version": "v1.2.3"})
        j_2_3_4 = loader.export(**eargs).json({"model": model, "version": "v2.3.4"})

        ** Note that not all models can export all versions.

        """
        return self.exporter()(*args, **kwargs)

    def exporter(self, return_none_if_missing: Optional[bool] = False):
        """
        Get the Exporter class which implements the schema version provided to Loader().
        Raises AttributeError if there is no Exporter for the version.
        See also: has_exporter()

        loader = Loader(...)
        Exporter = loader.exporter()
        exporter = Exporter(**{...})

        """
        module = self.module()
        if return_none_if_missing and not hasattr(module, "Exporter"):
            return None
        return getattr(module, "Exporter")

    def has_exporter(self):
        module = self.module()
        return hasattr(module, "Exporter")

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
        See also: has_exporter()

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

        schema_version = cast(SchemaVersion, self.version)
        version = str(schema_version.semver).replace(".", "_")
        try:
            module = importlib.import_module(f".{schema_version.prefix}{version}", package=__package__)
        except ModuleNotFoundError as e1:
            final_version = str(schema_version.semver.finalize_version()).replace(".", "_")
            if final_version == version:
                raise e1
            try:
                module = importlib.import_module(f".{schema_version.prefix}{final_version}", package=__package__)
            except ModuleNotFoundError as e2:
                raise ModuleNotFoundError(f"{e1} / {e2}")

        return module

    # #### Implementation details

    def _load(
        self,
        *,
        input: Union[str, dict, FilePath],
        validate_version: Optional[Validations] = Validations.READABLE,
        update_version: Optional[bool] = True,
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

        if self._validate_version(
            data=data, validate_version=cast(Validations, validate_version), update_version=cast(bool, update_version)
        ):
            return self._make_compatible(data)

        raise ValueError(f"Input schema version [{data.schema_version}] is invalid.")

    def _make_compatible(self, data: BaseModel) -> BaseModel:
        # Prior to version 0.2.x the Model's schema_version was a str
        # Dealing with this fundamental and significant type change is one of the
        # things we're figuring out how to do.

        schema_version = data.schema_version  # type: ignore
        if not isinstance(schema_version, SchemaVersion):
            data = SchemaVersion.create(schema_version)

        if schema_version >= SchemaVersion(prefix=schema_version.prefix, semver="0.2.0"):
            return data

        data.schema_version = str(schema_version)  # type: ignore
        return data

    def _validate_version(self, *, data: BaseModel, validate_version: Validations, update_version: bool) -> bool:
        """
        if validate_version == Validations.NONE and update_version
            data.schema_version = self.version (which is a SchemaVersion)
        """

        # Note: validate_version() ensures that self.version is always a SchemaVersion()
        assert isinstance(self.version, SchemaVersion)
        assert isinstance(validate_version, Validations)

        if validate_version == Validations.NONE:
            return True

        schema_version = data.schema_version  # type: ignore

        data_version = (
            schema_version if isinstance(schema_version, SchemaVersion) else SchemaVersion.create(schema_version)
        )

        if validate_version == Validations.IDENTICAL:
            if self.version != data_version:
                raise ValueError(f"Input of version [{data_version}] does not match Model version [{self.version}].")

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

        data.schema_version = self.version if update_version else data_version  # type: ignore

        return True
