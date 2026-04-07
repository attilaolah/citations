load("@rules_python//python:defs.bzl", "py_test")

def name_pairs_completeness_test(name, clean, global_names, ignore = None, **kwargs):
    data = [
        clean,
        global_names,
    ]
    ignore_path = ""
    if ignore != None:
        ignore_path = "$(rootpath %s)" % ignore
        data.append(ignore)

    py_test(
        name = name,
        srcs = ["//tools/extract:name_pairs_completeness_test.py"],
        main = "//tools/extract:name_pairs_completeness_test.py",
        data = data,
        env = {
            "CLEAN_PATH": "$(rootpath %s)" % clean,
            "GLOBAL_NAMES_PATH": "$(rootpath %s)" % global_names,
            "IGNORE_PATH": ignore_path,
        },
        **kwargs
    )
