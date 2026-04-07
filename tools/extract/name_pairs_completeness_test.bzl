load("@rules_python//python:defs.bzl", "py_test")

def name_pairs_completeness_test(name, clean, global_names, ignore = None, **kwargs):
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
        srcs = ["//tools/extract:name_pairs_completeness_test.py"],
        main = "//tools/extract:name_pairs_completeness_test.py",
        data = data,
        env = env,
        **kwargs
    )
