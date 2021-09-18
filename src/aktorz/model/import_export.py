"""
Import (load) and Export (save) functionality.
"""


import importlib
import json
from enum import Enum, auto
from pathlib import PosixPath, Path
from types import ModuleType as BaseModuleType
from typing import Optional, Union, cast

from pydantic import FilePath, validate_arguments, validator
from pydantic.dataclasses import dataclass

from .base_models import BaseModel, BaseVersionedModel
from .schema_version import SchemaVersion


class LoaderValidations(Enum):
    """Ways in which Loader.load() can validate the incoming data against the Model."""

    NONE = None
    READABLE = auto()
    WRITABLE = auto()
    IDENTICAL = auto()


class ModuleType(BaseModuleType):
    """Teach pydantic how to validate types.ModuleType"""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        return v


@dataclass
class ImportExport:
    """Common behaviors for import (load) and Export (save)."""

    version: Optional[Union[SchemaVersion, str]] = None
    module: ModuleType = cast(ModuleType, None)
    model: BaseVersionedModel = cast(BaseVersionedModel, None)

    @validator("version")
    @classmethod
    def validate_version_field(cls, v) -> SchemaVersion:
        # Adding @dataclass to Loader will cause this validator to be ignored. Why?
        if isinstance(v, str):
            return SchemaVersion.create(v)
        return v

    @validator("module")
    @classmethod
    def validate_module_field(cls, module, values) -> ModuleType:
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

        schema_version = cast(SchemaVersion, values["version"])
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

    @validator("model")
    @classmethod
    def validate_model_field(cls, model, values) -> BaseVersionedModel:
        """Get the Model class from the module."""
        return getattr(cast(ModuleType, values["module"]), "Model")


LoaderType = None


class Loader(ImportExport):
    """Load data and create Models."""

    def loader(self):
        """
        Get the Loader class specific to the schema version provided to Loader().
        If the implementation module does not provide a Loader, return self.

        Used by load() before it delegates to load_input(). You generally do not
        need to invoke loader() directly.
        """

        if hasattr(self.module, 'Loader'):
            loader = cast(ImportExport, getattr(self.module, 'Loader'))
            return loader(
                version=self.version,
                model=self.model,
                module=self.module
            )

        return self

    @validate_arguments
    def load(
        self,
        *,
        input: Union[str, dict, FilePath],
        validate_version: Optional[LoaderValidations] = LoaderValidations.READABLE,
        update_version: Optional[bool] = True,
    ) -> BaseVersionedModel:
        """
        Create a Model instance from the input data.
        Delegates to load_input() after fetching the version implementations custom
        Loader if there is one.

        These are equivalent regardless if there is or is not a custom loader:
            data = Loader(...).load(...)
            data = Loader(...).loader().load(...)

        To ignore any potential custom Loader (not recommended) you can do:
            data = Loader(...).load_input(...)

        When `input` is a dict, load() is similar to:
            loader = Loader(...)
            Model = loader.model()
            model = Model(**input)

        input : json string, dict or FilePath

        TODO: Document this properly.

        """
        do_load = self.load_input if (type(self) == LoaderType) else self.loader().load_input
        return do_load(input=input, validate_version=validate_version, update_version=update_version)

    def load_input(
        self,
        *,
        input: Union[str, dict, FilePath],
        validate_version: Optional[LoaderValidations] = LoaderValidations.READABLE,
        update_version: Optional[bool] = True,
    ) -> BaseVersionedModel:
        """
        Load input data and return a Model.

        Optionally updates `schema_version` in the returned Model to match self.version.
        """

        # Convert the input to a dict
        raw_data = self._load_raw_data(input)

        # Validate the input data against the implementation model's VERSION
        if not self.validate_version(
            input_version=SchemaVersion(raw_data['schema_version']),
            validate_version=cast(LoaderValidations, validate_version)
        ):
            raise ValueError(
                f"Input schema version [{data.schema_version}] "
                f"does not satisfy loader validation [{validate_version}]."
            )

        # Delegate to pydantic to create a Model from the raw data.
        data = cast(BaseModel, self.model).parse_obj(raw_data)

        if update_version:
            data.schema_version = self.version

        return self.make_compatible(data)

    def make_compatible(self, data: BaseVersionedModel) -> BaseVersionedModel:
        """
        Make `data` compatible with self.version.
        This may return data, update data inplace or return a new BaseVersionedModel
        instance.

        Note that this does not (and subclasses should not) update the value of
        data.schema_version. That will have been done by load_input() before it
        invokes make_compatible().
        """

        schema_version = data.schema_version  # type: ignore
        if not isinstance(schema_version, SchemaVersion):
            schema_version = SchemaVersion.create(schema_version)

        # Prior to version 0.2.x the Model's schema_version was a str
        # Dealing with this fundamental and significant type change is one of the
        # things we're figuring out how to do.
        if schema_version >= SchemaVersion(prefix=schema_version.prefix, semver="0.2.0"):
            return data

        data.schema_version = str(schema_version)  # type: ignore
        return data

    def validate_version(self, *, input_version: SchemaVersion, validate_version: LoaderValidations) -> bool:
        """
        Verify that the input_version vs self.module's version satisfies `validate_version`
        """

        assert isinstance(validate_version, LoaderValidations)

        module_version = SchemaVersion.create(self.module.VERSION)

        if validate_version == LoaderValidations.NONE:
            return True

        if validate_version == LoaderValidations.IDENTICAL:
            if module_version != input_version:
                raise ValueError(
                    f"Input of version [{input_version}] does not match "
                    f"Model version [{module_version}]."
                )

        if validate_version == LoaderValidations.READABLE:
            if not module_version.can_read(input_version):
                raise ValueError(
                    f"Input of version [{input_version}] cannot be read by "
                    f"Model version [{module_version}]."
                )

        if validate_version == LoaderValidations.WRITABLE:
            if not module_version.can_write(input_version):
                raise ValueError(
                    f"Input of version [{input_version}] cannot be written by "
                    f"Model version [{module_version}]."
                )

        return True

    # #### Implementation details

    def _load_raw_data(self, input):
        input_type = type(input)

        assert input_type in [FilePath, PosixPath, dict, str]

        if input_type in [FilePath, PosixPath]:
            path = cast(Path, input)
            with open(path.as_posix()) as f:
                return json.load(f)

        if input_type is dict:
            return cast(dict, input)

        if input_type is str:
            return json.loads(cast(str, input))

        # TODO: Create a test case for this.
        raise TypeError(f"Unexpected input type {input.__class__}")


# Update `LoaderType` to refer to our new Loader class
LoaderType = Loader


class CaCa:
    # vvv goes away

    def export(self, *args, **kwargs):
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
        if return_none_if_missing and not hasattr(self.module, "Exporter"):
            return None
        return getattr(self.module, "Exporter")

    def has_exporter(self):
        return hasattr(self.module, "Exporter")

    # ^^^^ goes away
