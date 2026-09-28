from types import SimpleNamespace

from edu_social_crawler.providers.facebook import _facebook_image_urls
from edu_social_crawler.providers.reddit import _reddit_image_urls
from edu_social_crawler.providers.threads import _threads_image_urls


def test_facebook_image_urls_include_main_and_album_images() -> None:
    post = {
        "full_picture": "https://img.example/main.jpg",
        "attachments": {
            "data": [
                {
                    "media": {"image": {"src": "https://img.example/main.jpg"}},
                    "subattachments": {
                        "data": [{"media": {"image": {"src": "https://img.example/second.jpg"}}}]
                    },
                }
            ]
        },
    }
    assert _facebook_image_urls(post) == [
        "https://img.example/main.jpg",
        "https://img.example/second.jpg",
    ]


def test_threads_uses_image_or_video_thumbnail() -> None:
    assert _threads_image_urls(
        {"media_type": "IMAGE", "media_url": "https://img.example/thread.jpg"}
    ) == ["https://img.example/thread.jpg"]
    assert _threads_image_urls(
        {"media_type": "VIDEO", "thumbnail_url": "https://img.example/thumb.jpg"}
    ) == ["https://img.example/thumb.jpg"]


def test_reddit_image_urls_decode_preview_and_gallery_urls() -> None:
    submission = SimpleNamespace(
        url="https://img.example/direct.png",
        preview={"images": [{"source": {"url": "https://img.example/preview.jpg?a=1&amp;b=2"}}]},
        media_metadata={"one": {"s": {"u": "https://img.example/gallery.webp"}}},
    )
    assert _reddit_image_urls(submission) == [
        "https://img.example/direct.png",
        "https://img.example/preview.jpg?a=1&b=2",
        "https://img.example/gallery.webp",
    ]
