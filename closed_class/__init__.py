import functools
import weakref

__all__ = ['ClosedMeta']

_base_dunder_exceptions = frozenset({
    '__new__',
    '__init__',
    '__del__',
    '__init_subclass__',
    '__instancecheck__',
    '__subclasscheck__',
})

_default_dunder_exceptions = frozenset({
    '__repr__',
    '__str__'
    '__bytes__'
    '__format__'
    '__lt__'
    '__le__'
    '__eq__'
    '__ne__',
    '__gt__',
    '__ge__',
    '__hash__',
    '__bool__',
    '__setattr__',
    '__delattr__',
    '__dir__',
    '__set__',
    '__delete__',
    '__set_name__',
    '__slots__',
    '__len__',
    '__length_hint__',
    '__setitem__',
    '__delitem__',
    '__iter__',
    '__reversed__',
    '__contains__',
    '__complex__',
    '__int__',
    '__float__',
    '__index__',
    '__enter__',
    '__exit__',
    '__await__',
    '__aiter__',
    '__anext__',
    '__aenter__',
    '__aexit__'
})


def get_mro(bases):
    # We omit 'object' as it is the base type
    return type('', bases, {}).__mro__[1:-1]


class ClosedMeta(type):
    _register = weakref.WeakValueDictionary()

    def __new__(cls, name, bases, namespace, exceptions=_default_dunder_exceptions):
        # A unique id for the class
        uid = max(cls._register) + 1 if cls._register else 0
        mro = get_mro(bases)
        exceptions = {*exceptions, *_base_dunder_exceptions}

        def tail_cast(f):
            """Cast the return value of f"""

            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                out = f(*args, **kwargs)
                if type(out) in mro:
                    # Since the class does not exist yet, we will recover it later
                    return cls._register[uid](out)
                return out

            return wrapper

        def deep_tail_cast(f):
            """Cast the return value of f or the return value of f(...)"""

            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                out = f(*args, **kwargs)
                if callable(out):
                    return tail_cast(out)
                elif type(out) in mro:
                    return cls._register[uid](out)
                else:
                    return out

            return wrapper

        class PropertyCast:
            """Cast the return value of a property"""

            def __init__(self, prop):
                self.prop = prop

            def __get__(self, instance, owner):
                return cls._register[uid](self.prop.__get__(instance, owner))

            def __set__(self, instance, value):
                return self.prop.__set__(instance, value)

            def __delete__(self, instance):
                return self.prop.__delete__(instance)

        for base in reversed(mro):
            for name, attr in base.__dict__.items():
                if name not in namespace and name not in exceptions:
                    if name in ('__getattr__', '__getattribute__'):
                        namespace[name] = deep_tail_cast(attr)
                    elif callable(attr):
                        namespace[name] = tail_cast(attr)
                    elif hasattr(attr, '__get__'):
                        namespace[name] = PropertyCast(attr)

        subcls = super().__new__(cls, name, bases, namespace)
        cls._register[uid] = subcls
        return subcls
