def _name_pairs_clean_impl(ctx):
    src = ctx.file.src
    python_bin = ctx.file._python
    cleaner = ctx.executable._cleaner
    gnparser = ctx.file.gnparser
    out = ctx.actions.declare_file(ctx.label.name + ".json")

    args = ctx.actions.args()
    args.add("--input", src.path)
    args.add("--output", out.path)
    args.add("--gnparser", gnparser.path)

    ctx.actions.run(
        executable = cleaner,
        arguments = [args],
        env = {
            "PATH": python_bin.path.rsplit("/", 1)[0],
        },
        inputs = [src, gnparser, python_bin],
        outputs = [out],
        tools = [cleaner],
        mnemonic = "CleanNamePairs",
        progress_message = "Cleaning name pairs from %s" % src.short_path,
    )

    return DefaultInfo(files = depset([out]))

name_pairs_clean = rule(
    implementation = _name_pairs_clean_impl,
    attrs = {
        "gnparser": attr.label(
            cfg = "exec",
            allow_single_file = True,
            default = "@gnparser//:bin/gnparser",
        ),
        "src": attr.label(
            allow_single_file = True,
            mandatory = True,
        ),
        "_cleaner": attr.label(
            cfg = "exec",
            executable = True,
            default = "//tools/extract:name_pairs_clean_tool",
        ),
        "_python": attr.label(
            cfg = "exec",
            allow_single_file = True,
            default = "@python//:bin/python3",
        ),
    },
)
