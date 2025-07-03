import logging
from functools import lru_cache
from typing import Any, List

from pydantic import ValidationError
from transformers import Pipeline, pipeline

from app.models.ask import Entity

logger = logging.getLogger(__name__)

MODEL_NAME = "dslim/bert-large-NER"


@lru_cache()
def get_ner_pipeline() -> Pipeline:
    logger.info(f"Loading NER model: {MODEL_NAME}")

    return pipeline(
        task="ner",
        model=MODEL_NAME,
        tokenizer=MODEL_NAME,
        aggregation_strategy="simple",
    )


def extract_entities(text: str) -> List[Entity]:
    ner = get_ner_pipeline()
    raw_predictions: List[dict[str, Any]] = ner(text)

    entities: List[Entity] = []
    for item in raw_predictions:
        data = {
            "entity": item.get("word", ""),
            "type": item.get("entity_group", ""),
            "score": float(item.get("score", 0.0)),
        }

        try:
            entities.append(Entity(**data))
        except ValidationError as e:
            logger.warning(f"Skipping invalid NER result {data!r}: {e}")
            continue

    return entities
