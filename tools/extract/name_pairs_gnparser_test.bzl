def _name_pairs_gnparser_test_impl(ctx):
    src = ctx.file.src
    python = ctx.file._python
    gnparser = ctx.file._gnparser
    script = ctx.actions.declare_file(ctx.label.name + ".sh")

    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        "pairs_file=\"$TEST_SRCDIR/$TEST_WORKSPACE/%s\"" % src.short_path,
        "python_bin=\"$TEST_SRCDIR/$TEST_WORKSPACE/%s\"" % python.short_path,
        "gnparser_bin=\"$TEST_SRCDIR/$TEST_WORKSPACE/%s\"" % gnparser.short_path,
        "if [[ ! -f \"$pairs_file\" ]]; then",
        "  echo \"Missing pairs file: $pairs_file\" >&2",
        "  exit 1",
        "fi",
        "if [[ ! -x \"$python_bin\" ]]; then",
        "  echo \"Missing python executable: $python_bin\" >&2",
        "  exit 1",
        "fi",
        "if [[ ! -x \"$gnparser_bin\" ]]; then",
        "  echo \"Missing gnparser executable: $gnparser_bin\" >&2",
        "  exit 1",
        "fi",
        "",
        "\"$python_bin\" - \"$pairs_file\" \"$gnparser_bin\" <<'PY'",
        "import json",
        "import subprocess",
        "import sys",
        "",
        "pairs_path = sys.argv[1]",
        "gnparser_bin = sys.argv[2]",
        "data = json.load(open(pairs_path, encoding='utf-8'))",
        "",
        "def normalize_key(name: str) -> str:",
        "    return name.title() if name.isupper() else name",
        "",
        "failures = []",
        "for key in sorted(data):",
        "    candidate = normalize_key(key)",
        "    proc = subprocess.run(",
        "        [gnparser_bin, candidate, '-f', 'compact'],",
        "        check=False,",
        "        text=True,",
        "        capture_output=True,",
        "    )",
        "    if proc.returncode != 0:",
        "        failures.append((key, candidate, 'non-zero exit', proc.stderr.strip()))",
        "        continue",
        "",
        "    out = proc.stdout.strip()",
        "    try:",
        "        parsed = json.loads(out)",
        "    except json.JSONDecodeError:",
        "        failures.append((key, candidate, 'invalid JSON', out))",
        "        continue",
        "",
        "    if not parsed.get('parsed', False):",
        "        failures.append((key, candidate, 'no parse match', out))",
        "",
        "if failures:",
        "    print('gnparser validation failures:')",
        "    for key, candidate, reason, details in failures:",
        "        print(f'  key={key!r} candidate={candidate!r} reason={reason} details={details}')",
        "    raise SystemExit(1)",
        "",
        "print('All extracted keys matched gnparser.')",
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
        runfiles = ctx.runfiles(files = [src, python, gnparser]),
    )

name_pairs_gnparser_test = rule(
    implementation = _name_pairs_gnparser_test_impl,
    test = True,
    attrs = {
        "src": attr.label(
            allow_single_file = True,
            mandatory = True,
        ),
        "_gnparser": attr.label(
            cfg = "exec",
            allow_single_file = True,
            default = "@gnparser//:bin/gnparser",
        ),
        "_python": attr.label(
            cfg = "exec",
            allow_single_file = True,
            default = "@python//:bin/python3",
        ),
    },
)
