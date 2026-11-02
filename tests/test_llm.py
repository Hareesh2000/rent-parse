from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from rent_parse.extract.llm import DEFAULT_MODEL, ExtractionError, extract_listing
from rent_parse.extract.schema import Listing, ListingType

TEXT = "Male Flatmate needed in a 3 BHK Flat"


def make_client(choices: list[Any]) -> AsyncMock:
    """Return a fake client whose .parse() resolves to a response with `choices`."""
    client = AsyncMock()

    response = MagicMock()
    response.choices = choices

    client.beta.chat.completions.parse = AsyncMock(return_value=response)
    return client


def make_choice(
    parsed: Listing | None = None,
    refusal: str | None = None,
    finish_reason: str = "stop",
) -> MagicMock:
    choice = MagicMock()
    choice.message.parsed = parsed
    choice.message.refusal = refusal
    choice.finish_reason = finish_reason
    return choice


async def test_returns_listing_when_parsed() -> None:
    listing = Listing(
        listing_type=ListingType.FLATMATE,
        rent=17000,
        locality="Seegehalli",
        furnishing=None,
        bedrooms=3,
        preferred_tenants="male",
    )
    client = make_client([make_choice(parsed=listing)])

    result = await extract_listing(TEXT, client)

    assert result == listing


async def test_empty_choices_raises_retryable_error() -> None:
    client = make_client([])

    with pytest.raises(ExtractionError) as exc_info:
        await extract_listing(TEXT, client)

    assert exc_info.value.retryable is True


@pytest.mark.parametrize(
    ("refusal", "finish_reason", "retryable"),
    [
        ("I can't help with that", "stop", False),  # refusal: retrying won't help
        (None, "content_filter", False),  # same input is filtered again
        (None, "length", True),  # truncated output may succeed on retry
    ],
)
async def test_unparsed_message_sets_retryable_by_cause(
    refusal: str | None, finish_reason: str, retryable: bool
) -> None:
    choice = make_choice(parsed=None, refusal=refusal, finish_reason=finish_reason)
    client = make_client([choice])

    with pytest.raises(ExtractionError) as exc_info:
        await extract_listing(TEXT, client)

    assert exc_info.value.retryable is retryable


async def test_error_message_includes_refusal_and_finish_reason() -> None:
    choice = make_choice(refusal="nope", finish_reason="content_filter")
    client = make_client([choice])

    with pytest.raises(ExtractionError, match="nope.*content_filter"):
        await extract_listing(TEXT, client)


async def test_sends_text_and_default_model_to_client() -> None:
    client = make_client([make_choice(parsed=MagicMock(spec=Listing))])

    await extract_listing(TEXT, client)

    kwargs = client.beta.chat.completions.parse.await_args.kwargs
    assert kwargs["model"] == DEFAULT_MODEL
    assert kwargs["messages"][-1] == {"role": "user", "content": TEXT}
    assert kwargs["response_format"] is Listing


async def test_model_can_be_overridden() -> None:
    client = make_client([make_choice(parsed=MagicMock(spec=Listing))])

    await extract_listing(TEXT, client, model="some-other-model")

    kwargs = client.beta.chat.completions.parse.await_args.kwargs
    assert kwargs["model"] == "some-other-model"
