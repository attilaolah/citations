def _extract_pairs_impl(ctx):
    src = ctx.file.src
    python_bin = ctx.file._python
    out = ctx.actions.declare_file(ctx.label.name + ".txt")

    args = ctx.actions.args()
    args.add("--input", src.path)
    args.add("--output", out.path)

    ctx.actions.run(
        executable = ctx.executable.tool,
        arguments = [args],
        env = {
            "PATH": python_bin.path.rsplit("/", 1)[0],
        },
        inputs = [src, python_bin],
        outputs = [out],
        mnemonic = "ExtractPairs",
        progress_message = "Extracting name pairs from %s" % src.short_path,
    )

    return DefaultInfo(files = depset([out]))

name_pairs = rule(
    implementation = _extract_pairs_impl,
    attrs = {
        "src": attr.label(
            allow_single_file = True,
            mandatory = True,
        ),
        "tool": attr.label(
            cfg = "exec",
            executable = True,
            mandatory = True,
        ),
        "_python": attr.label(
            cfg = "exec",
            allow_single_file = True,
            default = "@python//:bin/python3",
        ),
    },
)
