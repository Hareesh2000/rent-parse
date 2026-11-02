from openai import AsyncOpenAI

from rent_parse.extract.schema import Listing

DEFAULT_MODEL = "gemini-3.5-flash-lite"


class ExtractionError(Exception):
    def __init__(self, message: str, retryable: bool) -> None:
        super().__init__(message)
        self.message = message
        self.retryable = retryable


async def extract_listing(
    text: str, client: AsyncOpenAI, model: str = DEFAULT_MODEL
) -> Listing:
    response = await client.beta.chat.completions.parse(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You extract rental listings from "
                "Bengaluru Telegram posts and return them "
                "in a structured JSON format. ",
            },
            {"role": "user", "content": text},
        ],
        response_format=Listing,
        temperature=0.1,
    )

    if not response.choices:
        raise ExtractionError(message="no choices returned", retryable=True)

    choice = response.choices[0]
    parsed_message = choice.message.parsed

    if parsed_message is None:
        retryable = True
        if (
            choice.message.refusal is not None
            or choice.finish_reason == "content_filter"
        ):
            retryable = False
        raise ExtractionError(
            message=f"no parsed message returned. refusal: {choice.message.refusal}, "
            f"finish_reason: {choice.finish_reason}",
            retryable=retryable,
        )
    return parsed_message
