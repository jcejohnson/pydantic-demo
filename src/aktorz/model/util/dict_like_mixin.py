class DictLikeMixin:
    """
    Provide minimal dict-like behavior to a pydantic BaseModel (or subclass).
    """

    def __getattr__(self, field):
        # We will only be called for aliases.
        try:
            field_key = next(f for f in self.__fields__ if self.__fields__[f].alias == field)
            if field_key in self.__fields_set__:
                return getattr(self, field_key)

        except StopIteration:
            pass

        except AttributeError:
            pass

        raise AttributeError(field)

    # TypeError: 'Model' object is not subscriptable

    def __getitem__(self, key: str):

        if key in self.__fields_set__ or self.__fields__.get(key,None):
            try:
                return getattr(self, key)
            except AttributeError as e:
                raise KeyError(key)

        try:
            field_key = next(f for f in self.__fields__ if self.__fields__[f].alias == key)
            if field_key in self.__fields_set__ or self.__fields__.get(field_key,None):
                try:
                    return getattr(self, field_key)
                except AttributeError as e:
                    raise KeyError(key)

        except StopIteration:
            pass

        raise KeyError(key)

    # AttributeError: 'xxx' object has no attribute 'get'

    def get(self, key: str, default=None):

        try:
            return self.__getitem__(key)
        except KeyError:
            return default

    # AttributeError: 'Model' object has no attribute 'pop'

    def pop(self, key: str, *args):
        def _pop(key):
            value = getattr(self, key)
            delattr(self, key)
            self.__fields_set__.discard(key)
            return value

        if key in self.__fields_set__:
            return _pop(key)

        try:
            field_key = next(f for f in self.__fields__ if self.__fields__[f].alias == key)
            if field_key in self.__fields_set__:
                return _pop(field_key)

        except StopIteration:
            pass

        if len(args):
            return args[0]

        raise KeyError(key)

    # TypeError: 'Model' object does not support item assignment

    def __setitem__(self, key: str, value):
        try:
            field_key = key
            setattr(self, field_key, value)

        except ValueError:
            # ValueError: "Environments" object has no field "host-project"

            try:
                field_key = next(f for f in self.__fields__ if self.__fields__[f].alias == key)
                setattr(self, field_key, value)

            except StopIteration:
                raise KeyError(key)

            except ValueError:
                raise KeyError(key)

        self.__fields_set__.add(field_key)

        return

    # if key in data ...

    def __contains__(self, key: str):
        if key in self.__fields_set__:
            return True

        try:
            field_key = next(f for f in self.__fields__ if self.__fields__[f].alias == key)
            return field_key in self.__fields_set__

        except StopIteration:
            pass

        return False

    # for i in data ...

    def __iter__(self):
        return iter(self.__fields__[key].alias for key in self.__fields__ if key in self.__fields_set__)

    def __len__(self):
        return len(self.__fields_set__)

    # AttributeError: 'Foo' object has no attribute 'bar'

    def __the_key__(self, key):
        # This will almost always return self.__fields__[key].alias
        # but in the case of extra fields (e.g. -- dynamic comments)
        # it will return the incoming `key`
        return self.__fields__[key].alias if key in self.__fields__ else key

    def keys(self):
        return [self.__the_key__(key) for key in self.__fields_set__]

    # AttributeError: __delitem__

    def __delitem__(self, key: str):
        self.pop(key)

    # AttributeError: 'Foo' object has no attribute 'clear'

    def clear(self):
        required = {f: getattr(self, f) for f in self.__fields__ if self.__fields__[f].required}
        default = self.__class__(**required)
        for f in self.__fields__:
            setattr(self, f, getattr(default, f))
        return None

    # AttributeError: 'Foo' object has no attribute 'update'

    def update(self, other):

        if not (isinstance(other, DictLikeMixin) or isinstance(other, dict)):
            raise TypeError(f"Cannot updte [{type(self)}] from [{type(other)}].")

        for key, value in other.items():
            self[key] = value

    # AttributeError: 'Foo' object has no attribute 'items'

    def items(self):
        return [(self.__fields__[key].alias, getattr(self, key)) for key in self.__fields_set__]

