"""Base class and context for all security checks."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import httpx

from sitesentry.config import ScanConfig
from sitesentry.models import Finding, PageData


@dataclass
class ScanContext:
    """Data available to every check during a scan."""

    target_url: str
    pages: list[PageData]
    soft_404: PageData | None
    config: ScanConfig
    http_client: httpx.AsyncClient


class BaseCheck(ABC):
    """Abstract base for all security checks.

    Subclasses must define class-level ``id`` and ``title`` attributes,
    and implement ``run(context) -> list[Finding]``.
    """

    id: str = ""
    title: str = ""

    @abstractmethod
    async def run(self, context: ScanContext) -> list[Finding]:
        """Run the check against *context* and return a list of findings."""
        ...

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        # Ensure concrete subclasses define id and title
        if not getattr(cls, "__abstractmethods__", None):
            if not cls.id:
                raise TypeError(f"{cls.__name__} must define a class-level 'id' attribute")
            if not cls.title:
                raise TypeError(f"{cls.__name__} must define a class-level 'title' attribute")
