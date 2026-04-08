from __future__ import annotations

import asyncio
import ipaddress
import socket
from pathlib import Path
from tempfile import gettempdir
from urllib.parse import urljoin, urlparse

import aiohttp
from aiohttp.abc import AbstractResolver

from markio.settings import settings
from markio.utils.file_utils import (
    extract_filename_from_url,
    func_processing_time,
    md_dump_io,
    resolve_path_within_base,
    sanitize_filename,
    slugify_path_component,
)
from markio.utils.logger_config import get_logger

logger = get_logger(__name__)

URL_REDIRECT_STATUS_CODES = {301, 302, 303, 307, 308}
URL_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/117.0.0.0 Safari/537.36"
)


class URLSecurityError(ValueError):
    """Raised when URL target violates security constraints."""


class URLFetchError(RuntimeError):
    """Raised when URL fetch fails at transport or protocol layer."""


class _PinnedResolver(AbstractResolver):
    def __init__(self) -> None:
        self._pinned_hosts: dict[str, tuple[str, ...]] = {}

    def pin(self, hostname: str, ips: set[ipaddress._BaseAddress]) -> None:
        normalized = hostname.strip().lower().rstrip(".")
        self._pinned_hosts[normalized] = tuple(
            sorted(ip.compressed for ip in ips)
        )

    async def resolve(
        self,
        host: str,
        port: int = 0,
        family: int = socket.AF_UNSPEC,
    ) -> list[dict[str, object]]:
        normalized = host.strip().lower().rstrip(".")
        if normalized not in self._pinned_hosts:
            raise OSError(f"Host {host} was not pinned for connection")

        results: list[dict[str, object]] = []
        for raw_ip in self._pinned_hosts[normalized]:
            ip = ipaddress.ip_address(raw_ip)
            results.append(
                {
                    "hostname": host,
                    "host": raw_ip,
                    "port": port,
                    "family": socket.AF_INET6 if ip.version == 6 else socket.AF_INET,
                    "proto": socket.IPPROTO_TCP,
                    "flags": socket.AI_NUMERICHOST,
                }
            )
        return results

    async def close(self) -> None:
        self._pinned_hosts.clear()


def _normalize_fetch_mode(mode: str) -> str:
    normalized = str(mode or "direct").strip().lower()
    if normalized not in {"direct", "jina_proxy"}:
        raise URLSecurityError("Unsupported URL fetch mode")
    return normalized


def _parse_allowed_domains(raw: str) -> set[str]:
    return {
        domain.strip().lower().rstrip(".")
        for domain in str(raw or "").split(",")
        if domain.strip()
    }


def _is_domain_allowed(hostname: str, allowed_domains: set[str]) -> bool:
    if not allowed_domains:
        return True
    host = hostname.strip().lower().rstrip(".")
    for allowed in allowed_domains:
        if host == allowed or host.endswith(f".{allowed}"):
            return True
    return False


