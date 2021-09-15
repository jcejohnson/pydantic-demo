"""
The point of this test is to ensure that every supported version is implemented
exactly once and that every implementation module's VERSION is in the list of
supported versions.

TL;DR - We do all the things and don't do anything useless.
"""

import importlib
import inspect
import os
import pkgutil
from types import ModuleType
from typing import Dict

import pytest

from aktorz.model import BaseModel, loader, schema_version
from aktorz.model.supported_versions import SUPPORTED_VERSIONS

AKTORZ_MODEL_PATH: str = os.path.dirname(inspect.getfile(loader))
VERSION_MODULES_BY_NAME: Dict[str, ModuleType] = dict()
VERSION_MODULES_BY_VERSION: Dict[str, ModuleType] = dict()


def setup_module(module):
    global VERSION_MODULES_BY_NAME
    global VERSION_MODULES_BY_VERSION
    VERSION_MODULES_BY_NAME = get_version_modules_by_name()
    VERSION_MODULES_BY_VERSION = get_version_modules_by_version()


def get_version_modules_by_name():
    _build_version_modules_by_x()
    return VERSION_MODULES_BY_NAME


def get_version_modules_by_version():
    _build_version_modules_by_x()
    return VERSION_MODULES_BY_VERSION


def _build_version_modules_by_x():
    global VERSION_MODULES_BY_NAME
    global VERSION_MODULES_BY_VERSION

    if VERSION_MODULES_BY_NAME and VERSION_MODULES_BY_VERSION:
        return

    def _has_model_class(name):
        return hasattr(importlib.import_module(f".{name}", package=loader.__package__), "Model")

    by_name = dict()
    by_version = dict()
    for m in pkgutil.walk_packages([AKTORZ_MODEL_PATH]):

        name = m.name

        if not (name.startswith(schema_version.DEFAULT_PREFIX) or _has_model_class(name)):
            continue

        by_name[name] = module = importlib.import_module(f".{name}", package=loader.__package__)

        try:
            version = getattr(module, "VERSION")
            if version not in by_version:
                by_version[version] = by_name[name]
        finally:
            # We will handle missing VERSION attributes in test_version_module_validity()
            pass

    VERSION_MODULES_BY_NAME = by_name
    VERSION_MODULES_BY_VERSION = by_version


class TestSupportedVersions:
    @pytest.fixture
    def aktorz_model_path(self):
        """Get the filesystem path where the models can be found."""
        return AKTORZ_MODEL_PATH

    @pytest.fixture
    def version_modules_by_name(self):
        """Gather the versioned model modules."""
        return VERSION_MODULES_BY_NAME

    @pytest.fixture
    def version_modules_by_version(self):
        """Gather the versioned model modules."""
        return VERSION_MODULES_BY_VERSION

    def test_aktorz_model_path(self, aktorz_model_path: str):
        """Verify that the filesystem path is valid."""
        assert aktorz_model_path.endswith(os.path.join("aktorz", "model"))
        assert os.path.isdir(aktorz_model_path)

    def test_has_version_modules(self, version_modules_by_name: Dict[str, ModuleType]):
        """Verify that we found at least one module providing a Model."""
        assert version_modules_by_name, "Failed to locate any version modules."

    @pytest.mark.parametrize(
        "name, module",
        [(name, module) for name, module in get_version_modules_by_name().items()]
    )
    def test_version_module_validity(self, name, module):
        """All version modules must contain a Model with specific characteristics:
        - version modules must contain a Model
        - Model must subclass aktorz.model.BaseModel (which subclasses pydantic's BaseModel)
        - version modules must contain a VERSION attribute
        - VERSION must be truthy
        """

        # All version modules must contain a Model class.
        assert hasattr(module, "Model"), f"Version module [{name}] is missing [Model]"

        # All Model classes must subclass BaseModel.
        assert issubclass(getattr(module, "Model"), BaseModel)

        # All version modules must provide a truthy VERSION attribute.
        assert hasattr(module, "VERSION"), f"Version module [{name}] is missing [VERSION]"
        assert str(getattr(module, "VERSION")), f"Version module [{name}] has falsy [VERSION]"

    @pytest.mark.parametrize(
        "name, module",
        [(name, module) for name, module in get_version_modules_by_name().items()]
    )
    def test_only_one_implementation_per_version(
        self, name, module, version_modules_by_version: Dict[str, ModuleType]
    ):
        """Only one version module can support a given version."""

        # Skip any invalid modules. Rely on test_version_module_validity() to sort those out.
        if not hasattr(module, "VERSION"):
            return

        version = str(getattr(module, "VERSION"))
        assert version_modules_by_version[version] == module, (
            f"Version module [{name}] duplicates existing version [{version}] "
            f"provided by [{version_modules_by_version[version].__name__}]"
        )

    @pytest.mark.parametrize(
        "version, module",
        [(version, module) for version, module in get_version_modules_by_version().items()]
    )
    def test_every_implementation_is_useful(self, version, module):
        """Veryfy that every version implmentation module is implementing a supported version.
        Any modules that are not implementing supported versions are unnecessary and should be deleted.
        """

        assert (
            version in SUPPORTED_VERSIONS
        ), f"Module [{module.__name__}] implements unsupported version [{version}] and should be deleted."

    @pytest.mark.parametrize(
        "version",
        [(version) for version in get_version_modules_by_version()]
    )
    def test_every_version_is_implemented(self, version, version_modules_by_version):
        """Verify that every supported version has an implementation module."""

        assert version in version_modules_by_version, f"Missing implementation for supported version [{version}]."
