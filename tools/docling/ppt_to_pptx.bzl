def _ppt_to_pptx_impl(ctx):
    src = ctx.file.src
    out = ctx.actions.declare_file(ctx.label.name + ".pptx")
    soffice = ctx.executable._soffice

    # LibreOffice writes "<input-basename>.pptx" to --outdir.
    # Set the local input basename to match the declared output basename,
    # so soffice writes directly to the declared output path.
    local_input = ctx.actions.declare_file(ctx.label.name + ".ppt")

    ctx.actions.symlink(
        output = local_input,
        target_file = src,
    )

    soffice_args = ctx.actions.args()
    soffice_args.add("--headless")
    soffice_args.add("--nologo")
    soffice_args.add("--nolockcheck")
    soffice_args.add("--nodefault")
    soffice_args.add("--nofirststartwizard")
    soffice_args.add("--convert-to")
    soffice_args.add("pptx")
    soffice_args.add("--outdir")
    soffice_args.add(out.dirname)
    soffice_args.add(local_input.path)

    ctx.actions.run(
        executable = soffice,
        arguments = [soffice_args],
        env = {
            "HOME": "/tmp",
        },
        inputs = [local_input],
        outputs = [out],
        mnemonic = "PptToPptx",
        progress_message = "Converting PPT to PPTX for %s" % src.short_path,
    )

    return DefaultInfo(files = depset([out]))

_ppt_to_pptx = rule(
    implementation = _ppt_to_pptx_impl,
    attrs = {
        "src": attr.label(
            allow_single_file = True,
            mandatory = True,
        ),
        "_soffice": attr.label(
            cfg = "exec",
            default = "@libreoffice//:soffice",
            executable = True,
        ),
    },
)

def ppt_to_pptx(name, src):
    _ppt_to_pptx(
        name = name,
        src = src,
    )
