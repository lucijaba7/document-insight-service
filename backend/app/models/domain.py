from dataclasses import dataclass
from typing import List


@dataclass
class DocumentSession:
    session_id: str
    page_texts: List[str]
