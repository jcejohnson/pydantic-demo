import importlib
import inspect
import os
import pkgutil
from types import ModuleType
from typing import Dict

from aktorz.model import loader, schema_version


class VersionModules:

    aktorz_model_path: str = os.path.dirname(inspect.getfile(loader))
    version_modules_by_name: Dict[str, ModuleType] = dict()
    version_modules_by_version: Dict[str, ModuleType] = dict()

    def __init__(self):
        def _has_model_class(name):
            return hasattr(importlib.import_module(f".{name}", package=loader.__package__), "Model")

        self.version_modules_by_name = dict()
        self.version_modules_by_version = dict()
        for m in pkgutil.walk_packages([self.aktorz_model_path]):

            name = m.name

            if not (name.startswith(schema_version.DEFAULT_PREFIX) or _has_model_class(name)):
                continue

            module = importlib.import_module(f".{name}", package=loader.__package__)
            self.version_modules_by_name[name] = module

            try:
                version = getattr(module, "VERSION")
                if version not in self.version_modules_by_version:
                    self.version_modules_by_version[version] = self.version_modules_by_name[name]
            finally:
                # We will handle missing VERSION attributes in test_version_module_validity()
                pass


CONFIG_DATA: VersionModules = VersionModules()