def _validate_url_format(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise URLSecurityError("URL must start with http:// or https://")
    if not parsed.hostname:
        raise URLSecurityError("URL host is required")
    if parsed.username or parsed.password:
        raise URLSecurityError("URL with embedded credentials is not allowed")


def _is_blocked_ip_address(ip: ipaddress._BaseAddress) -> bool:
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


async def _resolve_hostname_ips(hostname: str) -> set[ipaddress._BaseAddress]:
    loop = asyncio.get_running_loop()
    try:
        addr_infos = await loop.getaddrinfo(
            hostname,
            None,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )
    except socket.gaierror as exc:
        raise URLFetchError("Failed to resolve URL host") from exc

    resolved: set[ipaddress._BaseAddress] = set()
    for family, _, _, _, socket_addr in addr_infos:
        if family == socket.AF_INET:
            raw_ip = socket_addr[0]
        elif family == socket.AF_INET6:
            raw_ip = socket_addr[0]
        else:
            continue
        try:
            resolved.add(ipaddress.ip_address(raw_ip))
        except ValueError:
            continue

    if not resolved:
        raise URLFetchError("Failed to resolve URL host")
    return resolved


async def _validate_target_host(
    target_url: str,
    *,
    block_private_networks: bool,
    allowed_domains: set[str],
    resolve_for_connection: bool = False,
) -> set[ipaddress._BaseAddress]:
    parsed = urlparse(target_url)
    hostname = (parsed.hostname or "").strip().lower().rstrip(".")
    if not hostname:
        raise URLSecurityError("URL host is required")

    if not _is_domain_allowed(hostname, allowed_domains):
        raise URLSecurityError("URL host is not in allowed domains")

    candidate_ips: set[ipaddress._BaseAddress] = set()

    try:
        candidate_ips = {ipaddress.ip_address(hostname)}
    except ValueError:
        if block_private_networks or resolve_for_connection:
            candidate_ips = await _resolve_hostname_ips(hostname)

    if not block_private_networks:
        return candidate_ips

    for ip in candidate_ips:
        if _is_blocked_ip_address(ip):
            raise URLSecurityError("URL host resolves to blocked network address")
    return candidate_ips


def _build_fetch_url(url: str, mode: str) -> str:
    if mode == "direct":
        return url

    proxy_base = str(settings.url_proxy_base or "").strip()
    if not proxy_base:
        raise URLFetchError("URL proxy base is not configured")
    if not proxy_base.endswith("/"):
        proxy_base = f"{proxy_base}/"
    return f"{proxy_base}{url}"


async def _read_response_limited(response: aiohttp.ClientResponse, max_bytes: int) -> str:
    content = bytearray()
    async for chunk in response.content.iter_chunked(64 * 1024):
        content.extend(chunk)
        if len(content) > max_bytes:
            raise URLFetchError("URL response exceeds configured size limit")

    encoding = response.charset or "utf-8"
    return bytes(content).decode(encoding, errors="replace")


async def _read_response_bytes_limited(
    response: aiohttp.ClientResponse,
    max_bytes: int,
) -> bytes:
    content = bytearray()
    async for chunk in response.content.iter_chunked(64 * 1024):
        content.extend(chunk)
        if len(content) > max_bytes:
            raise URLFetchError("URL response exceeds configured size limit")
    return bytes(content)


async def _fetch_markdown_content(url: str) -> str:
    _validate_url_format(url)

    fetch_mode = _normalize_fetch_mode(settings.url_fetch_mode)
    allowed_domains = _parse_allowed_domains(settings.url_allowed_domains)
    block_private_networks = bool(settings.url_block_private_networks)

    pinned_resolver: _PinnedResolver | None = None
    connector: aiohttp.TCPConnector | None = None
    initial_ips = await _validate_target_host(
        url,
        block_private_networks=block_private_networks,
        allowed_domains=allowed_domains,
        resolve_for_connection=(fetch_mode == "direct"),
    )
    if fetch_mode == "direct" and initial_ips:
        pinned_resolver = _PinnedResolver()
        pinned_resolver.pin(urlparse(url).hostname or "", initial_ips)
        connector = aiohttp.TCPConnector(resolver=pinned_resolver)

    timeout_seconds = max(1, int(settings.url_request_timeout_seconds))
    max_response_bytes = max(1, int(settings.url_max_response_bytes))
    max_redirects = max(0, int(settings.url_max_redirects))
    current_url = _build_fetch_url(url, fetch_mode)

    headers = {"User-Agent": URL_USER_AGENT}
    timeout = aiohttp.ClientTimeout(total=timeout_seconds)

    try:
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            for redirect_hops in range(max_redirects + 1):
                async with session.get(
                    current_url,
                    headers=headers,
                    allow_redirects=False,
                ) as response:
                    if (
                        response.status in URL_REDIRECT_STATUS_CODES
                        and response.headers.get("Location")
                    ):
                        if redirect_hops >= max_redirects:
                            raise URLFetchError("URL exceeded redirect limit")
                        next_url = urljoin(str(response.url), response.headers["Location"])
                        if fetch_mode == "direct":
                            _validate_url_format(next_url)
                            next_ips = await _validate_target_host(
                                next_url,
                                block_private_networks=block_private_networks,
                                allowed_domains=allowed_domains,
                                resolve_for_connection=True,
                            )
                            if pinned_resolver is not None:
                                pinned_resolver.pin(urlparse(next_url).hostname or "", next_ips)
                        current_url = next_url
                        continue

                    response.raise_for_status()

                    if fetch_mode == "direct":
                        final_url = str(response.url)
                        _validate_url_format(final_url)
                        final_ips = await _validate_target_host(
                            final_url,
                            block_private_networks=block_private_networks,
                            allowed_domains=allowed_domains,
                            resolve_for_connection=True,
                        )
                        if pinned_resolver is not None:
                            pinned_resolver.pin(urlparse(final_url).hostname or "", final_ips)

                    return await _read_response_limited(response, max_response_bytes)
    except aiohttp.ClientResponseError as exc:
        raise URLFetchError(
            f"Failed to fetch URL content: HTTP {exc.status}"
        ) from exc
    except asyncio.TimeoutError as exc:
        raise URLFetchError("URL fetch timeout") from exc
    except aiohttp.ClientError as exc:
        raise URLFetchError("Failed to fetch URL content") from exc

    raise URLFetchError("Failed to fetch URL content")


async def download_file_from_url(
    url: str,
    output_dir: str | None = None,
    filename: str | None = None,
    timeout_seconds: int | None = None,
) -> str:
    _validate_url_format(url)

    allowed_domains = _parse_allowed_domains(settings.url_allowed_domains)
    block_private_networks = bool(settings.url_block_private_networks)
    initial_ips = await _validate_target_host(
        url,
        block_private_networks=block_private_networks,
        allowed_domains=allowed_domains,
        resolve_for_connection=True,
    )

    request_timeout_seconds = max(
        1,
        int(timeout_seconds if timeout_seconds is not None else settings.url_request_timeout_seconds),
    )
    max_response_bytes = max(1, int(settings.url_max_response_bytes))
    max_redirects = max(0, int(settings.url_max_redirects))
    current_url = url
    headers = {"User-Agent": URL_USER_AGENT}
    timeout = aiohttp.ClientTimeout(total=request_timeout_seconds)
    pinned_resolver = _PinnedResolver()
    pinned_resolver.pin(urlparse(url).hostname or "", initial_ips)
    connector = aiohttp.TCPConnector(resolver=pinned_resolver)

    safe_filename = sanitize_filename(
        filename or extract_filename_from_url(url) or "downloaded_file"
    )
    base_dir = Path(output_dir or gettempdir()).expanduser().resolve()
    base_dir.mkdir(parents=True, exist_ok=True)
    output_path = (base_dir / safe_filename).resolve()
    try:
        resolve_path_within_base(base_dir, output_path)
    except ValueError as exc:
        raise URLSecurityError("Invalid output path for downloaded URL resource") from exc

    try:
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            for redirect_hops in range(max_redirects + 1):
                async with session.get(
                    current_url,
                    headers=headers,
                    allow_redirects=False,
                ) as response:
                    if (
                        response.status in URL_REDIRECT_STATUS_CODES
                        and response.headers.get("Location")
                    ):
                        if redirect_hops >= max_redirects:
                            raise URLFetchError("URL exceeded redirect limit")
                        next_url = urljoin(str(response.url), response.headers["Location"])
                        _validate_url_format(next_url)
                        next_ips = await _validate_target_host(
                            next_url,
                            block_private_networks=block_private_networks,
                            allowed_domains=allowed_domains,
                            resolve_for_connection=True,
                        )
                        pinned_resolver.pin(urlparse(next_url).hostname or "", next_ips)
                        current_url = next_url
                        continue

                    response.raise_for_status()

                    final_url = str(response.url)
                    _validate_url_format(final_url)
                    final_ips = await _validate_target_host(
                        final_url,
                        block_private_networks=block_private_networks,
                        allowed_domains=allowed_domains,
                        resolve_for_connection=True,
                    )
                    pinned_resolver.pin(urlparse(final_url).hostname or "", final_ips)

                    payload = await _read_response_bytes_limited(
                        response,
                        max_response_bytes,
                    )
                    output_path.write_bytes(payload)
                    return str(output_path)
    except aiohttp.ClientResponseError as exc:
        raise URLFetchError(
            f"Failed to fetch URL content: HTTP {exc.status}"
        ) from exc
    except asyncio.TimeoutError as exc:
        raise URLFetchError("URL fetch timeout") from exc
    except aiohttp.ClientError as exc:
        raise URLFetchError("Failed to fetch URL content") from exc

    raise URLFetchError("Failed to fetch URL content")


@func_processing_time
async def url_parse_main(
    url: str,
    save_parsed_content: bool = False,
    output_dir: str = "",
) -> str:
    """
    Fetch and parse content from a URL, converting it to Markdown format.
    """
    markdown_content = await _fetch_markdown_content(url)

    file_name = markdown_content.split("\n")[0].replace("Title:", "").strip()
    safe_slug = slugify_path_component(file_name, fallback="url-content")

    if save_parsed_content:
        resolved_output_dir = Path(output_dir).resolve()
        save_parsed_dir = (resolved_output_dir / safe_slug).resolve()
        try:
            resolve_path_within_base(resolved_output_dir, save_parsed_dir)
        except ValueError as exc:
            raise RuntimeError("Invalid URL output path") from exc
        save_parsed_dir.mkdir(parents=True, exist_ok=True)
        output_path = (save_parsed_dir / f"{safe_slug}.md").resolve()
        try:
            resolve_path_within_base(resolved_output_dir, output_path)
        except ValueError as exc:
            raise RuntimeError("Invalid URL output file path") from exc

        await md_dump_io(
            md_content=markdown_content,
            output_path=output_path,
        )
        logger.info(f"URL {safe_slug} saved to {output_path}")

    return markdown_content
