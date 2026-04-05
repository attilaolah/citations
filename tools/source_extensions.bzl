load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_file")

_IPFS_GATEWAYS = [
    "ipfs.io",
    "gateway.pinata.cloud",
    "dweb.link",
]

_WIKIBOOKS_HU_RAW_URL_BASE = "https://hu.wikibooks.org/w/index.php?title="

def _ipfs_mirror_urls(ipfs_cid):
    return ["https://%s/ipfs/%s" % (gateway, ipfs_cid) for gateway in _IPFS_GATEWAYS]

def _downloaded_file_path(url):
    url_without_fragment = url.split("#")[0]
    url_without_query = url_without_fragment.split("?")[0]
    path = url_without_query.rsplit("/", 1)[-1]
    ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
    if ext:
        return "downloaded.%s" % ext
    return "downloaded"

def _wikibooks_hu_raw_url(title):
    return _WIKIBOOKS_HU_RAW_URL_BASE + title + "&action=raw"

def _sources_impl(module_ctx):
    for module in module_ctx.modules:
        for external_source in module.tags.external_source:
            http_file(
                name = external_source.name,
                urls = _ipfs_mirror_urls(external_source.ipfs_cid),
                sha256 = external_source.sha256,
                downloaded_file_path = _downloaded_file_path(external_source.url),
            )
        for wikibooks_hu_source in module.tags.wikibooks_hu_source:
            url = _wikibooks_hu_raw_url(wikibooks_hu_source.title)
            http_file(
                name = wikibooks_hu_source.name,
                urls = _ipfs_mirror_urls(wikibooks_hu_source.ipfs_cid),
                sha256 = wikibooks_hu_source.sha256,
                downloaded_file_path = _downloaded_file_path(url),
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
