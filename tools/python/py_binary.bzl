"""Local wrapper macro for rules_python `py_binary` with filename defaults."""

load("@rules_python//python:defs.bzl", _py_binary = "py_binary")

def py_binary(name, srcs = None, main = None, **kwargs):
    """Create a Python binary target with `<name>.py` defaults.

    Args:
      name: Target name.
      srcs: Optional source file labels. Defaults to `[name + ".py"]`.
      main: Optional main module path. Defaults to `name + ".py"`.
      **kwargs: Remaining attributes forwarded to `rules_python` `py_binary`.
    """
    if srcs == None:
        srcs = ["%s.py" % name]
    if main == None:
        main = "%s.py" % name
    _py_binary(
        name = name,
        srcs = srcs,
        main = main,
        **kwargs
    )
