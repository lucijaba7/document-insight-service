from typing import List

from pydantic import BaseModel, ConfigDict


class UploadResponse(BaseModel):
    session_token: str
    session_id: str
    text: List[str]

    model_config = ConfigDict(from_attributes=True)
