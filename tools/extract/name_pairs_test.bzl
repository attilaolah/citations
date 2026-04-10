"""Macro for sample-based validation tests over extracted name-pair outputs."""

load("@rules_python//python:defs.bzl", "py_test")

def name_pairs_test(name, src, samples, **kwargs):
    py_test(
        name = name,
        srcs = ["//tools/extract:name_pairs_test"],
        main = "name_pairs_test.py",
        deps = ["//tools/extract:models"],
        data = [
            src,
            samples,
        ],
        env = {
            "PAIRS": "$(rootpath %s)" % src,
            "SAMPLES": "$(rootpath %s)" % samples,
        },
        **kwargs
    )
