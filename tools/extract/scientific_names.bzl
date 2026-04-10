"""Rule for extracting global scientific names from source publication content."""

load("//tools/python:actions.bzl", "run_py")

def _scientific_names_impl(ctx):
    src = ctx.file.src
    gnfinder = ctx.file.gnfinder
    extractor = ctx.executable._extractor
    out = ctx.actions.declare_file(ctx.attr.basename + ".names.json")

    args = ctx.actions.args()
    args.add("--input", src.path)
    args.add("--output", out.path)
    args.add("--gnfinder", gnfinder.path)

    run_py(
        ctx,
        executable = extractor,
        arguments = [args],
        inputs = [src, gnfinder],
        outputs = [out],
        tools = [extractor],
        mnemonic = "ScientificNames",
        progress_message = "Extracting scientific names from %s" % src.short_path,
    )

    return DefaultInfo(files = depset([out]))

scientific_names = rule(
    implementation = _scientific_names_impl,
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
            default = "//tools/extract:scientific_names",
        ),
        "_python": attr.label(
            cfg = "exec",
            allow_single_file = True,
            default = "@python//:python",
        ),
    },
)
