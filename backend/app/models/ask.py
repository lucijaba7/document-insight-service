from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class Entity(BaseModel):
    entity: str
    type: str
    score: float

    model_config = ConfigDict(from_attributes=True)


class AskRequest(BaseModel):
    question: str


class SingleModelAnswer(BaseModel):
    model_name: str
    description: str
    answer: str
    score: float
    entities: Optional[List[Entity]]

    model_config = ConfigDict(from_attributes=True)


class MultiAskResponse(BaseModel):
    results: List[SingleModelAnswer]

    model_config = ConfigDict(from_attributes=True)
