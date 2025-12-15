from typing import TypedDict, Optional


class ContentItem(TypedDict):
    source: str
    content_id: str
    title: str
    creator: str
    published_at: str
    raw_text: str
    language: Optional[str]
