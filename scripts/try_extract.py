import asyncio
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import AsyncOpenAI

from rent_parse.extract.llm import ExtractionError, extract_listing
from rent_parse.extract.schema import Listing
from rent_parse.ingest.telegram_export import parse_text_entities

DATA_PATH = Path("data/raw/data_1.json")
RUNS_DIR = Path("data/runs")
SAMPLE_SIZE = 20


def load_messages(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    messages: list[dict[str, Any]] = data["messages"]
    return messages


def pick_messages(
    messages: list[dict[str, Any]], n: int = SAMPLE_SIZE
) -> list[dict[str, Any]]:
    return messages[:n]


def make_record(
    message_id: int,
    text: str,
    listing: Listing | None,
    error: ExtractionError | None,
) -> dict[str, Any]:
    error_info = None
    if error is not None:
        error_info = {"message": str(error), "retryable": error.retryable}

    record: dict[str, Any] = {
        "id": message_id,
        "text": text,
        "listing": listing.model_dump(mode="json") if listing is not None else None,
        "error": error_info,
    }
    return record


async def main() -> None:
    load_dotenv()
    client = AsyncOpenAI(
        api_key=os.environ["GEMINI_API_KEY"],
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )

    messages = pick_messages(load_messages(DATA_PATH))

    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RUNS_DIR / f"extract_{datetime.now():%Y%m%d-%H%M%S}.jsonl"

    succeeded = failed = 0
    start = time.perf_counter()

    with out_path.open("w", encoding="utf-8") as out:
        for message in messages:
            parsed = parse_text_entities(message["text_entities"])
            listing: Listing | None = None
            error: ExtractionError | None = None
            try:
                listing = await extract_listing(parsed.text, client)
                succeeded += 1
                print(f"[{message['id']}] ok")
            except ExtractionError as err:
                error = err
                failed += 1
                print(f"[{message['id']}] FAILED (retryable={err.retryable}): {err}")

            record = make_record(message["id"], parsed.text, listing, error)
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            out.flush()

    elapsed = time.perf_counter() - start
    print(
        f"\nDone: {succeeded} succeeded, {failed} failed, "
        f"{len(messages)} total in {elapsed:.1f}s"
    )
    print(f"Results written to {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
