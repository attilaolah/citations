"""Macro for testing cleaned name pairs against globally extracted names."""

load("@rules_python//python:defs.bzl", "py_test")

def name_pairs_completeness_test(name, clean, global_names, ignore = None, **kwargs):
    """Defines a py_test that checks cleaned pairs cover expected global names.

    Args:
      name: Name of the generated test target.
      clean: Label for the cleaned name-pairs artifact.
      global_names: Label for the extracted global-names artifact.
      ignore: Optional label with names that should be ignored.
      **kwargs: Extra attributes forwarded to the underlying py_test.
    """
    data = [
        clean,
        global_names,
    ]
    env = {
        "CLEAN": "$(rootpath %s)" % clean,
        "GLOBAL_NAMES": "$(rootpath %s)" % global_names,
    }
    if ignore != None:
        env["IGNORE_NAMES"] = "$(rootpath %s)" % ignore
        data.append(ignore)

    py_test(
        name = name,
        srcs = [
            "//tools/extract:models.py",
            "//tools/extract:name_pairs_completeness_test.py",
        ],
        main = "name_pairs_completeness_test.py",
        data = data,
        env = env,
        **kwargs
    )
