"""
Import (load) and Export (transmute) functionality.
"""


import importlib
import json
import warnings
from enum import Enum, auto
from pathlib import Path, PosixPath
from types import ModuleType as BaseModuleType
from typing import TYPE_CHECKING, Optional, Union, cast, Any

from pydantic import Extra, FilePath, MissingError, validate_arguments, validator
from pydantic.dataclasses import dataclass

if TYPE_CHECKING:
    from pydantic.typing import AbstractSetIntStr, MappingIntStrAny

from .base_model import BaseModel
from .base_versioned_model import BaseVersionedModel
from .mixin_arbitrary_type import ArbitraryTypeMixin
from .schema_version import SchemaVersion

# #### ModuleType Implementation


class ModuleType(ArbitraryTypeMixin, BaseModuleType):
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


# #### ImportExport Implementation


@dataclass
class ImportExport:
    """Common behaviors for import (load) and Export (transmute)."""

    # WARNING: The order of fields is important for proper validation.

    # The Model field identifying the version implemented by the Model.
    schema_version_field: str = "schema_version"

    # The Model version this instance (e.g. - Loader) will provide.
    version: Union[SchemaVersion, str] = cast(SchemaVersion, None)

    # The package containing the module.
    package: Optional[str] = None

    # The module containing the Model.
    module: Optional[ModuleType] = None

    # The Model implementing `version`.
    # May be versioned or unversioned.
    model: Optional[BaseModel] = None

    # Populated by subclasses as necessary

    # SchemaVersion.create(self.module.VERSION)
    module_version: SchemaVersion = None

    @validator("version")
    @classmethod
    def validate_version_field(cls, v: Union[SchemaVersion, str]) -> SchemaVersion:
        # Adding @dataclass to Loader will cause this validator to be ignored. Why?
        if isinstance(v, str):
            return SchemaVersion.create(v)
        if isinstance(v, SchemaVersion):
            return v
        raise TypeError(f"ImportExport.validate_version_field() expected type [SchemaVersion, str] got [{type(v)}]")

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

        if "version" not in values:
            raise MissingError(f"Missing `version` field on {cls} instance.")

        # Get the value of the version field from the cls instance (e.g. - a Loader instance)
        schema_version = cast(SchemaVersion, values["version"])
        version = str(schema_version.semver).replace(".", "_")

        # If no package was provided, assume that the Model implementation is in the same
        # module as the Loader.
        model_package = values.get("package", None)
        if not model_package:
            if hasattr(cls, "default_package"):
                model_package = getattr(cls, "default_package")
            else:
                model_package = importlib.import_module(cls.__module__).__package__

        try:
            module = importlib.import_module(f".{schema_version.prefix}{version}", package=model_package)
        except ModuleNotFoundError as e1:
            final_version = str(schema_version.semver.finalize_version()).replace(".", "_")
            if final_version == version:
                raise e1
            try:
                module = importlib.import_module(f".{schema_version.prefix}{final_version}", package=model_package)
            except ModuleNotFoundError as e2:
                raise ModuleNotFoundError(f"{e1} / {e2}")
        except Exception as e:
            raise Exception(e)  #

        if hasattr(module, "SCHEMA_VERSION_FIELD"):
            values["schema_version_field"] = getattr(module, "SCHEMA_VERSION_FIELD")

        return module

    @validator("model")
    @classmethod
    def validate_model_field(cls, model, values) -> BaseVersionedModel:
        """Get the Model class from the module."""

        if "module" not in values:
            raise MissingError(f"Missing `module` field on {cls} instance.")

        model = getattr(values["module"], "Model")
        if issubclass(model, BaseVersionedModel):
            return model

        assert issubclass(model, BaseModel), f"{type(model)} does not subclass BaseModel"

        # We cannot safely coerce the Model to subclass BaseVersionedModel but we can
        # at least ensure it has an attribute telling us which of its fields represent
        # the schema version.
        assert "schema_version_field" in values, "No [schema_version_field] attribute."
        assert values["schema_version_field"], "No value for [schema_version_field]."

        # assert getattr(
        #     model, values["schema_version_field"]
        # ), f"Model type [{model.__class__}] missing [{values['schema_version_field']}] attribute."

        return model

    @classmethod
    def create(cls, *, version):
        """
        Extension point for creating Loader and Exporter subclass instances.
        """

        return cls(version=SchemaVersion.create(version))

    def get_schema_version(self, model: Union[BaseModel, dict]) -> SchemaVersion:
        """
        Get the schema version of an input Model that is to be exported.
        """

        if not model:
            raise ValueError("get_schema_version(__falsy__)")

        # Avoid mypy complaint by using getattr()
        #   Value of type "Union[BaseVersionedModel, Dict[Any, Any]]" is not indexable
        schema_version = getattr(model, "get")(self.schema_version_field)

        if isinstance(model, dict):
            return SchemaVersion.create(schema_version)

        if isinstance(schema_version, SchemaVersion):
            return schema_version

        return SchemaVersion.create(schema_version)

    def set_schema_version(self, model):
        """
        Set the version in a Model created by export_model()
        """
        model[self.schema_version_field] = self.version


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

    # I would like to use @validate_arguments here but that has the nasty side-effect
    # of casting `input` to the wrong type if, for instance, it is a BaseModel.
    def load(
        self,
        *,
        input: Union[str, dict, Path],
        validate_version: Optional[LoaderValidations] = LoaderValidations.READABLE,
        update_version: Optional[bool] = True,
    ) -> BaseVersionedModel:
        """
        Create a Model instance from the input data.
        Delegates to load_input() after fetching the version implementation's custom
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

        input : json string, dict or Path

        TODO: Document this properly.

        """
        if type(input) not in [str, dict] and not isinstance(input, Path):
            # Old-school type checking. See the note above about @validate_arguments
            raise ValueError(f"Cannot load {type(input)}. Must be str, dict or Path.")
        return self.loader().load_input(input=input, validate_version=validate_version, update_version=update_version)

    def loader(self):
        """
        Get the Loader class specific to the schema version provided to Loader().
        If the implementation module does not provide a Loader, return self.

        Used by load() before it delegates to load_input(). You generally do not
        need to invoke loader() directly.
        """

        if hasattr(self.module, "Loader"):
            loader = cast(ImportExport, getattr(self.module, "Loader"))
            return loader.create(version=self.version)

        return self

    def load_input(
        self,
        *,
        input: Union[str, dict, FilePath],
        validate_version: Optional[LoaderValidations] = LoaderValidations.READABLE,
        update_version: Optional[bool] = True,
    ) -> BaseVersionedModel:
        """
        Create a Model instance from the input data which can be a json string, a dict
        or a FilePath pointing to a json document.
        """

        # Convert the input to a dict
        raw_data = self.load_raw_data(input)

        if not raw_data:
            # If you want to deal with the case where load_raw_data() returns
            # no data, override load_raw_data() in your subclass & do it there.
            raise ValueError(f"{type(self)}.load_raw_data(...) -> __falsy__")

        # Extract the schema version from the incoming data.
        raw_data_version = self.get_schema_version(model=raw_data)

        # Validate that the incoming data's version satisfies `validate_version`.
        if not self.validate_version(
            input_version=raw_data_version,
            validate_version=cast(LoaderValidations, validate_version),
        ):
            raise ValueError(
                f"Input schema version [{raw_data_version}] does not satisfy loader validation [{validate_version}]."
            )

        # Manipulate the input (if necessary) to make it compatible with the target Model
        raw_data = self.make_compatible(data=raw_data, data_version=raw_data_version)

        # Delegate to pydantic to create a Model from the raw data dict.
        model = self.materialze_model(data=raw_data)

        if update_version:
            self.set_schema_version(model=model)

        return model

    def make_compatible(self, data: dict, data_version: SchemaVersion) -> dict:
        """
        Update `data` if necessary to make it compatible with with self.version.

        Note that the `schema_version` element of the returned dict should not
        be updated by this method. That will be done by set_schema_version()
        after the new Model is created if load_input() was given a truthy value
        for update_version.

        The caveat to this rule is if you have additional constraints on the target
        version's Model's schema_version attribute that would fail during parse_obj().
        In such a scenario the raw_dict's schema_version must be updated here in
        order to make it compatible with the target Model's parse_obj().
        """

        return data

    def materialze_model(self, data: dict) -> BaseVersionedModel:
        """
        Materialize a Model from a compatible dict.

        Delegates to pydantic to create a Model from the raw data dict.

        This will fail if the incoming data does not conform to the Model's schema.
        Use make_compatible() to manipulate the data if that is a concern or load
        the data with a compatible Model and use Exporter to export it to the
        desired Model.

        e.g. -- If the incoming data is v0.5.6 and you want to load it into a v0.5.3
        Model, use Loader to load the data into a v0.5.6 Model then use Exporter to
        create the target v0.5.3 Model from the v0.5.6 Model instance instead of
        trying to directly load the v0.5.6 data into a v0.5.3 Model.
        """
        return cast(BaseVersionedModel, self.model).parse_obj(data)

    def validate_version(self, *, input_version: SchemaVersion, validate_version: LoaderValidations) -> bool:
        """
        Verify that the input_version vs self.module's version satisfies `validate_version`.
        The implementation module may provide can_read/can_write methods to determine if it is able
        to read/write input_version. If these methods do not exist, we will call the can_read/can_write
        methods of SchemaVersion(self.module.VERSION)
        """

        assert isinstance(validate_version, LoaderValidations)

        # Delegate to SchemaVersion.create() to convert (if necessary) the implementation module's
        # VERSION attribute to a SchemaVersion.
        version = str(getattr(self.module, "VERSION"))
        self.module_version = SchemaVersion.create(version=version)

        if validate_version == LoaderValidations.NONE:
            return True

        if validate_version == LoaderValidations.IDENTICAL:
            if self.module_version != input_version:
                raise ValueError(
                    f"Input of version [{input_version}] does not match " f"Model version [{self.module_version}]."
                )

        if validate_version == LoaderValidations.READABLE:
            if not self.can_read(input_version):
                raise ValueError(
                    f"Input of version [{input_version}] cannot be read by " f"Model version [{self.module_version}]."
                )

        if validate_version == LoaderValidations.WRITABLE:
            if not self.can_write(input_version):
                raise ValueError(
                    f"Input of version [{input_version}] cannot be written by "
                    f"Model version [{self.module_version}]."
                )

        return True

    def can_read(self, other: Union[SchemaVersion, str]):
        """If self.module has a can_read() method, delegate to it else
        delegate to self.module.VERSION.can_read()
        You will often override this for "boundary" implementations.
        (e.g. - so that v2.0.0 can read v1.last.version data)
        """
        can_read = (
            # self.module.can_read or self.module_version.can_read
            self.module_version.can_read
            if not hasattr(self.module, "can_read")
            else getattr(self.module, "can_read")
        )
        return can_read(other)

    def can_write(self, other: Union[SchemaVersion, str]):
        """If self.module has a can_write() method, delegate to it else
        delegate to self.module.VERSION.can_write()
        You will often override this for "boundary" implementations.
        (e.g. - so that v2.0.0 can write v1.last.version data)
        """
        can_write = (
            # self.module.can_write or self.module_version.can_write
            self.module_version.can_write
            if not hasattr(self.module, "can_write")
            else getattr(self.module, "can_write")
        )
        return can_write(other)

    # #### Implementation details

    def load_raw_data(self, input):
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
    to export a Model to another compatible Model version.

    Subclasses of Exporter may extend this further to allow a Model to export itself
    to Model versions not explicitly implied by their SchemaVersion compatibility.

    Subclasses may also need to override several of the helper methods where Exporter
    expects to find a `schema_version` attribute of type SchemaVersion.
    """

    silence_identical_versions_warning: bool = False
    ignore_extra: bool = True

    def export(
        self,
        *,
        input: BaseModel,
        update_version: Optional[bool] = True,
        copy_before_export: Optional[bool] = False,
    ) -> BaseModel:
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

        # We cannot use @validate_arguments because `input` may be a subclass
        # of BaseModel and we explicitly disallow extra fields.
        assert isinstance(
            input, BaseModel
        ), f"{type(self)}.export() expected `input` type [BaseModel] got [{type(input)}]"

        do_export = self.exporter().export_model
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
            return exporter.create(version=self.version)

        return self

    def export_model(
        self,
        *,
        input: BaseModel,
        update_version: Optional[bool] = True,
        copy_before_export: Optional[bool] = False,
    ) -> BaseModel:
        """
        Create a Model instance from the input Model.

        Optionally updates `schema_version` in the returned Model to match self.version.
        """

        input_version = self.get_schema_version(model=input)

        # Warn the user if they're doing things the hard way.
        if not self.silence_identical_versions_warning and input_version == self.version:
            warnings.warn(
                f"Using Exporter when input and target versions are identical [{input_version}] is not recommended."
            )

        # Validate the input data against self.version
        if not self.validate_version(input_version=input_version):
            raise ValueError(f"Input schema version [{input_version}] cannot be exported as [{self.version}].")

        if copy_before_export:
            # There is a possibility that make_compatible() may update the dict representation
            # of the input data. Set copy_before_export if this is a concern.
            input = input.copy(deep=True)

        # Convert the input to a dict and manipulate it (if necessary) to make it compatible with the target Model
        raw_data = self.make_compatible(model=input)

        # Delegate to pydantic to create a Model from the raw data dict.
        model = self.materialze_model(data=raw_data)

        if update_version:
            self.set_schema_version(model=model)

        return model

    def make_compatible(self, model: BaseModel) -> dict:
        """
        Return a dict representation of `model` that is compatible with self.version.

        Note that the `schema_version` element of the returned dict should not
        be updated by this method. That will be done by set_schema_version()
        after the new Model is created if export_model() was given a truthy value
        for update_version.

        The caveat to this rule is if you have additional constraints on the target
        version's Model's schema_version attribute that would fail during parse_obj().
        In such a scenario the raw_dict's schema_version must be updated here in
        order to make it compatible with the target Model's parse_obj().
        """

        return model.dict(include=self.get_includes(), exclude=self.get_excludes())

    def get_includes(self) -> Union["AbstractSetIntStr", "MappingIntStrAny"]:
        return cast(Union["AbstractSetIntStr", "MappingIntStrAny"], None)

    def get_excludes(self) -> Union["AbstractSetIntStr", "MappingIntStrAny"]:
        return cast(Union["AbstractSetIntStr", "MappingIntStrAny"], None)

    def materialze_model(self, data: dict) -> BaseModel:
        """
        Materialize a Model from a compatible dict representation of another Model.

        Delegates to pydantic to create a Model from the raw data dict.

        We know this will fail if the input model has fields that are not present in
        the target model. We will tell pydantic to ignore extra fields so that we
        don't have to explicitly list each one.

        This is absolutely not thread safe if self.ignore_extra is truthy!
        """

        parse_obj = cast(BaseModel, self.model).parse_obj

        if not self.ignore_extra:
            return parse_obj(data)

        extra = BaseModel.Config.extra
        BaseModel.Config.extra = Extra.ignore
        model = parse_obj(data)
        BaseModel.Config.extra = extra

        return model

    def validate_version(self, *, input_version: SchemaVersion) -> bool:
        """
        Verify that the input_version vs self.module's version satisfies SchemaVersion compatibility.

        Subclasses of Export may extend compatibility beyond SchemaVersion's default rules.

        For instance, va.b.c is not required to be exportable to vA.B.C where where a != A.
        Similarly, va.b.c is not required to be exportable to va.B.? where b < B.
        An Exporter subclass in the va.b.c implementation module can override validate_version()
        (and will probably need to override make_compatible()) in order to allow this.
        """

        can_write = (
            input_version.can_write if not hasattr(self.module, "can_write") else getattr(self.module, "can_write")
        )

        if can_write(self.version):
            return True

        raise ValueError(f"Input of version [{input_version}] cannot be exported as [{self.version}].")


# Update `ExporterType` to refer to our new Exporter class
ExporterType = Exporter
