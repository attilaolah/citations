_BUILD = """\
package(default_visibility = ["//visibility:public"])

filegroup(
    name = "file",
    srcs = glob(["**"], exclude = ["BUILD.bazel"]),
)
"""

_URLS_BUILD = """\
package(default_visibility = ["//visibility:public"])

exports_files(["urls.txt"])
"""

_IPFS_GATEWAYS = [
    "ipfs.io",
    "gateway.pinata.cloud",
    "dweb.link",
]

_WIKIBOOKS_HU_RAW_URL_BASE = "https://hu.wikibooks.org/w/index.php?title="

def _ipfs_mirror_urls(ipfs_cid):
    return ["https://%s/ipfs/%s" % (gateway, ipfs_cid) for gateway in _IPFS_GATEWAYS]

def _wikibooks_hu_raw_url(title):
    return _WIKIBOOKS_HU_RAW_URL_BASE + title + "&action=raw"

def _xz_source_repo_impl(repository_ctx):
    repository_ctx.download_and_extract(
        url = repository_ctx.attr.urls,
        sha256 = repository_ctx.attr.sha256,
        type = "xz",
        output = "file",
    )
    repository_ctx.file(
        "file/BUILD.bazel",
        content = _BUILD,
    )

_xz_source_repo = repository_rule(
    implementation = _xz_source_repo_impl,
    attrs = {
        "sha256": attr.string(mandatory = True),
        "urls": attr.string_list(mandatory = True),
    },
)

def _source_urls_repo_impl(repository_ctx):
    repository_ctx.file(
        "BUILD.bazel",
        content = _URLS_BUILD,
    )
    repository_ctx.file(
        "urls.txt",
        content = "".join(["%s\n" % url for url in repository_ctx.attr.urls]),
    )

_source_urls_repo = repository_rule(
    implementation = _source_urls_repo_impl,
    attrs = {
        "urls": attr.string_list(mandatory = True),
    },
)

def _sources_impl(module_ctx):
    source_urls = {}

    for module in module_ctx.modules:
        for external_source in module.tags.external_source:
            _xz_source_repo(
                name = external_source.name,
                urls = _ipfs_mirror_urls(external_source.ipfs_cid),
                sha256 = external_source.sha256,
            )
            source_urls[external_source.url] = None
        for wikibooks_hu_source in module.tags.wikibooks_hu_source:
            url = _wikibooks_hu_raw_url(wikibooks_hu_source.title)
            _xz_source_repo(
                name = wikibooks_hu_source.name,
                urls = _ipfs_mirror_urls(wikibooks_hu_source.ipfs_cid),
                sha256 = wikibooks_hu_source.sha256,
            )
            source_urls[url] = None

    _source_urls_repo(
        name = "source_urls",
        urls = sorted(source_urls.keys()),
    )

_external_source_tag = tag_class(
    attrs = {
        "ipfs_cid": attr.string(mandatory = True),
        "name": attr.string(mandatory = True),
        "sha256": attr.string(mandatory = True),
        "updated_on": attr.string(mandatory = True),
        "url": attr.string(mandatory = True),
    },
)

_wikibooks_hu_source_tag = tag_class(
    attrs = {
        "ipfs_cid": attr.string(mandatory = True),
        "name": attr.string(mandatory = True),
        "sha256": attr.string(mandatory = True),
        "title": attr.string(mandatory = True),
        "updated_on": attr.string(mandatory = True),
    },
)

sources = module_extension(
    implementation = _sources_impl,
    tag_classes = {
        "external_source": _external_source_tag,
        "wikibooks_hu_source": _wikibooks_hu_source_tag,
    },
)
