
from typing import Any, Type


class ValidationMixin:
    '''
    MyModel.validate(myModel) doesn't work the way that _I_ need.
    However, MyModel.validate(myModel.dict()) gets the job done.
    This mixin provides that functionality.

    See tests/test_validation.py for more.
    '''

    @classmethod
    def validate(cls: Type['Model'], value: Any, **dict_kwargs) -> 'Model':
        if isinstance(value, cls):
            return cls.validate(value.dict(**dict_kwargs))
        return super().validate(value)
