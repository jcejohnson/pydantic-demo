"""
The point of this test is to ensure that every supported version is implemented
exactly once and that every implementation module's VERSION is in the list of
supported versions.

TL;DR - We do all the things and don't do anything useless.
"""

import os
from types import ModuleType
from typing import Dict

import pytest

# We are testing the public interface so we will import from
# the package rather than the underlying modules.
from aktorz.model import BaseModel, SUPPORTED_VERSIONS

from .version_modules import CONFIG_DATA


class TestSupportedVersions:

    # Isolate CONFIG_DATA and SUPPORTED_VERSIONS to the fixtures
    # and let the fixtures provide the data to the tests.

    @pytest.fixture
    def aktorz_model_path(self):
        """Get the filesystem path where the models can be found."""
        return CONFIG_DATA.aktorz_model_path

    @pytest.fixture
    def version_modules_by_name(self):
        return CONFIG_DATA.version_modules_by_name

    @pytest.fixture
    def version_modules_by_version(self):
        return CONFIG_DATA.version_modules_by_version

    @pytest.fixture
    def implemented_versions(self):
        return CONFIG_DATA.version_modules_by_version.keys()

    @pytest.fixture
    def supported_versions(self):
        return SUPPORTED_VERSIONS

    # Tests...

    def test_aktorz_model_path(self, aktorz_model_path: str):
        """Verify that the filesystem path is valid."""
        assert aktorz_model_path.endswith(os.path.join("aktorz", "model"))
        assert os.path.isdir(aktorz_model_path)

    def test_has_version_modules(self, version_modules_by_name: Dict[str, ModuleType]):
        """Verify that we found at least one module providing a Model."""
        assert version_modules_by_name, "Failed to locate any version modules."

    @pytest.mark.parametrize(
        "name, module", [(name, module) for name, module in CONFIG_DATA.version_modules_by_name.items()]
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
        [
            (name, module)
            for name, module in CONFIG_DATA.version_modules_by_name.items()
            # Skip implementations that don't provide a version or model.
            # We'll deal with those in test_version_module_validity.
            if hasattr(module, "Model") and hasattr(module, "VERSION")
        ],
    )
    def test_only_one_implementation_per_version(
        self, name, module, version_modules_by_version: Dict[str, ModuleType]
    ):
        """Only one version module can support a given version."""

        version = str(getattr(module, "VERSION"))
        assert version_modules_by_version[version] == module, (
            f"Version module [{name}] duplicates existing version [{version}] "
            f"provided by [{version_modules_by_version[version].__name__}]"
        )

    @pytest.mark.parametrize(
        "version, module", [(version, module) for version, module in CONFIG_DATA.version_modules_by_version.items()]
    )
    def test_every_implementation_is_useful(self, version, module, supported_versions):
        """
        Veryfy that every version implmentation module is implementing a supported version.
        Any modules that are not implementing supported versions are unnecessary and should be deleted.
        """

        assert (
            version in supported_versions
        ), f"Module [{module.__name__}] implements unsupported version [{version}] and should be deleted."

    @pytest.mark.parametrize("version", [(version) for version in SUPPORTED_VERSIONS])
    def test_every_version_is_implemented(self, version, implemented_versions):
        """Verify that every supported version has an implementation module."""

        assert version in implemented_versions, f"Missing implementation for supported version [{version}]."
