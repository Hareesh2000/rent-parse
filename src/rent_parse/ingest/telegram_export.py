from dataclasses import dataclass
from typing import NotRequired, TypedDict


@dataclass
class ParsedData:
    text: str
    extracted_data: dict[str, str]


class TextEntity(TypedDict):
    type: str
    text: str
    href: NotRequired[str]


KNOWN_ENTITY_TYPES: frozenset[str] = frozenset(
    {"link", "phone", "email", "mention", "text_link"}
)


def parse_text_entities(entities: list[TextEntity]) -> ParsedData:
    """Flattens a list of Telegram text entities into a plain string
    and extracts data with known types."""
    flattened_text = []
    entity_type_counts: dict[str, int] = {}
    extracted_entities_data: dict[str, str] = {}

    for entity in entities:
        # Replace specific entities with placeholders to avoid unnecessary AI cost
        entity_type = entity["type"]
        entity_text = entity["text"]
        if entity_type in KNOWN_ENTITY_TYPES:
            if entity_type == "text_link" and (
                entity.get("href") is None or entity.get("href") == ""
            ):
                # If a text_link entity does not have an href, treat it as plain text
                flattened_text.append(entity_text)
                continue

            entity_type_count = entity_type_counts.get(entity_type, 1)
            entity_placeholder = f"[{entity_type.upper()}_{entity_type_count}]"
            entity_type_counts[entity_type] = entity_type_count + 1

            if entity_type == "text_link":
                flattened_text.append(entity_text)
                extracted_entities_data[entity_placeholder] = entity["href"]
                flattened_text.append(" " + entity_placeholder)
            else:
                extracted_entities_data[entity_placeholder] = entity_text
                flattened_text.append(entity_placeholder)

        else:
            flattened_text.append(entity_text)

    flattened_text_string = "".join(flattened_text)
    parsed_entity = ParsedData(
        text=flattened_text_string, extracted_data=extracted_entities_data
    )
    return parsed_entity
