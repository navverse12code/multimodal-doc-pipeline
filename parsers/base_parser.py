from abc import ABC, abstractmethod
from typing import List, Tuple

class BaseParser(ABC):
    """
    Abstract base class for all file parsers.
    Each parser returns a list of tuples: (page_or_slide_number, content)
    """

    @abstractmethod
    def parse(self, file_path: str) -> List[Tuple[int, str]]:
        pass
