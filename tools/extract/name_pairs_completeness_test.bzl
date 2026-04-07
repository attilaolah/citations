load("@rules_python//python:defs.bzl", "py_test")

def name_pairs_completeness_test(name, clean, global_names, ignore = None, **kwargs):
    data = [
        clean,
        global_names,
    ]
    ignore_path = ""
    if ignore != None:
        ignore_path = "$(location %s)" % ignore
        data.append(ignore)

    py_test(
        name = name,
        srcs = ["//tools/extract:name_pairs_completeness_test.py"],
        main = "//tools/extract:name_pairs_completeness_test.py",
        data = data,
        env = {
            "NAME_PAIRS_COMPLETENESS_CLEAN_PATH": "$(location %s)" % clean,
            "NAME_PAIRS_COMPLETENESS_GLOBAL_NAMES_PATH": "$(location %s)" % global_names,
            "NAME_PAIRS_COMPLETENESS_IGNORE_PATH": ignore_path,
        },
        **kwargs
    )
