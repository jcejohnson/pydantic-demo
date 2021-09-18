"""
Import (load) and Export (transmute) functionality.
"""


import importlib
import json
import warnings
from enum import Enum, auto
from pathlib import Path, PosixPath
from types import ModuleType as BaseModuleType
from typing import Any, Optional, Union, cast

from pydantic import Extra, FilePath, validate_arguments, validator
from pydantic.dataclasses import dataclass

from .base_models import BaseModel, BaseVersionedModel
from .schema_version import SchemaVersion

# #### ModuleType Implementation


class ModuleType(BaseModuleType):
    """
    Teach pydantic how to validate types.ModuleType

    Class properties SchemaVersion and VERSION are also declared because
    all of our versioned Model implementation modules must provide these.
    """

    # The data type for SchemaVersion instances
    SchemaVersion = None

    # The schema version implemented by the module.
    # type(ModuleType.VERSION) == ModuleType.SchemaVersion
    VERSION = None

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        return v


# #### ImportExport Implementation


@dataclass
class ImportExport:
    """Common behaviors for import (load) and Export (transmute)."""

    version: Union[SchemaVersion, str] = cast(SchemaVersion, None)
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

        module = cast(ModuleType, values["module"])
        model = getattr(module, "Model")
        if issubclass(model, BaseVersionedModel):
            return model

        # We cannot safely coerce the Model to subclass BaseVersionedModel but we can
        # at least ensure it has the required schema_version field.
        assert "schema_version" in model.__fields__

        return model

    @classmethod
    def create(cls, *args, version=None, other=None):
        """
        Create a Loader/Exporter with either a version or another Loader/Exporter instance.
        """

        if args:
            if isinstance(args[0], str):
                version = args[0]
            elif isinstance(args[0], SchemaVersion):
                version = args[0]
            else:
                other = args[0]

        if version:
            return cls(version=SchemaVersion.create(version))

        assert issubclass(type(other), cls)
        assert other.module
        assert other.model
        assert isinstance(other.module, BaseModuleType)

        # We cannot assert that model is a BaseVersionedModel but we can assert
        # that is has a schema_version field.
        assert "schema_version" in other.model.__fields__

        if isinstance(other.model, BaseVersionedModel):
            return cls(
                version=SchemaVersion.create(other.version),
                module=cast(ModuleType, other.module),
                model=cast(BaseVersionedModel, other.model),
            )

        # If other.model is not a BaseVersionedModel then we will let the new
        # instance's validate_model_field() figure it out.
        return cls(
            version=SchemaVersion.create(other.version),
            module=cast(ModuleType, other.module),
            model=cast(BaseVersionedModel, None),
        )


# #### LoaderValidations Implementation


class LoaderValidations(Enum):
    """Ways in which Loader.load() can validate the incoming data against the Model."""

    NONE = None
    READABLE = auto()
    WRITABLE = auto()
    IDENTICAL = auto()


# #### Loader Implementation

LoaderType = None


