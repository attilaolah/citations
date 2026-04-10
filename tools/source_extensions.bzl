"""Bzlmod extension for external source repositories and URL manifests."""

_BUILD = """\
package(default_visibility = ["@@//:__subpackages__"])

filegroup(
    name = "file",
    srcs = ["%s"],
)
"""

_URLS_BUILD = """\
package(default_visibility = ["@@//:__subpackages__"])
"""

_IPFS_GATEWAYS = [
    "ipfs.io",
    "gateway.pinata.cloud",
    "dweb.link",
]

_WIKIMEDIA_BASE = "https://dumps.wikimedia.org/other/mediawiki_content_current"

def _ipfs_mirror_urls(ipfs_cid):
    return ["https://%s/ipfs/%s" % (gateway, ipfs_cid) for gateway in _IPFS_GATEWAYS]

def _url_extension(url):
    path = url.split("?")[0].split("#")[0]
    filename = path.rsplit("/", 1)[-1]
    if "." not in filename:
        return ".txt"
    return "." + filename.rsplit(".", 1)[-1].lower()

def _wikimedia_dump_base_url(site, timestamp):
    return "%s/%s/%s/xml/bzip2" % (_WIKIMEDIA_BASE, site, timestamp)

def _wikimedia_dump_archive_filename(site, timestamp, pages):
    return "%s-%s-p1p%d.xml.bz2" % (site, timestamp, pages)

def _xz_source_repo_impl(repository_ctx):
    output_file = "source" + repository_ctx.attr.extension
    repository_ctx.download_and_extract(
        url = repository_ctx.attr.urls,
        sha256 = repository_ctx.attr.sha256,
        type = "xz",
        output = "file/raw",
    )
    repository_ctx.symlink(
        "file/raw/" + repository_ctx.attr.archive_basename,
        "file/" + output_file,
    )
    repository_ctx.file(
        "file/BUILD.bazel",
        content = _BUILD % output_file,
    )

_xz_source_repo = repository_rule(
    implementation = _xz_source_repo_impl,
    attrs = {
        "archive_basename": attr.string(mandatory = True),
        "extension": attr.string(mandatory = True),
        "sha256": attr.string(mandatory = True),
        "urls": attr.string_list(mandatory = True),
    },
)

def _wikimedia_dump_repo_impl(repository_ctx):
    dump_filename = _wikimedia_dump_archive_filename(
        repository_ctx.attr.site,
        repository_ctx.attr.timestamp,
        repository_ctx.attr.pages,
    )
    repository_ctx.download_and_extract(
        url = _wikimedia_dump_base_url(repository_ctx.attr.site, repository_ctx.attr.timestamp) + "/" + dump_filename,
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
        content = _BUILD % "source.xml",
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

def _cached_urls_repo_impl(repository_ctx):
    repository_ctx.file(
        "BUILD.bazel",
        content = _URLS_BUILD,
    )
    repository_ctx.file(
        "urls.txt",
        content = "".join(["%s\n" % url for url in repository_ctx.attr.urls]),
    )

_cached_urls_repo = repository_rule(
    implementation = _cached_urls_repo_impl,
    attrs = {
        "urls": attr.string_list(mandatory = True),
    },
)

def _sources_impl(module_ctx):
    cached_urls = {}

    for module in module_ctx.modules:
        for external_source in module.tags.external_source:
            extension = external_source.extension or _url_extension(external_source.url)
            _xz_source_repo(
                name = external_source.name,
                archive_basename = external_source.ipfs_cid,
                extension = extension,
                urls = _ipfs_mirror_urls(external_source.ipfs_cid),
                sha256 = external_source.sha256,
            )
            cached_urls[external_source.url] = None

        for wikimedia_dump in module.tags.wikimedia_dump:
            _wikimedia_dump_repo(
                name = wikimedia_dump.site + "_xml",
                pages = wikimedia_dump.pages,
                sha256 = wikimedia_dump.sha256,
                site = wikimedia_dump.site,
                timestamp = wikimedia_dump.timestamp,
            )

    _cached_urls_repo(
        name = "cached_urls",
        urls = sorted(cached_urls.keys()),
    )

_external_source_tag = tag_class(
    attrs = {
        "extension": attr.string(),
        "ipfs_cid": attr.string(mandatory = True),
        "name": attr.string(mandatory = True),
        "sha256": attr.string(mandatory = True),
        "updated_on": attr.string(mandatory = True),
        "url": attr.string(mandatory = True),
    },
)

_wikimedia_dump_tag = tag_class(
    attrs = {
        "pages": attr.int(mandatory = True),
        "sha256": attr.string(mandatory = True),
        "site": attr.string(mandatory = True),
        "timestamp": attr.string(mandatory = True),
    },
)

sources = module_extension(
    implementation = _sources_impl,
    tag_classes = {
        "external_source": _external_source_tag,
        "wikimedia_dump": _wikimedia_dump_tag,
    },
)
