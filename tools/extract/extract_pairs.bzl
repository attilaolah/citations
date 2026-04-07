load("//tools/extract:global_names.bzl", "global_names")
load("//tools/extract:name_pairs_clean.bzl", "name_pairs_clean")
load("//tools/extract:name_pairs_completeness_test.bzl", "name_pairs_completeness_test")
load("//tools/extract:name_pairs_test.bzl", "name_pairs_test")

def _extract_pairs_impl(ctx):
    src = ctx.file.src
    python_bin = ctx.file._python
    out = ctx.actions.declare_file(ctx.label.name + ".json")

    args = ctx.actions.args()
    args.add("--input", src.path)
    args.add("--output", out.path)

    ctx.actions.run(
        executable = ctx.executable.tool,
        arguments = [args],
        env = {
            "PATH": python_bin.path.rsplit("/", 1)[0],
        },
        inputs = [src, python_bin],
        outputs = [out],
        mnemonic = "ExtractPairs",
        progress_message = "Extracting name pairs from %s" % src.short_path,
    )

    return DefaultInfo(files = depset([out]))

_name_pairs = rule(
    implementation = _extract_pairs_impl,
    attrs = {
        "src": attr.label(
            allow_single_file = True,
            mandatory = True,
        ),
        "tool": attr.label(
            cfg = "exec",
            executable = True,
            mandatory = True,
        ),
        "_python": attr.label(
            cfg = "exec",
            allow_single_file = True,
            default = "@python//:bin/python3",
        ),
    },
)

def name_pairs(name, src, tool, samples = None, ignore = None, **kwargs):
    _name_pairs(
        name = name,
        src = src,
        tool = tool,
        **kwargs
    )

    name_pairs_clean(
        name = name + "_clean",
        src = ":" + name,
    )

    global_names(
        name = name + "_gn",
        basename = name,
        src = src,
    )

    name_pairs_completeness_test(
        name = name + "_completeness_test",
        clean = ":" + name + "_clean",
        global_names = ":" + name + "_gn",
        ignore = ignore,
    )

    if samples != None:
        name_pairs_test(
            name = name + "_test",
            src = ":" + name,
            samples = samples,
        )
