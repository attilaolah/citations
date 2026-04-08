from typing import Protocol, Self

class HtmlElement(Protocol):
    def xpath(self, expr: str) -> list[Self]: ...
    def text_content(self) -> str: ...

def fromstring(
    html: bytes | str,
    base_url: str | None = ...,
    parser: object | None = ...,
    **kw: object,
) -> HtmlElement: ...
