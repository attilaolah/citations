load("@rules_python//python:defs.bzl", "py_test")

def name_pairs_test(name, src, samples, **kwargs):
    py_test(
        name = name,
        srcs = ["//tools/extract:name_pairs_test.py"],
        main = "//tools/extract:name_pairs_test.py",
        args = [
            "--mode",
            "pairs",
            "--pairs",
            "$(location %s)" % src,
            "--samples",
            "$(location %s)" % samples,
        ],
        data = [
            src,
            samples,
        ],
        **kwargs
    )
