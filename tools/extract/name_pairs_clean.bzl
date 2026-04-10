"""Rule for cleaning extracted name pairs with gnparser-backed normalization."""

def _name_pairs_clean_impl(ctx):
    src = ctx.file.src
    python_bin = ctx.file._python
    cleaner = ctx.executable._cleaner
    gnparser = ctx.file.gnparser
    basename = ctx.label.name
    if basename.endswith("_clean"):
        basename = basename[:-len("_clean")]
    out = ctx.actions.declare_file(basename + ".clean.json")

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
            default = "@gnparser//:gnparser",
        ),
        "src": attr.label(
            allow_single_file = True,
            mandatory = True,
        ),
        "_cleaner": attr.label(
            cfg = "exec",
            executable = True,
            default = "//tools/extract:name_pairs_clean",
        ),
        "_python": attr.label(
            cfg = "exec",
            allow_single_file = True,
            default = "@python//:python",
        ),
    },
)
