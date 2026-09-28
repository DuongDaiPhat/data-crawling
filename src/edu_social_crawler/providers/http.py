from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import requests

from .base import ProviderError


class JsonHttpClient:
    def __init__(self, timeout: int = 30) -> None:
        self.session = requests.Session()
        self.timeout = timeout

    def get(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            detail = ""
            if "response" in locals():
                detail = response.text[:500]
            raise ProviderError(f"API request that bai: {url}. {detail}") from exc
        if isinstance(payload, dict) and payload.get("error"):
            raise ProviderError(f"API tra ve loi: {payload['error']}")
        if not isinstance(payload, dict):
            raise ProviderError(f"API response khong dung dinh dang object: {url}")
        return payload

    def edge(
        self,
        url: str,
        params: dict[str, Any],
        limit: int,
    ) -> Iterator[dict[str, Any]]:
        emitted = 0
        next_url: str | None = url
        next_params: dict[str, Any] | None = params
        while next_url and emitted < limit:
            payload = self.get(next_url, next_params)
            data = payload.get("data", [])
            if not isinstance(data, list):
                raise ProviderError(f"API response thieu data list: {next_url}")
            for item in data:
                if not isinstance(item, dict):
                    continue
                yield item
                emitted += 1
                if emitted >= limit:
                    return
            paging = payload.get("paging", {})
            next_url = paging.get("next") if isinstance(paging, dict) else None
            next_params = None
