"""Shared HTTP fetch layer with disk caching, rate limiting, and robots.txt compliance."""

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx

from backend.config import settings

logger = logging.getLogger(__name__)


@dataclass
class FetchResult:
    url: str
    status_code: int
    text: str
    from_cache: bool = False
    is_blocked: bool = False
    error: str | None = None


class RateLimiter:
    def __init__(self, default_delay: float = 1.0) -> None:
        self.default_delay = default_delay
        self.last_request_times: dict[str, float] = {}
        self.locks: dict[str, asyncio.Lock] = {}

    async def acquire(self, domain: str) -> None:
        if domain not in self.locks:
            self.locks[domain] = asyncio.Lock()

        async with self.locks[domain]:
            now = time.monotonic()
            last_time = self.last_request_times.get(domain, 0.0)
            elapsed = now - last_time
            if elapsed < self.default_delay:
                sleep_duration = self.default_delay - elapsed
                await asyncio.sleep(sleep_duration)
            self.last_request_times[domain] = time.monotonic()


class RobotsCache:
    def __init__(self, user_agent: str) -> None:
        self.user_agent = user_agent
        self.parsers: dict[str, RobotFileParser] = {}
        self.lock = asyncio.Lock()

    async def can_fetch(self, url: str, client: httpx.AsyncClient) -> bool:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if not domain:
            return True

        async with self.lock:
            if domain in self.parsers:
                return self.parsers[domain].can_fetch(self.user_agent, url)

        # Attempt to read robots.txt
        robots_url = f"{parsed.scheme}://{domain}/robots.txt"
        parser = RobotFileParser()
        try:
            resp = await client.get(robots_url, timeout=5.0)
            if resp.status_code == 200:
                parser.parse(resp.text.splitlines())
            else:
                # If robots.txt returns 404 or cannot be reached, allow crawling
                parser.allow_all = True
        except Exception:
            parser.allow_all = True

        async with self.lock:
            self.parsers[domain] = parser
            return parser.can_fetch(self.user_agent, url)


class DiskCache:
    def __init__(self, cache_dir: str | Path) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, url: str) -> Path:
        url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{url_hash}.json"

    def get(self, url: str, max_age_seconds: float = 86400.0) -> FetchResult | None:
        path = self._get_cache_path(url)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            cached_at = data.get("timestamp", 0.0)
            if time.time() - cached_at > max_age_seconds:
                return None
            return FetchResult(
                url=url,
                status_code=data.get("status_code", 200),
                text=data.get("text", ""),
                from_cache=True,
            )
        except Exception as exc:
            logger.warning(f"Failed to read disk cache for {url}: {exc}")
            return None

    def set(self, url: str, status_code: int, text: str) -> None:
        path = self._get_cache_path(url)
        try:
            data = {
                "url": url,
                "status_code": status_code,
                "text": text,
                "timestamp": time.time(),
            }
            path.write_text(json.dumps(data), encoding="utf-8")
        except Exception as exc:
            logger.warning(f"Failed to write disk cache for {url}: {exc}")


class SharedFetcher:
    def __init__(
        self,
        cache_dir: str | None = None,
        rate_limit_delay: float | None = None,
        timeout: float | None = None,
    ) -> None:
        self.cache = DiskCache(cache_dir or settings.HTTP_CACHE_DIR)
        self.rate_limiter = RateLimiter(rate_limit_delay or settings.RATE_LIMIT_DELAY_SECONDS)
        self.timeout = timeout or settings.HTTP_TIMEOUT_SECONDS
        self.user_agent = settings.USER_AGENT
        self.robots = RobotsCache(self.user_agent)

    async def fetch(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        use_cache: bool = True,
        cache_ttl_seconds: float = 86400.0,
        respect_robots: bool = True,
        timeout: float | None = None,
    ) -> FetchResult:
        if use_cache:
            cached = self.cache.get(url, max_age_seconds=cache_ttl_seconds)
            if cached:
                return cached

        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        req_headers = {"User-Agent": self.user_agent}
        if headers:
            req_headers.update(headers)

        async with httpx.AsyncClient(
            timeout=timeout or self.timeout, follow_redirects=True
        ) as client:
            if respect_robots:
                allowed = await self.robots.can_fetch(url, client)
                if not allowed:
                    logger.info(f"Access to {url} disallowed by robots.txt")
                    return FetchResult(
                        url=url,
                        status_code=403,
                        text="",
                        is_blocked=True,
                        error="Disallowed by robots.txt",
                    )

            # Enforce rate limiter
            await self.rate_limiter.acquire(domain)

            # Perform request with backoff on 429
            max_retries = settings.MAX_RETRIES_PER_DOMAIN
            delay = 2.0

            for attempt in range(max_retries):
                try:
                    response = await client.get(url, headers=req_headers)
                    if response.status_code == 429:
                        if attempt < max_retries - 1:
                            logger.warning(f"HTTP 429 on {url}, backing off for {delay}s")
                            await asyncio.sleep(delay)
                            delay *= 2.0
                            continue
                        return FetchResult(
                            url=url,
                            status_code=429,
                            text="",
                            error="Rate limited after maximum retries",
                        )

                    if response.status_code == 403:
                        logger.warning(
                            f"HTTP 403 Forbidden on {url}, marking unavailable without bypass"
                        )
                        return FetchResult(
                            url=url,
                            status_code=403,
                            text="",
                            is_blocked=True,
                            error="Access forbidden by origin",
                        )

                    if response.status_code == 200 and use_cache:
                        self.cache.set(url, response.status_code, response.text)

                    return FetchResult(
                        url=url,
                        status_code=response.status_code,
                        text=response.text,
                    )
                except (httpx.TimeoutException, httpx.RequestError) as exc:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay)
                        delay *= 2.0
                        continue
                    return FetchResult(
                        url=url,
                        status_code=504,
                        text="",
                        error=f"Request failed: {exc}",
                    )

            return FetchResult(
                url=url,
                status_code=500,
                text="",
                error="Exhausted retry budget",
            )


# Default singleton instance
fetcher = SharedFetcher()
