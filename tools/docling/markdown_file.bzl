"""Rule for extracting normalized Markdown from document files via Docling."""

load("//tools/docling/models:models.bzl", "ModelsInfo")
load("//tools/python:actions.bzl", "run_py")

_SOFFICE_WRAPPER_TEMPLATE = """#!/usr/bin/env bash
exec "{soffice}" \
  -env:UserInstallation=file://{profile} \
  --headless \
  --nologo \
  --nolockcheck \
  --nodefault \
  --nofirststartwizard \
  "$@"
"""

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

    soffice_id = (ctx.label.package + "_" + ctx.label.name).replace("/", "_")
    soffice_home = "/tmp/docling-libreoffice-home-" + soffice_id
    soffice_profile = "/tmp/docling-libreoffice-profile-" + soffice_id
    soffice_wrapper = ctx.actions.declare_file(ctx.label.name + ".soffice.sh")
    ctx.actions.write(
        output = soffice_wrapper,
        content = _SOFFICE_WRAPPER_TEMPLATE.format(
            soffice = ctx.executable._soffice.path,
            profile = soffice_profile,
        ),
        is_executable = True,
    )

    ctx.actions.run(
        executable = ctx.executable._docling,
        arguments = [args],
        env = {
            "DOCLING_LIBREOFFICE_CMD": soffice_wrapper.path,
            "HF_HOME": "/tmp/huggingface",
            "HOME": soffice_home,
            "XDG_CACHE_HOME": "/tmp",
        },
        inputs = inputs,
        outputs = [raw_out],
        tools = [ctx.executable._soffice, soffice_wrapper],
        mnemonic = "DoclingMarkdown",
        progress_message = "Extracting Markdown from %s" % src.short_path,
    )

    clean_args = ctx.actions.args()
    clean_args.add("--input", raw_out.path)
    clean_args.add("--output", out.path)
    run_py(
        ctx,
        executable = ctx.executable._markdown_cleanup,
        arguments = [clean_args],
        inputs = [raw_out],
        outputs = [out],
        tools = [ctx.executable._markdown_cleanup],
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
            cfg = "exec",
            default = "//tools/docling:markdown_cleanup",
            executable = True,
        ),
        "_python": attr.label(
            cfg = "exec",
            allow_single_file = True,
            default = "@python//:python",
        ),
        "_soffice": attr.label(
            cfg = "exec",
            default = "@libreoffice//:soffice",
            executable = True,
        ),
    },
)
