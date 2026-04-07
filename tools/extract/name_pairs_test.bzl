load("@rules_python//python:defs.bzl", "py_test")

def name_pairs_test(name, src, samples, **kwargs):
    py_test(
        name = name,
        srcs = ["//tools/extract:name_pairs_test.py"],
        main = "//tools/extract:name_pairs_test.py",
        data = [
            src,
            samples,
        ],
        env = {
            "PAIRS_PATH": "$(location %s)" % src,
            "SAMPLES_PATH": "$(location %s)" % samples,
        },
        **kwargs
    )
