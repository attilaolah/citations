load("@rules_python//python:defs.bzl", "py_test")

def name_pairs_test(name, src, samples, **kwargs):
      main = "//tools/extract:name_pairs_test.py"
    py_test(
        name = name,
        srcs = [main],
        main = main,
        data = [
            src,
            samples,
        ],
        env = {
            "PAIRS_PATH": "$(rootpath %s)" % src,
            "SAMPLES_PATH": "$(rootpath %s)" % samples,
        },
        **kwargs
    )
