from typing import Callable, Literal, TypeVar

_T = TypeVar("_T", bound=Callable[..., object])

def fixture(
    *,
    scope: Literal["function", "class", "module", "package", "session"] = "function",
) -> Callable[[_T], _T]: ...
