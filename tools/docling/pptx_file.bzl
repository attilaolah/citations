"""Rule for converting legacy PPT files to PPTX via LibreOffice."""

def _pptx_file_impl(ctx):
    src = ctx.file.src
    out = ctx.actions.declare_file(ctx.label.name + ".pptx")
    soffice = ctx.executable._soffice

    # LibreOffice writes "<input-basename>.pptx" to --outdir.
    # Set the local input basename to match the declared output basename, so soffice writes directly to the output.
    local_input = ctx.actions.declare_file(ctx.label.name + ".ppt")

    ctx.actions.symlink(
        output = local_input,
        target_file = src,
    )

    args = ctx.actions.args()
    args.add("-env:UserInstallation=file:///tmp/libreoffice-profile-" + ctx.label.name)
    args.add("--headless")
    args.add("--nologo")
    args.add("--nolockcheck")
    args.add("--nodefault")
    args.add("--nofirststartwizard")
    args.add("--convert-to", "pptx")
    args.add("--outdir", out.dirname)
    args.add(local_input.path)

    ctx.actions.run(
        executable = soffice,
        arguments = [args],
        env = {
            "DBUS_SESSION_BUS_ADDRESS": "disabled:",
            "HOME": "/tmp/libreoffice-" + ctx.label.name,
        },
        inputs = [local_input],
        outputs = [out],
        mnemonic = "PptToPptx",
        progress_message = "Converting PPT to PPTX for %s" % src.short_path,
    )

    return DefaultInfo(files = depset([out]))

pptx_file = rule(
    implementation = _pptx_file_impl,
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
