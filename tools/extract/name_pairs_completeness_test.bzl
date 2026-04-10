"""Macro for testing cleaned name pairs against extracted scientific names."""

load("@rules_python//python:defs.bzl", "py_test")

def name_pairs_completeness_test(name, clean, scientific_names, ignore = None, **kwargs):
    """Defines a py_test that checks cleaned pairs cover expected scientific names.

    Args:
      name: Name of the generated test target.
      clean: Label for the cleaned name-pairs artifact.
      scientific_names: Label for the extracted scientific-names artifact.
      ignore: Optional label with names that should be ignored.
      **kwargs: Extra attributes forwarded to the underlying py_test.
    """
    data = [
        clean,
        scientific_names,
    ]
    env = {
        "CLEAN": "$(rootpath %s)" % clean,
        "SCIENTIFIC_NAMES": "$(rootpath %s)" % scientific_names,
    }
    if ignore != None:
        env["IGNORE_NAMES"] = "$(rootpath %s)" % ignore
        data.append(ignore)

    py_test(
        name = name,
        srcs = ["//tools/extract:name_pairs_completeness_test"],
        main = "name_pairs_completeness_test.py",
        deps = ["//tools/extract:models"],
        data = data,
        env = env,
        **kwargs
    )
