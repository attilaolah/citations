load("//tools/docling/models:models.bzl", "ModelsInfo")

def _markdown_file_impl(ctx):
    src = ctx.file.src
    raw_out = ctx.actions.declare_file(ctx.label.name + ".docling.md")
    out = ctx.actions.declare_file(ctx.label.name + ".md")

    from_format = src.extension.lower()

    # Name input to match expected markdown basename in the output directory.
    local_input = ctx.actions.declare_file(ctx.label.name + ".docling." + from_format)
    ctx.actions.symlink(
        output = local_input,
        target_file = src,
    )

    inputs = [local_input]
    artifacts_dir = None
    if ctx.attr.models != None:
        artifacts_dir = ctx.attr.models[ModelsInfo].artifacts_dir
        inputs.append(artifacts_dir)

    args = ctx.actions.args()
    args.add("--from", from_format)
    args.add("--to", "md")
    args.add("--image-export-mode", "placeholder")
    args.add("--device", ctx.attr.device)
    if artifacts_dir != None:
        args.add("--artifacts-path", artifacts_dir.path)
    if from_format == "pdf":
        args.add("--ocr-lang", ctx.attr.ocr_lang)
    args.add("--output", raw_out.dirname)
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
        outputs = [raw_out],
        mnemonic = "DoclingMarkdown",
        progress_message = "Extracting Markdown from %s" % src.short_path,
    )

    clean_args = ctx.actions.args()
    clean_args.add("--input", raw_out.path)
    clean_args.add("--output", out.path)
    ctx.actions.run(
        executable = ctx.file._python,
        arguments = [ctx.file._markdown_cleanup.path, clean_args],
        inputs = [raw_out, ctx.file._markdown_cleanup, ctx.file._python],
        outputs = [out],
        mnemonic = "CleanMarkdown",
        progress_message = "Cleaning extracted Markdown for %s" % src.short_path,
    )

    return DefaultInfo(files = depset([out]))

markdown_file = rule(
    implementation = _markdown_file_impl,
    attrs = {
        "device": attr.string(
            default = "auto",
            values = ["auto", "cpu", "cuda", "mps", "xpu"],
        ),
        "models": attr.label(
            providers = [ModelsInfo],
        ),
        "ocr_lang": attr.string(default = "hu"),
        "src": attr.label(
            allow_single_file = [".pdf", ".pptx", ".docx"],
            mandatory = True,
        ),
        "_docling": attr.label(
            cfg = "exec",
            default = "@docling//:docling",
            executable = True,
        ),
        "_markdown_cleanup": attr.label(
            allow_single_file = True,
            default = "//tools/docling:markdown_cleanup.py",
        ),
        "_python": attr.label(
            cfg = "exec",
            allow_single_file = True,
            default = "@python//:bin/python",
        ),
    },
)
