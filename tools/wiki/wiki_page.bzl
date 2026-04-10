"""Rule for extracting one page text from a MediaWiki XML dump."""

# The Hungarian "shorc" alphabet.
# Keys are as they appear in titles and text, values are used for build targets.
ABC_SHORT = {
    letter: letter.replace("Ö", "OE").replace("Ü", "UE").replace(",", "").lower()
    for letter in "A B C D E F G H I J K L M N O Ö P R S Sz T U Ü V W X,Y Z Zs".split(" ")
}

def _wiki_page_impl(ctx):
    src = ctx.file.src
    python_bin = ctx.file._python
    out = ctx.actions.declare_file(ctx.label.name + ".txt")

    args = ctx.actions.args()
    args.add("--input", src.path)
    args.add("--title", ctx.attr.title)
    args.add("--output", out.path)

    ctx.actions.run(
        executable = ctx.executable._tool,
        arguments = [args],
        env = {
            "PATH": python_bin.path.rsplit("/", 1)[0],
        },
        inputs = [src, python_bin],
        outputs = [out],
        tools = [ctx.executable._tool],
        mnemonic = "WikiPage",
        progress_message = "Extracting wiki page %s from %s" % (ctx.attr.title, src.short_path),
    )

    return DefaultInfo(files = depset([out]))

wiki_page = rule(
    implementation = _wiki_page_impl,
    attrs = {
        "src": attr.label(
            allow_single_file = [".xml"],
            mandatory = True,
        ),
        "title": attr.string(mandatory = True),
        "_python": attr.label(
            cfg = "exec",
            allow_single_file = True,
            default = "@python//:python",
        ),
        "_tool": attr.label(
            cfg = "exec",
            default = "//tools/wiki:wiki_page",
            executable = True,
        ),
    },
)
