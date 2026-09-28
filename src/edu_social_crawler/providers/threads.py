from __future__ import annotations

import os
from collections.abc import Iterator
from typing import Any

from ..models import RawItem
from .base import Provider, ProviderError
from .http import JsonHttpClient


class ThreadsProvider(Provider):
    name = "threads"

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        token_env = str(config.get("access_token_env", "THREADS_ACCESS_TOKEN"))
        self.token = os.environ.get(token_env, "")
        if not self.token:
            raise ProviderError(f"Thieu bien moi truong {token_env}.")
        self.version = str(config.get("api_version", "v1.0"))
        self.base_url = f"https://graph.threads.net/{self.version}"
        self.http = JsonHttpClient()

    def collect(self) -> Iterator[RawItem]:
        for query in self.config.get("queries", []):
            if isinstance(query, str):
                query = {"text": query}
            text = str(query.get("text", "")).strip()
            if not text:
                continue
            trusted = bool(query.get("trusted_education_source", True))
            params = {
                "access_token": self.token,
                "q": text,
                "search_type": str(query.get("search_type", "RECENT")).upper(),
                "search_mode": str(query.get("search_mode", "KEYWORD")).upper(),
                "fields": (
                    "id,text,timestamp,permalink,username,media_type,media_url,thumbnail_url"
                ),
                "limit": min(100, int(self.config.get("posts_per_query", 50))),
            }
            posts = self.http.edge(
                f"{self.base_url}/keyword_search",
                params,
                int(self.config.get("posts_per_query", 50)),
            )
            for post in posts:
                post_id = str(post.get("id", ""))
                post_text = str(post.get("text", ""))
                if not post_id:
                    continue
                yield RawItem(
                    platform=self.name,
                    source_name=text,
                    source_type="keyword_search",
                    object_type="post",
                    source_item_id=post_id,
                    post_id=post_id,
                    target_text=post_text,
                    permalink=str(post.get("permalink", "")),
                    published_at=str(post.get("timestamp", "")),
                    author_id=str(post.get("username", "")),
                    trusted_education_source=trusted,
                    image_urls=_threads_image_urls(post),
                )
                if self.config.get("fetch_replies") and post_id:
                    yield from self._replies(
                        text,
                        trusted,
                        post_id,
                        post_text,
                        _threads_image_urls(post),
                    )

    def _replies(
        self,
        source_name: str,
        trusted: bool,
        post_id: str,
        post_text: str,
        post_image_urls: list[str],
    ) -> Iterator[RawItem]:
        replies = self.http.edge(
            f"{self.base_url}/{post_id}/replies",
            {
                "access_token": self.token,
                "fields": (
                    "id,text,timestamp,permalink,username,media_type,media_url,thumbnail_url"
                ),
                "limit": min(100, int(self.config.get("replies_per_post", 50))),
            },
            int(self.config.get("replies_per_post", 50)),
        )
        for reply in replies:
            reply_id = str(reply.get("id", ""))
            if not reply_id:
                continue
            yield RawItem(
                platform=self.name,
                source_name=source_name,
                source_type="keyword_search",
                object_type="reply",
                source_item_id=reply_id,
                post_id=post_id,
                target_text=str(reply.get("text", "")),
                post_text=post_text,
                permalink=str(reply.get("permalink", "")),
                published_at=str(reply.get("timestamp", "")),
                author_id=str(reply.get("username", "")),
                trusted_education_source=trusted,
                image_urls=[*post_image_urls, *_threads_image_urls(reply)],
            )


def _threads_image_urls(item: dict[str, Any]) -> list[str]:
    media_type = str(item.get("media_type", "")).upper()
    if media_type == "IMAGE" and item.get("media_url"):
        return [str(item["media_url"])]
    if item.get("thumbnail_url"):
        return [str(item["thumbnail_url"])]
    return []
