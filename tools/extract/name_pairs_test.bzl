def _sh_single_quote(value):
    return "'" + value.replace("'", "'\"'\"'") + "'"

def _name_pairs_test_impl(ctx):
    src = ctx.file.src
    script = ctx.actions.declare_file(ctx.label.name + ".sh")

    checks = []
    for latin in sorted(ctx.attr.expected.keys()):
        for hungarian in sorted(ctx.attr.expected[latin]):
            checks.append("%s = %s" % (latin, hungarian))

    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        "pairs_file=\"$TEST_SRCDIR/$TEST_WORKSPACE/%s\"" % src.short_path,
        "if [[ ! -f \"$pairs_file\" ]]; then",
        "  echo \"Missing pairs file: $pairs_file\" >&2",
        "  exit 1",
        "fi",
        "",
    ]

    for check in checks:
        quoted = _sh_single_quote(check)
        lines.extend([
            "if ! grep -Fqx -- %s \"$pairs_file\"; then" % quoted,
            "  echo \"Missing extracted pair: %s\" >&2" % check,
            "  exit 1",
            "fi",
        ])

    lines.append("echo \"All expected name pairs found.\"")
    lines.append("")

    ctx.actions.write(
        output = script,
        content = "\n".join(lines),
        is_executable = True,
    )

    return DefaultInfo(
        executable = script,
        runfiles = ctx.runfiles(files = [src]),
    )

name_pairs_test = rule(
    implementation = _name_pairs_test_impl,
    test = True,
    attrs = {
        "expected": attr.string_list_dict(
            mandatory = True,
        ),
        "src": attr.label(
            allow_single_file = True,
            mandatory = True,
        ),
    },
)
