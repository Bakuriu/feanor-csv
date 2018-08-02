import inspect

from functools import singledispatch, update_wrapper


def to_string_list(iterable):
    """Utility function to produce a string like: "'A', 'B', 'C'" from ['B', 'A', 'C'].

        >>> to_string_list(['B', 'A', 'C'])
        "'A', 'B', 'C'"

    """
    return ', '.join(map(repr, sorted(iterable)))


def overloaded(func=None, is_method=None):
    """Utility function that can be used to create overloaded functions and methods.

    For functions it works in the same way as `functools.singledispatch`:

        >>> @overloaded
        ... def func(arg, other_arg):
        ...     return arg + other_arg
        ...
        >>> @func.register(float)
        ... def _(arg):
        ...     return 'float {:.2f}'.format(arg)
        ...
        >>> @func.register(int)
        ... def _(arg, other_arg):
        ...     return 2*arg
        ...
        >>> func(10, -1)
        20
        >>> func(0.753)
        'float 0.75'
        >>> func("Hello ", "World!")
        'Hello World!'

    The dispatching is done on the type of the first argument.

    The decorator can be used on methods too:

        >>> class A:
        ...     @overloaded
        ...     def method(self, arg):
        ...         return 2*arg
        ...     @method.register(float)
        ...     def _(self, arg):
        ...         return 3*arg
        ...
        >>> a = A()
        >>> a.method(5)
        10
        >>> a.method(5.0)
        15.0

    It detects the fact that it is applied on a method by the name `self` of the first parameter and the fact that
    there are at least 2 parameters. You can also force the treatment of a method by explicitly specifying the
    `is_method` keyword argument to the decorator:

        >>> class A:
        ...     @overloaded(is_method=True)
        ...     def method(not_self, arg):
        ...         return 2*arg
        ...     @method.register(float)
        ...     def _(not_self, arg):
        ...         return 3*arg
        ...
        >>> a = A()
        >>> a.method(5)
        10
        >>> a.method(5.0)
        15.0

    """

    def inner_decorator(function):
        nonlocal is_method
        if is_method is None:
            params = inspect.signature(function).parameters
            is_method = len(params) >= 2 and next(iter(params.values())).name == 'self'

        dispatcher = singledispatch(function)

        if not is_method:
            return dispatcher

        def wrapper(*args, **kw):
            return dispatcher.dispatch(args[1].__class__)(*args, **kw)

        wrapper.register = dispatcher.register
        update_wrapper(wrapper, function)
        return wrapper

    if func is None:
        return inner_decorator
    return inner_decorator(func)
