"""Rule for extracting global scientific names from source publication content."""

def _global_names_impl(ctx):
    src = ctx.file.src
    gnfinder = ctx.file.gnfinder
    python_bin = ctx.file._python
    extractor = ctx.executable._extractor
    out = ctx.actions.declare_file(ctx.attr.basename + ".names.json")

    args = ctx.actions.args()
    args.add("--input", src.path)
    args.add("--output", out.path)
    args.add("--gnfinder", gnfinder.path)

    ctx.actions.run(
        executable = extractor,
        arguments = [args],
        env = {
            "PATH": python_bin.path.rsplit("/", 1)[0],
        },
        inputs = [src, gnfinder, python_bin],
        outputs = [out],
        tools = [extractor],
        mnemonic = "GlobalNames",
        progress_message = "Extracting global names from %s" % src.short_path,
    )

    return DefaultInfo(files = depset([out]))

global_names = rule(
    implementation = _global_names_impl,
    attrs = {
        "basename": attr.string(mandatory = True),
        "gnfinder": attr.label(
            cfg = "exec",
            allow_single_file = True,
            default = "@gnfinder//:gnfinder",
        ),
        "src": attr.label(
            allow_single_file = True,
            mandatory = True,
        ),
        "_extractor": attr.label(
            cfg = "exec",
            executable = True,
            default = "//tools/extract:global_names",
        ),
        "_python": attr.label(
            cfg = "exec",
            allow_single_file = True,
            default = "@python//:python",
        ),
    },
)
