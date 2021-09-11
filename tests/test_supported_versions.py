import importlib
import inspect
import os
import pkgutil
from types import ModuleType
from typing import Any, Dict

import pytest
from parameterized import parameterized

from aktorz.model import BaseModel, loader, schema_version

AKTORZ_MODEL_PATH: str = os.path.dirname(inspect.getfile(loader))
VERSION_MODULES_BY_NAME: Dict[str, ModuleType] = None
VERSION_MODULES_BY_VERSION: Dict[str, ModuleType] = None


def setup_module(module):
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

    by_name = dict()
    by_version = dict()
    for m in pkgutil.walk_packages([AKTORZ_MODEL_PATH]):

        name = m.name

        if not (
            name.startswith(schema_version.DEFAULT_PREFIX)
            or hasattr(importlib.import_module(f".{name}", package=loader.__package__), "Model")
        ):
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
    def version_modules_by_name(self, aktorz_model_path):
        """Gather the versioned model modules."""
        return VERSION_MODULES_BY_NAME

    def test_aktorz_model_path(self, aktorz_model_path: str):
        """Verify that the filesystem path is valid."""
        assert aktorz_model_path.endswith(os.path.join("src", "aktorz", "model"))
        assert os.path.isdir(aktorz_model_path)

    def test_has_version_modules(self, version_modules_by_name: Dict[str, ModuleType]):
        """Verify that we found at least one module providing a Model."""
        assert version_modules_by_name, "Failed to locate any version modules."

    @parameterized.expand([(name, module) for name, module in get_version_modules_by_name().items()])
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

    @parameterized.expand(
        [(name, module, get_version_modules_by_version()) for name, module, in get_version_modules_by_name().items()]
    )
    def test_one_implementation_per_version(self, name, module, version_modules_by_version: Dict[str, ModuleType]):
        """Only one version module can support a given version."""

        # Skip any invalid modules. Rely on test_version_module_validity() to sort those out.
        if not hasattr(module, "VERSION"):
            return

        version = str(getattr(module, "VERSION"))
        assert version_modules_by_version[version] == module, (
            f"Version module [{name}] duplicates existing version [{version}] "
            f"provided by [{version_modules_by_version[version].__name__}]"
        )
