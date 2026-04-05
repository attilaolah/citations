load("@rules_python//python:defs.bzl", "py_test")

def name_pairs_gnparser_test(name, src, gnparser = "@gnparser//:bin/gnparser", **kwargs):
    py_test(
        name = name,
        srcs = ["//tools/extract:name_pairs_test.py"],
        main = "//tools/extract:name_pairs_test.py",
        args = [
            "--mode",
            "gnparser",
            "--pairs",
            "$(location %s)" % src,
            "--gnparser",
            "$(location %s)" % gnparser,
        ],
        data = [
            src,
            gnparser,
        ],
        **kwargs
    )
