"""Bzlmod extension for Wikimedia XML dump sources."""

_BUILD = """\
package(default_visibility = ["@@//external_sources/wikibooks_hu:__subpackages__"])

filegroup(
    name = "file",
    srcs = ["source.xml"],
)
"""

_WIKIMEDIA_BASE = "https://dumps.wikimedia.org/other/mediawiki_content_current"

def _wikimedia_dump_repo_impl(repository_ctx):
    dump_filename = "%s-%s-p1p%d.xml.bz2" % (
        repository_ctx.attr.site,
        repository_ctx.attr.timestamp,
        repository_ctx.attr.pages,
    )
    repository_ctx.download_and_extract(
        url = "%s/%s/%s/xml/bzip2/%s" % (
            _WIKIMEDIA_BASE,
            repository_ctx.attr.site,
            repository_ctx.attr.timestamp,
            dump_filename,
        ),
        sha256 = repository_ctx.attr.sha256,
        type = "bz2",
        output = "file/raw",
    )

    repository_ctx.symlink(
        "file/raw/" + dump_filename[:-4],
        "file/source.xml",
    )
    repository_ctx.file(
        "file/BUILD.bazel",
        content = _BUILD,
    )

_wikimedia_dump_repo = repository_rule(
    implementation = _wikimedia_dump_repo_impl,
    attrs = {
        "pages": attr.int(mandatory = True),
        "sha256": attr.string(mandatory = True),
        "site": attr.string(mandatory = True),
        "timestamp": attr.string(mandatory = True),
    },
)

def _wiki_sources_impl(module_ctx):
    for module in module_ctx.modules:
        for wikimedia_dump in module.tags.wikimedia_dump:
            _wikimedia_dump_repo(
                name = wikimedia_dump.site + "_xml",
                pages = wikimedia_dump.pages,
                sha256 = wikimedia_dump.sha256,
                site = wikimedia_dump.site,
                timestamp = wikimedia_dump.timestamp,
            )

_wikimedia_dump_tag = tag_class(
    attrs = {
        "pages": attr.int(mandatory = True),
        "sha256": attr.string(mandatory = True),
        "site": attr.string(mandatory = True),
        "timestamp": attr.string(mandatory = True),
    },
)

wiki_sources = module_extension(
    implementation = _wiki_sources_impl,
    tag_classes = {
        "wikimedia_dump": _wikimedia_dump_tag,
    },
)
