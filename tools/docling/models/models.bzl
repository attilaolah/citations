"""Rule for downloading and exposing Docling model artifacts for builds."""

ModelsInfo = provider(
    doc = "Directory containing Docling model artifacts.",
    fields = {
        "artifacts_dir": "Tree artifact directory produced by models().",
    },
)

def _models_impl(ctx):
    out = ctx.actions.declare_directory(ctx.label.name)

    args = ctx.actions.args()
    args.add("models")
    args.add("download")
    args.add("--output-dir", out.path)
    args.add("--quiet")
    if ctx.attr.all_models:
        args.add("--all")

    ctx.actions.run(
        executable = ctx.executable._docling_tools,
        arguments = [args],
        env = {
            "HF_HOME": "/tmp/huggingface",
            "HOME": "/tmp",
            "XDG_CACHE_HOME": "/tmp",
        },
        outputs = [out],
        mnemonic = "DoclingModels",
        progress_message = "Downloading docling model artifacts for %s" % ctx.label.name,
    )

    return [
        DefaultInfo(files = depset([out])),
        ModelsInfo(artifacts_dir = out),
    ]

models = rule(
    implementation = _models_impl,
    attrs = {
        "all_models": attr.bool(default = False),
        "_docling_tools": attr.label(
            cfg = "exec",
            default = "@docling//:docling-tools",
            executable = True,
        ),
    },
)
