"""Unit tests for the async crawler."""

from __future__ import annotations

import httpx
import pytest
import respx

from sitesentry.config import ScanConfig
from sitesentry.crawler import Crawler, PermissionDeniedError, _looks_like_soft_404
from sitesentry.models import PageData
from sitesentry.scope import ScopeGuard


class TestCrawlerSafetyGates:
    @pytest.mark.asyncio
    async def test_permission_denied_without_flag(self) -> None:
        cfg = ScanConfig(
            target_url="http://127.0.0.1:8000", confirm_permission=False, allow_private=True
        )
        scope = ScopeGuard(cfg.target_url, allow_private=True)
        crawler = Crawler(cfg, scope)
        async with crawler:
            with pytest.raises(PermissionDeniedError):
                async for _ in crawler.crawl():
                    pass


class TestCrawlerFunctionality:
    @pytest.mark.asyncio
    async def test_crawl_bfs_and_max_pages(self) -> None:
        cfg = ScanConfig(
            target_url="http://127.0.0.1:8000",
            confirm_permission=True,
            max_pages=2,
            max_depth=2,
            allow_private=True,
            rate_limit=50.0,
        )
        scope = ScopeGuard(cfg.target_url, allow_private=True)

        with respx.mock(assert_all_called=False) as mock:
            mock.get("http://127.0.0.1:8000/robots.txt").mock(return_value=httpx.Response(404))
            mock.get(url__regex=r"http://127\.0\.0\.1:8000/[a-f0-9]{32}").mock(
                return_value=httpx.Response(404, text="Not Found")
            )
            mock.get("http://127.0.0.1:8000/").mock(
                return_value=httpx.Response(
                    200,
                    headers={"content-type": "text/html"},
                    text='<html><body><a href="/p1">Page 1</a><a href="/p2">Page 2</a></body></html>',
                )
            )
            mock.get("http://127.0.0.1:8000/p1").mock(
                return_value=httpx.Response(
                    200, headers={"content-type": "text/html"}, text="<html>Page 1</html>"
                )
            )
            mock.get("http://127.0.0.1:8000/p2").mock(
                return_value=httpx.Response(
                    200, headers={"content-type": "text/html"}, text="<html>Page 2</html>"
                )
            )

            pages: list[PageData] = []
            async with Crawler(cfg, scope) as crawler:
                async for page in crawler.crawl():
                    pages.append(page)

            assert len(pages) == 2
            assert pages[0].url == "http://127.0.0.1:8000/"
            assert pages[1].url == "http://127.0.0.1:8000/p1"

    @pytest.mark.asyncio
    async def test_robots_txt_disallow(self) -> None:
        cfg = ScanConfig(
            target_url="http://127.0.0.1:8000",
            confirm_permission=True,
            max_pages=5,
            allow_private=True,
            rate_limit=50.0,
            respect_robots=True,
            ignore_robots=False,
        )
        scope = ScopeGuard(cfg.target_url, allow_private=True)

        with respx.mock(assert_all_called=False) as mock:
            mock.get("http://127.0.0.1:8000/robots.txt").mock(
                return_value=httpx.Response(200, text="User-agent: *\nDisallow: /secret\n")
            )
            mock.get(url__regex=r"http://127\.0\.0\.1:8000/[a-f0-9]{32}").mock(
                return_value=httpx.Response(404)
            )
            mock.get("http://127.0.0.1:8000/").mock(
                return_value=httpx.Response(
                    200,
                    headers={"content-type": "text/html"},
                    text='<html><body><a href="/secret">Disallowed</a><a href="/allowed">Allowed</a></body></html>',
                )
            )
            mock.get("http://127.0.0.1:8000/secret").mock(
                return_value=httpx.Response(200, text="Secret")
            )
            mock.get("http://127.0.0.1:8000/allowed").mock(
                return_value=httpx.Response(200, text="Allowed")
            )

            pages: list[PageData] = []
            async with Crawler(cfg, scope) as crawler:
                async for page in crawler.crawl():
                    pages.append(page)

            crawled_urls = [p.url for p in pages]
            assert "http://127.0.0.1:8000/" in crawled_urls
            assert "http://127.0.0.1:8000/allowed" in crawled_urls
            assert "http://127.0.0.1:8000/secret" not in crawled_urls

    @pytest.mark.asyncio
    async def test_redirect_to_out_of_scope_is_not_followed(self) -> None:
        cfg = ScanConfig(
            target_url="http://127.0.0.1:8000",
            confirm_permission=True,
            max_pages=2,
            allow_private=True,
            rate_limit=50.0,
        )
        scope = ScopeGuard(cfg.target_url, allow_private=True)

        with respx.mock(assert_all_called=False) as mock:
            mock.get("http://127.0.0.1:8000/robots.txt").mock(return_value=httpx.Response(404))
            mock.get(url__regex=r"http://127\.0\.0\.1:8000/[a-f0-9]{32}").mock(
                return_value=httpx.Response(404)
            )
            # Redirect to external domain
            mock.get("http://127.0.0.1:8000/").mock(
                return_value=httpx.Response(302, headers={"location": "https://attacker.com/evil"})
            )

            pages: list[PageData] = []
            async with Crawler(cfg, scope) as crawler:
                async for page in crawler.crawl():
                    pages.append(page)

            assert len(pages) == 1
            assert pages[0].status_code == 302
            assert "https://attacker.com/evil" in pages[0].redirect_chain

    def test_looks_like_soft_404(self) -> None:
        soft_404_ref = PageData(
            url="http://example.com/rand123",
            status_code=200,
            body="<html>Not Found Custom</html>",
            content_length=100,
        )

        similar_page = PageData(
            url="http://example.com/.env",
            status_code=200,
            body="<html>Not Found Custom</html>",
            content_length=102,
        )
        assert _looks_like_soft_404(similar_page, soft_404_ref) is True

        different_status = PageData(
            url="http://example.com/.env",
            status_code=404,
            body="404",
            content_length=3,
        )
        assert _looks_like_soft_404(different_status, soft_404_ref) is False

        assert _looks_like_soft_404(similar_page, None) is False
