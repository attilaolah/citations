"""CLI wrapper for selecting one wiki page from a MediaWiki dump."""

import html
from contextlib import suppress
from enum import StrEnum, auto
from typing import TYPE_CHECKING, override
from xml.sax.handler import ContentHandler

from defusedxml import sax

from tools.settings import IOSettings

if TYPE_CHECKING:
    from pathlib import Path
    from xml.sax.xmlreader import AttributesImpl

_REVISION_PATH_DEPTH = 2


def main() -> None:
    """Run the extraction CLI."""
    settings = _Settings.from_args()
    content = _extract_wiki_page_text(input_path=settings.input, title=settings.title)
    settings.output.write_text(content, encoding="utf-8")


class _Settings(IOSettings):
    """Settings for extracting one wiki page from a dump."""

    title: str


class _PageFoundError(Exception):
    """Raised internally to stop parsing once the requested page is found."""


class _PageNotFoundError(IndexError):
    """Raised when the requested page title does not exist in the XML dump."""

    def __init__(self, title: str) -> None:
        """Initialize the exception with the missing title."""
        super().__init__(f"page not found: {title!r}")


class _WikiNode(StrEnum):
    PAGE = auto()
    REVISION = auto()
    TEXT = auto()
    TITLE = auto()


class _WikiPageHandler(ContentHandler):
    def __init__(self, title: str) -> None:
        super().__init__()
        self._target_title = title
        self._path: list[_WikiNode | None] = []
        self._current_title_parts: list[str] | None = None
        self._current_text_parts: list[str] | None = None
        self._page_title = ""
        self.page_text = ""

    @staticmethod
    def _node(name: str) -> _WikiNode | None:
        local_name = name.rpartition(":")[2]
        with suppress(ValueError):
            return _WikiNode(local_name)
        return None

    @staticmethod
    def _title_matches(actual: str, expected: str) -> bool:
        if actual == expected:
            return True
        return actual.replace("_", " ") == expected.replace("_", " ")

    @override
    def startElement(self, name: str, attrs: AttributesImpl) -> None:
        del attrs
        node = self._node(name)
        self._path.append(node)

        if node is _WikiNode.PAGE:
            self._current_title_parts = None
            self._current_text_parts = None
            self._page_title = ""
            self.page_text = ""
            return

        if node is _WikiNode.TITLE and self._path[-2:] == [_WikiNode.PAGE, _WikiNode.TITLE]:
            self._current_title_parts = []
            return

        if (
            node is _WikiNode.TEXT
            and len(self._path) >= _REVISION_PATH_DEPTH
            and self._path[-_REVISION_PATH_DEPTH] is _WikiNode.REVISION
        ):
            self._current_text_parts = []

    @override
    def characters(self, content: str) -> None:
        if self._current_title_parts is not None:
            self._current_title_parts.append(content)
        if self._current_text_parts is not None:
            self._current_text_parts.append(content)

    @override
    def endElement(self, name: str) -> None:
        node = self._node(name)

        if node is _WikiNode.TITLE and self._current_title_parts is not None:
            self._page_title = "".join(self._current_title_parts)
            self._current_title_parts = None
        elif node is _WikiNode.TEXT and self._current_text_parts is not None:
            self.page_text = "".join(self._current_text_parts)
            self._current_text_parts = None
        elif node is _WikiNode.PAGE and self._title_matches(self._page_title, self._target_title):
            raise _PageFoundError

        self._path.pop()


def _extract_wiki_page_text(*, input_path: Path, title: str) -> str:
    """Extract one page body by title and decode XML entity escapes.

    Returns:
        Page text for the requested title.

    Raises:
        _PageNotFoundError: The input XML does not contain the requested page title.
    """
    handler = _WikiPageHandler(title=title)

    try:
        sax.parse(str(input_path), handler)
    except _PageFoundError:
        return html.unescape(handler.page_text)

    raise _PageNotFoundError(title)


if __name__ == "__main__":
    main()
