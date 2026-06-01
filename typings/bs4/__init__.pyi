"""Minimal type stubs for BeautifulSoup4 (bs4) — strict-mode compatible."""

from typing import Any

class BeautifulSoup:
    def __init__(
        self,
        markup: str | bytes = ...,
        features: str | None = ...,
        builder: Any = ...,
        parse_only: Any = ...,
        from_encoding: str | None = ...,
        exclude_encodings: list[str] | None = ...,
        **kwargs: Any,
    ) -> None: ...
    def find_all(
        self,
        name: Any = ...,
        attrs: dict[str, Any] = ...,
        recursive: bool = ...,
        string: Any = ...,
        limit: int | None = ...,
        **kwargs: Any,
    ) -> list[Any]: ...
    def find(self, name: Any = ..., attrs: dict[str, Any] = ..., **kwargs: Any) -> Any: ...
    def select(self, selector: str, **kwargs: Any) -> list[Any]: ...
    def get_text(self, separator: str = ..., strip: bool = ..., types: Any = ...) -> str: ...
    @property
    def string(self) -> str | None: ...
    @property
    def text(self) -> str: ...
