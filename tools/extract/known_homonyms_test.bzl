"""Macro for validating known homonyms against cleaned name-pair artifacts."""

load("@rules_python//python:defs.bzl", "py_test")

def known_homonyms_test(name, clean_jsons, known_homonyms, **kwargs):
    py_test(
        name = name,
        srcs = [
            "//tools/extract:known_homonyms_test.py",
            "//tools/extract:known_typos.py",
        ],
        main = "//tools/extract:known_homonyms_test.py",
        data = clean_jsons + [known_homonyms],
        env = {
            "CLEAN_JSONS": ":".join(["$(rootpath %s)" % clean for clean in clean_jsons]),
            "KNOWN_HOMONYMS": "$(rootpath %s)" % known_homonyms,
        },
        **kwargs
    )
