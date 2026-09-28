from __future__ import annotations

import html
import os
import re
from collections.abc import Iterator
from typing import Any

import praw

from ..models import RawItem
from .base import Provider, ProviderError


class RedditProvider(Provider):
    name = "reddit"

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        client_id = os.environ.get(str(config.get("client_id_env", "REDDIT_CLIENT_ID")), "")
        client_secret = os.environ.get(
            str(config.get("client_secret_env", "REDDIT_CLIENT_SECRET")), ""
        )
        user_agent = os.environ.get(str(config.get("user_agent_env", "REDDIT_USER_AGENT")), "")
        if not all([client_id, client_secret, user_agent]):
            raise ProviderError(
                "Thieu REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET hoac REDDIT_USER_AGENT."
            )
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
            check_for_async=False,
        )
        self.reddit.read_only = True

    def collect(self) -> Iterator[RawItem]:
        for source in self.config.get("subreddits", []):
            if isinstance(source, str):
                source = {"name": source, "queries": []}
            name = str(source.get("name", "")).removeprefix("r/")
            if not name:
                continue
            trusted = bool(source.get("trusted_education_source", False))
            subreddit = self.reddit.subreddit(name)
            queries = source.get("queries", []) or [""]
            seen_posts: set[str] = set()
            for query in queries:
                try:
                    submissions = self._submissions(subreddit, str(query))
                    for submission in submissions:
                        if submission.id in seen_posts:
                            continue
                        seen_posts.add(submission.id)
                        if getattr(submission, "over_18", False) and not self.config.get(
                            "include_nsfw", False
                        ):
                            continue
                        yield from self._comments(submission, name, trusted)
                except Exception as exc:
                    raise ProviderError(f"Reddit API loi tai r/{name}: {exc}") from exc

    def _submissions(self, subreddit: Any, query: str) -> Any:
        limit = int(self.config.get("posts_per_query", 25))
        if query:
            return subreddit.search(
                query,
                sort=str(self.config.get("sort", "new")),
                time_filter=str(self.config.get("time_filter", "month")),
                limit=limit,
            )
        return subreddit.new(limit=limit)

    def _comments(
        self,
        submission: Any,
        subreddit_name: str,
        trusted: bool,
    ) -> Iterator[RawItem]:
        submission.comment_sort = "new"
        submission.comments.replace_more(limit=0)
        post_text = "\n\n".join(
            part for part in [str(submission.title), str(submission.selftext or "")] if part
        )
        image_urls = _reddit_image_urls(submission)
        max_comments = int(self.config.get("comments_per_post", 100))
        for index, comment in enumerate(submission.comments.list()):
            if index >= max_comments:
                break
            body = str(getattr(comment, "body", ""))
            parent_id = ""
            parent_text = ""
            try:
                parent = comment.parent()
                if getattr(parent, "body", None) is not None:
                    parent_id = str(getattr(parent, "id", ""))
                    parent_text = str(parent.body)
            except Exception:
                pass
            author = getattr(comment, "author", None)
            yield RawItem(
                platform=self.name,
                source_name=f"r/{subreddit_name}",
                source_type="public_subreddit",
                object_type="reply" if parent_id else "comment",
                source_item_id=str(comment.id),
                post_id=str(submission.id),
                parent_comment_id=parent_id,
                target_text=body,
                post_text=post_text,
                parent_comment_text=parent_text,
                permalink=f"https://www.reddit.com{comment.permalink}",
                published_at=str(getattr(comment, "created_utc", "")),
                author_id=str(author) if author else "",
                trusted_education_source=trusted,
                image_urls=image_urls,
            )


IMAGE_EXTENSION_RE = re.compile(r"\.(?:avif|gif|jpe?g|png|webp)(?:\?|$)", re.IGNORECASE)


def _reddit_image_urls(submission: Any) -> list[str]:
    urls: list[str] = []
    direct_url = str(getattr(submission, "url", ""))
    if direct_url and IMAGE_EXTENSION_RE.search(direct_url):
        urls.append(html.unescape(direct_url))

    preview = getattr(submission, "preview", None)
    if isinstance(preview, dict):
        for image in preview.get("images", []):
            if not isinstance(image, dict):
                continue
            source = image.get("source", {})
            if isinstance(source, dict) and source.get("url"):
                urls.append(html.unescape(str(source["url"])))

    metadata = getattr(submission, "media_metadata", None)
    if isinstance(metadata, dict):
        for media in metadata.values():
            if not isinstance(media, dict):
                continue
            source = media.get("s", {})
            if isinstance(source, dict) and source.get("u"):
                urls.append(html.unescape(str(source["u"])))
    return list(dict.fromkeys(urls))
