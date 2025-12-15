from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseIngestor(ABC):
    """
    Contract for all content ingestion sources.
    """

    @abstractmethod
    def fetch(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def validate(self, item: Dict[str, Any]) -> bool:
        pass
