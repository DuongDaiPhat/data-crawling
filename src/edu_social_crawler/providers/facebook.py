from __future__ import annotations

import os
from collections.abc import Iterator
from typing import Any

from ..models import RawItem
from .base import Provider, ProviderError
from .http import JsonHttpClient


class FacebookProvider(Provider):
    name = "facebook"

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        token_env = str(config.get("access_token_env", "META_ACCESS_TOKEN"))
        self.token = os.environ.get(token_env, "")
        if not self.token:
            raise ProviderError(f"Thieu bien moi truong {token_env}.")
        self.version = str(config.get("graph_version", "v26.0"))
        self.base_url = f"https://graph.facebook.com/{self.version}"
        self.http = JsonHttpClient()

    def collect(self) -> Iterator[RawItem]:
        for page in self.config.get("pages", []):
            page_id = str(page["id"])
            page_name = str(page.get("name", page_id))
            trusted = bool(page.get("trusted_education_source", False))
            posts = self.http.edge(
                f"{self.base_url}/{page_id}/posts",
                {
                    "access_token": self.token,
                    "fields": (
                        "id,message,created_time,permalink_url,full_picture,"
                        "attachments{media,subattachments{media}}"
                    ),
                    "limit": min(100, int(self.config.get("posts_per_page", 25))),
                },
                int(self.config.get("posts_per_page", 25)),
            )
            for post in posts:
                post_id = str(post.get("id", ""))
                post_text = str(post.get("message", ""))
                if not post_id:
                    continue
                yield from self._comments(
                    page_name,
                    trusted,
                    post_id,
                    post_text,
                    _facebook_image_urls(post),
                )

    def _comments(
        self,
        page_name: str,
        trusted: bool,
        post_id: str,
        post_text: str,
        image_urls: list[str],
    ) -> Iterator[RawItem]:
        comments = self.http.edge(
            f"{self.base_url}/{post_id}/comments",
            {
                "access_token": self.token,
                "fields": "id,message,created_time,permalink_url,from{id}",
                "filter": "toplevel",
                "limit": min(100, int(self.config.get("comments_per_post", 100))),
            },
            int(self.config.get("comments_per_post", 100)),
        )
        for comment in comments:
            comment_id = str(comment.get("id", ""))
            message = str(comment.get("message", ""))
            if not comment_id:
                continue
            author = comment.get("from") or {}
            yield RawItem(
                platform=self.name,
                source_name=page_name,
                source_type="public_page",
                object_type="comment",
                source_item_id=comment_id,
                post_id=post_id,
                target_text=message,
                post_text=post_text,
                permalink=str(comment.get("permalink_url", "")),
                published_at=str(comment.get("created_time", "")),
                author_id=str(author.get("id", "")) if isinstance(author, dict) else "",
                trusted_education_source=trusted,
                image_urls=image_urls,
            )
            if comment_id:
                yield from self._replies(
                    page_name,
                    trusted,
                    post_id,
                    post_text,
                    comment_id,
                    message,
                    image_urls,
                )

    def _replies(
        self,
        page_name: str,
        trusted: bool,
        post_id: str,
        post_text: str,
        parent_id: str,
        parent_text: str,
        image_urls: list[str],
    ) -> Iterator[RawItem]:
        replies = self.http.edge(
            f"{self.base_url}/{parent_id}/comments",
            {
                "access_token": self.token,
                "fields": "id,message,created_time,permalink_url,from{id}",
                "limit": min(100, int(self.config.get("replies_per_comment", 50))),
            },
            int(self.config.get("replies_per_comment", 50)),
        )
        for reply in replies:
            reply_id = str(reply.get("id", ""))
            if not reply_id:
                continue
            author = reply.get("from") or {}
            yield RawItem(
                platform=self.name,
                source_name=page_name,
                source_type="public_page",
                object_type="reply",
                source_item_id=reply_id,
                post_id=post_id,
                parent_comment_id=parent_id,
                target_text=str(reply.get("message", "")),
                post_text=post_text,
                parent_comment_text=parent_text,
                permalink=str(reply.get("permalink_url", "")),
                published_at=str(reply.get("created_time", "")),
                author_id=str(author.get("id", "")) if isinstance(author, dict) else "",
                trusted_education_source=trusted,
                image_urls=image_urls,
            )


def _facebook_image_urls(post: dict[str, Any]) -> list[str]:
    urls: list[str] = []
    full_picture = post.get("full_picture")
    if full_picture:
        urls.append(str(full_picture))

    def visit_attachment(attachment: Any) -> None:
        if not isinstance(attachment, dict):
            return
        media = attachment.get("media")
        if isinstance(media, dict):
            image = media.get("image")
            if isinstance(image, dict) and image.get("src"):
                urls.append(str(image["src"]))
        children = attachment.get("subattachments")
        if isinstance(children, dict):
            for child in children.get("data", []):
                visit_attachment(child)

    attachments = post.get("attachments")
    if isinstance(attachments, dict):
        for attachment in attachments.get("data", []):
            visit_attachment(attachment)
    return list(dict.fromkeys(urls))