class Loader(ImportExport):
    """Load data and create Models."""

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

    def loader(self):
        """
        Get the Loader class specific to the schema version provided to Loader().
        If the implementation module does not provide a Loader, return self.

        Used by load() before it delegates to load_input(). You generally do not
        need to invoke loader() directly.
        """

        if hasattr(self.module, "Loader"):
            loader = cast(ImportExport, getattr(self.module, "Loader"))
            return loader.create(self)

        return self

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
        input_version = raw_data["schema_version"]

        # Validate the input data against the implementation model's VERSION
        if not self.validate_version(
            input_version=SchemaVersion.create(input_version),
            validate_version=cast(LoaderValidations, validate_version),
        ):
            raise ValueError(
                f"Input schema version [{input_version}] " f"does not satisfy loader validation [{validate_version}]."
            )

        # Delegate to pydantic to create a Model from the raw data.
        data = cast(BaseModel, self.model).parse_obj(raw_data)

        if update_version:
            data["schema_version"] = self.version

        return self.make_compatible(data)

    def make_compatible(self, data: Union[BaseVersionedModel, BaseModel]) -> BaseVersionedModel:
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
            return cast(BaseVersionedModel, data)

        data.schema_version = str(schema_version)  # type: ignore

        # Models prior to v0.2.0 will not be BaseVersionedModel.
        # To may mypy happy we cast to Any.
        # Downstream code needing to deal with all models should use data['schema_version']
        # whereas cod only working with >= v0.2.0 can use data.schema_version.
        return cast(Any, data)

    def validate_version(self, *, input_version: SchemaVersion, validate_version: LoaderValidations) -> bool:
        """
        Verify that the input_version vs self.module's version satisfies `validate_version`
        """

        assert isinstance(validate_version, LoaderValidations)

        # We explicitly use the string form of the module's VERSION because its actual
        # data type is str in versions < v0.2.0 and SchemaVersion in versions >= v0.2.0
        # As with other such checks in the code, this is exactly the kind of thing this
        # demo is meant to illustrate.
        module_version = SchemaVersion.create(version=str(self.module.VERSION))

        if validate_version == LoaderValidations.NONE:
            return True

        if validate_version == LoaderValidations.IDENTICAL:
            if module_version != input_version:
                raise ValueError(
                    f"Input of version [{input_version}] does not match " f"Model version [{module_version}]."
                )

        if validate_version == LoaderValidations.READABLE:
            if not module_version.can_read(input_version):
                raise ValueError(
                    f"Input of version [{input_version}] cannot be read by " f"Model version [{module_version}]."
                )

        if validate_version == LoaderValidations.WRITABLE:
            if not module_version.can_write(input_version):
                raise ValueError(
                    f"Input of version [{input_version}] cannot be written by " f"Model version [{module_version}]."
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

# #### Exporter Implementation

ExporterType = None


class Exporter(ImportExport):
    """
    Extend pydantic's native ability to export as dict and json with the ability
    to export a Model to another compatible Model version. Subclasses of Exporter
    may extend this further to allow a Model to export itself to Model versions
    not explicitly implied by their SchemaVersion compatibility.
    """

    silence_identical_versions_warning: bool = False

    @validate_arguments
    def export(
        self,
        *,
        input: Union[BaseVersionedModel, BaseModel],
        update_version: Optional[bool] = True,
        copy_before_export: Optional[bool] = False,
    ) -> BaseVersionedModel:
        """
        Create a new Model instance from the input Model.
        Delegates to export_model() after fetching the target version's custom
        Exporter if there is one.

        These are equivalent regardless if there is or is not a custom loader:
            data = Exporter(...).export(...)
            data = Exporter(...).exporter().export(...)

        To ignore any potential custom Exporter (not recommended) you can do:
            data = Exporter(...).export_model(...)

        TODO: Document this properly.

        """
        do_export = self.export_model if (type(self) == ExporterType) else self.exporter().export_model
        return do_export(input=input, update_version=update_version)

    def exporter(self):
        """
        Get the Exporter class specific to our target version.
        If the implementation module does not provide an Exporter, return self.

        Used by export() before it delegates to export_model(). You generally do not
        need to invoke exporter() directly.
        """

        if hasattr(self.module, "Exporter"):
            exporter = cast(ImportExport, getattr(self.module, "Exporter"))
            return exporter.create(self)

        return self

    def export_model(
        self,
        *,
        input: Union[BaseVersionedModel, BaseModel],
        update_version: Optional[bool] = True,
        copy_before_export: Optional[bool] = False,
    ) -> BaseVersionedModel:
        """
        Create a Model instance from the input Model.

        Optionally updates `schema_version` in the returned Model to match self.version.

        input may be a BaseVersionedModel (v0.2.0 and beyond) or a BaseModel.
        Fortunately, BaseModel implements dict-like behavior so we can get the input model's
        schema version using `input['schema_version']` for either scenario.
        """

        input_version = input["schema_version"]

        if not self.silence_identical_versions_warning and input_version == self.version:
            warnings.warn(
                f"Using Exporter to when input and target versions are identical [{input_version}] is not recommended."
            )

        # Validate the input data against the target version
        if not self.validate_version(input_version=SchemaVersion.create(input_version)):
            raise ValueError(f"Input schema version [{input_version}] " f"cannot be exported as [{self.version}].")

        if copy_before_export:
            # There is a possibility that make_compatible() may update the dict representation
            # of the input data. Set copy_before_export if this is a concern.
            input = input.copy(deep=True)

        # Convert the input to a dict compatible with the Model for our target version.
        raw_data = self.make_compatible(input)

        # Delegate to pydantic to create a Model from the now-compatible raw data.
        # We know this will fail if the input model has fields that are not present in
        # the target model. We will tell pydantic to ignore extra fields so that we
        # don't have to explicitly list each one.
        # This is absolutely not thread safe!
        extra = BaseModel.Config.extra
        BaseModel.Config.extra = Extra.ignore
        model = self.model.parse_obj(raw_data)
        BaseModel.Config.extra = extra

        if update_version:
            # See comments in make_compatible() for why we do this version check.
            version = cast(SchemaVersion, self.version)
            if version >= SchemaVersion(prefix=version.prefix, semver="0.2.0"):
                model["schema_version"] = version
            else:
                model["schema_version"] = str(version)

        return model

    def make_compatible(self, data: Union[BaseVersionedModel, BaseModel]) -> dict:
        """
        Return a dict representation of `data` that is compatible with self.version.

        Note that thie `schema_version` element of the returned dict should be the
        same as data.schema_version. export_model() will update the final model's
        schema_version after parsing our return value if update_version is truthy.

        The caveat to this rule is if you have additional constraints on the target
        version's Model's schema_version attribute that would fail during parse_obj().
        In such a scenario the raw_dict's schema_version must be updated here in
        order to make it compatible with the target Model's parse_obj().
        """

        raw_dict = data.dict()

        # Prior to version 0.2.x the Model's schema_version was a str
        # Dealing with this fundamental and significant type change is one of the
        # things we're figuring out how to do.
        version = cast(SchemaVersion, self.version)
        if version >= SchemaVersion(prefix=version.prefix, semver="0.2.0"):
            return raw_dict

        raw_dict["schema_version"] = str(raw_dict["schema_version"])
        return raw_dict

    def validate_version(self, *, input_version: SchemaVersion) -> bool:
        """
        Verify that the input_version vs self.module's version satisfies SchemaVersion compatibility.

        Subclasses of Export may extend compatibility beyond SchemaVersion's default rules.

        For instance, va.b.c is not required to be exportable to vA.B.C where where a != A.
        Similarly, va.b.c is not required to be exportable to va.B.? where b < B.
        An Exporter subclass in the va.b.c implementation module can override validate_version()
        (and will probably need to override make_compatible()) in order to allow this.
        """

        if input_version.can_write(self.version):
            return True

        raise ValueError(f"Input of version [{input_version}] cannot be exported as [{self.version}].")

    # #### Implementation details

    def _export_raw_data(self, input):
        input_type = type(input)

        assert input_type in [FilePath, PosixPath, dict, str]

        if input_type in [FilePath, PosixPath]:
            path = cast(Path, input)
            with open(path.as_posix()) as f:
                return json.export(f)

        if input_type is dict:
            return cast(dict, input)

        if input_type is str:
            return json.exports(cast(str, input))

        # TODO: Create a test case for this.
        raise TypeError(f"Unexpected input type {input.__class__}")


# Update `ExporterType` to refer to our new Exporter class
ExporterType = Exporter
