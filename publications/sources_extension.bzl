load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_file")

_IPFS_GATEWAYS = [
    "ipfs.io",
    "gateway.pinata.cloud",
    "dweb.link",
]

def _ipfs_mirror_urls(ipfs_cid):
    return ["https://%s/ipfs/%s" % (gateway, ipfs_cid) for gateway in _IPFS_GATEWAYS]

def _sources_impl(module_ctx):
    for module in module_ctx.modules:
        for publication in module.tags.publication:
            http_file(
                name = publication.name,
                urls = _ipfs_mirror_urls(publication.ipfs_cid) + [publication.url],
                sha256 = publication.sha256,
            )

_publication_tag = tag_class(
    attrs = {
        "ipfs_cid": attr.string(mandatory = True),
        "name": attr.string(mandatory = True),
        "sha256": attr.string(mandatory = True),
        "url": attr.string(mandatory = True),
    },
)

sources = module_extension(
    implementation = _sources_impl,
    tag_classes = {
        "publication": _publication_tag,
    },
)
