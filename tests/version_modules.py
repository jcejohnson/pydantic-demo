import importlib
import inspect
import os
import pkgutil
import re
from types import ModuleType
from typing import Dict

from aktorz.model import DEFAULT_VERSION_PREFIX, v0_1_x


class VersionModules:
    """
    Helper class for finding modules that implement versioned models.
    """

    aktorz_model_path: str = os.path.dirname(inspect.getfile(v0_1_x))
    version_modules_by_name: Dict[str, ModuleType] = dict()
    version_modules_by_version: Dict[str, ModuleType] = dict()
    version_prefix: str = DEFAULT_VERSION_PREFIX

    def __init__(self):
        def _has_model_class(name):
            return hasattr(importlib.import_module(f".{name}", package=v0_1_x.__package__), "Model")

        self.version_modules_by_name = dict()
        self.version_modules_by_version = dict()
        for m in pkgutil.walk_packages([self.aktorz_model_path]):

            name = m.name

            # Skip modules that are not version modules
            if not name.startswith(self.version_prefix):
                continue

            # Skip version-specific utility modules
            # e.g. -- v0_1_x
            if not re.match("^.*[0-9]$", name):
                continue

            # Skip version modules that have no Model
            if not _has_model_class(name):
                continue

            module = importlib.import_module(f".{name}", package=v0_1_x.__package__)
            self.version_modules_by_name[name] = module

            version = getattr(module, "VERSION")
            if version not in self.version_modules_by_version:
                self.version_modules_by_version[version] = self.version_modules_by_name[name]


CONFIG_DATA: VersionModules = VersionModules()
