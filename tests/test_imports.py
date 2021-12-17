import importlib
from types import ModuleType


class TestImports:
    """
    Just some basic usage of importlib.
    """

    def test_import_model(self):

        module = importlib.import_module("aktorz.model.v0_1_0")

        assert type(module) == ModuleType

    def test_module_from_class(self):

        from aktorz.model.v0_1_0 import Model

        module = Model.__module__

        assert type(module) == str
        assert module == "aktorz.model.v0_1_0"

        module = importlib.import_module(module)
        assert type(module) == ModuleType

    def test_loader_from_class(self):

        from aktorz.model.v0_2_0 import Loader, Model

        module = Model.__module__

        module = importlib.import_module(module)

        loader = getattr(module, "Loader")

        assert loader == Loader
