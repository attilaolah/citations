"""Rule for converting legacy DOC files to DOCX via LibreOffice."""

def _docx_file_impl(ctx):
    src = ctx.file.src
    out = ctx.actions.declare_file(ctx.label.name + ".docx")
    soffice = ctx.executable._soffice

    # LibreOffice writes "<input-basename>.docx" to --outdir.
    # Set the local input basename to match the declared output basename, so soffice writes directly to the output.
    local_input = ctx.actions.declare_file(ctx.label.name + ".doc")

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
    args.add("--convert-to", "docx")
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
        mnemonic = "DocToDocx",
        progress_message = "Converting DOC to DOCX for %s" % src.short_path,
    )

    return DefaultInfo(files = depset([out]))

docx_file = rule(
    implementation = _docx_file_impl,
    attrs = {
        "src": attr.label(
            allow_single_file = [".doc"],
            mandatory = True,
        ),
        "_soffice": attr.label(
            cfg = "exec",
            default = "@libreoffice//:soffice",
            executable = True,
        ),
    },
)
