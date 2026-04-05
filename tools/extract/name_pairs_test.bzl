def _py_single_quote(value):
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"

def _name_pairs_test_impl(ctx):
    src = ctx.file.src
    python = ctx.file._python
    script = ctx.actions.declare_file(ctx.label.name + ".sh")

    checks = []
    for latin in sorted(ctx.attr.expected.keys()):
        for hungarian in sorted(ctx.attr.expected[latin]):
            checks.append((latin, hungarian))

    checks_py_lines = ["["]
    for latin, hungarian in checks:
        checks_py_lines.append("    (%s, %s)," % (_py_single_quote(latin), _py_single_quote(hungarian)))
    checks_py_lines.append("]")
    checks_py = "\n".join(checks_py_lines)

    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        "pairs_file=\"$TEST_SRCDIR/$TEST_WORKSPACE/%s\"" % src.short_path,
        "python_bin=\"$TEST_SRCDIR/$TEST_WORKSPACE/%s\"" % python.short_path,
        "if [[ ! -f \"$pairs_file\" ]]; then",
        "  echo \"Missing pairs file: $pairs_file\" >&2",
        "  exit 1",
        "fi",
        "if [[ ! -x \"$python_bin\" ]]; then",
        "  echo \"Missing python executable: $python_bin\" >&2",
        "  exit 1",
        "fi",
        "",
        "\"$python_bin\" - \"$pairs_file\" <<'PY'",
        "import json",
        "import sys",
        "",
        "pairs_path = sys.argv[1]",
        "data = json.load(open(pairs_path, encoding='utf-8'))",
        "expected = %s" % checks_py,
        "",
        "index = {}",
        "for latin, values in data.items():",
        "    latin_cf = latin.casefold()",
        "    value_set = index.setdefault(latin_cf, set())",
        "    for value in values:",
        "        value_set.add(value.casefold())",
        "",
        "for latin, hungarian in expected:",
        "    latin_cf = latin.casefold()",
        "    hungarian_cf = hungarian.casefold()",
        "    if latin_cf not in index:",
        "        print(f'Missing extracted key: {latin}')",
        "        raise SystemExit(1)",
        "    if hungarian_cf not in index[latin_cf]:",
        "        print(f'Missing extracted pair: {latin} = {hungarian}')",
        "        raise SystemExit(1)",
        "",
        "if %s:" % ("True" if ctx.attr.exact else "False"),
        "    expected_map = {}",
        "    for latin, hungarian in expected:",
        "        expected_map.setdefault(latin.casefold(), set()).add(hungarian.casefold())",
        "    for latin_cf, expected_values in expected_map.items():",
        "        actual_values = index[latin_cf]",
        "        if actual_values != expected_values:",
        "            print(f'Unexpected values for key {latin_cf}: expected={sorted(expected_values)}, actual={sorted(actual_values)}')",
        "            raise SystemExit(1)",
        "",
        "print('All expected name pairs found.')",
        "PY",
        "",
    ]

    ctx.actions.write(
        output = script,
        content = "\n".join(lines),
        is_executable = True,
    )

    return DefaultInfo(
        executable = script,
        runfiles = ctx.runfiles(files = [src, python]),
    )

name_pairs_test = rule(
    implementation = _name_pairs_test_impl,
    test = True,
    attrs = {
        "exact": attr.bool(
            default = False,
        ),
        "expected": attr.string_list_dict(
            mandatory = True,
        ),
        "src": attr.label(
            allow_single_file = True,
            mandatory = True,
        ),
        "_python": attr.label(
            cfg = "exec",
            allow_single_file = True,
            default = "@python//:bin/python3",
        ),
    },
)
