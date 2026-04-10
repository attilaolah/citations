"""Macros and rules for extracting, cleaning, and testing name-pair datasets."""

load("//tools/extract:name_pairs_clean.bzl", "name_pairs_clean")
load("//tools/extract:name_pairs_completeness_test.bzl", "name_pairs_completeness_test")
load("//tools/extract:name_pairs_test.bzl", "name_pairs_test")
load("//tools/extract:scientific_names.bzl", "scientific_names")

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
            default = "@python//:python",
        ),
    },
)

def name_pairs(name, src, tool, samples = None, ignore = None, **kwargs):
    """Build extraction output and companion validation targets for one source file.

    Args:
      name: Base name for generated targets.
      src: Label of the source input file to process.
      tool: Executable label used to extract raw name pairs.
      samples: Optional sample fixture label for `name_pairs_test`.
      ignore: Optional ignore-list label for completeness checks.
      **kwargs: Extra attributes forwarded to the underlying extraction rule.
    """
    _name_pairs(
        name = name,
        src = src,
        tool = tool,
        **kwargs
    )

    clean = "%s_clean" % name
    name_pairs_clean(
        name = clean,
        src = ":%s" % name,
        visibility = ["//:__subpackages__"],
    )

    scientific = "%s_scientific_names" % name
    scientific_names(
        name = scientific,
        basename = name,
        src = src,
    )

    name_pairs_completeness_test(
        name = "%s_completeness_test" % name,
        clean = ":%s" % clean,
        scientific_names = ":%s" % scientific,
        ignore = ignore,
    )

    if samples != None:
        name_pairs_test(
            name = "%s_test" % scientific,
            src = ":" + name,
            samples = samples,
        )
