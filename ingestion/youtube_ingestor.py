from typing import List, Dict, Any
from ingestion.base_ingestor import BaseIngestor
from ingestion.schema import ContentItem
from ingestion.logger import logger

# placeholder for transcript retrieval
def fetch_transcript(video_id: str) -> str:
    raise NotImplementedError


class YouTubeIngestor(BaseIngestor):
    def fetch(self) -> List[ContentItem]:
        logger.info("Starting YouTube ingestion")
        items: List[ContentItem] = []

        # stub example
        video_id = "example_id"
        transcript = fetch_transcript(video_id)

        item: ContentItem = {
            "source": "youtube",
            "content_id": video_id,
            "title": "placeholder",
            "creator": "placeholder",
            "published_at": "2024-01-01",
            "raw_text": transcript,
            "language": None,
        }

        if self.validate(item):
            items.append(item)

        logger.info("Completed YouTube ingestion")
        return items

    def validate(self, item: Dict[str, Any]) -> bool:
        required = ["content_id", "raw_text"]
        return all(item.get(k) for k in required)
