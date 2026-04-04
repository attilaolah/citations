def _markdown_file_impl(ctx):
    src = ctx.file.src
    out = ctx.actions.declare_file(ctx.label.name + ".md")

    from_format = src.extension.lower()

    # Name input to match expected markdown basename in the output directory.
    local_input = ctx.actions.declare_file(ctx.label.name + "." + from_format)
    ctx.actions.symlink(
        output = local_input,
        target_file = src,
    )

    inputs = [local_input]
    artifacts_dir = None
    if ctx.file.models_tar != None:
        artifacts_dir = ctx.actions.declare_directory(ctx.label.name + "_artifacts")
        ctx.actions.run_shell(
            command = """
set -euo pipefail
mkdir -p "$1"
tar -C "$1" -xf "$2"
""",
            arguments = [artifacts_dir.path, ctx.file.models_tar.path],
            inputs = [ctx.file.models_tar],
            outputs = [artifacts_dir],
            mnemonic = "UnpackDoclingModels",
            progress_message = "Unpacking docling model artifacts for %s" % ctx.label.name,
        )
        inputs.append(artifacts_dir)

    args = ctx.actions.args()
    args.add("--from", from_format)
    args.add("--to", "md")
    args.add("--image-export-mode", "placeholder")
    args.add("--device", ctx.attr.device)
    if artifacts_dir != None:
        args.add("--artifacts-path", artifacts_dir.path)
    args.add("--output", out.dirname)
    args.add(local_input.path)

    ctx.actions.run(
        executable = ctx.executable._docling,
        arguments = [args],
        env = {
            "HF_HOME": "/tmp/huggingface",
            "HOME": "/tmp",
            "XDG_CACHE_HOME": "/tmp",
        },
        inputs = inputs,
        outputs = [out],
        mnemonic = "DoclingMarkdown",
        progress_message = "Extracting Markdown from %s" % src.short_path,
    )

    return DefaultInfo(files = depset([out]))

markdown_file = rule(
    implementation = _markdown_file_impl,
    attrs = {
        "device": attr.string(
            default = "auto",
            values = ["auto", "cpu", "cuda", "mps", "xpu"],
        ),
        "models_tar": attr.label(allow_single_file = True),
        "src": attr.label(
            allow_single_file = [".pdf", ".pptx"],
            mandatory = True,
        ),
        "_docling": attr.label(
            cfg = "exec",
            default = "@docling//:docling",
            executable = True,
        ),
    },
)
