import json

from openai import OpenAI
from pydantic import BaseModel

from . import config
from .schemas import BoardOut, Mutation

# JSON schema for the structured chat reply. Strict mode requires every
# property to be listed in `required`; optional fields are made nullable.
_MUTATION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "type": {
            "type": "string",
            "enum": [
                "create_card",
                "update_card",
                "delete_card",
                "move_card",
                "rename_column",
            ],
        },
        "card_id": {"type": ["integer", "null"]},
        "column_id": {"type": ["integer", "null"]},
        "title": {"type": ["string", "null"]},
        "description": {"type": ["string", "null"]},
        "position": {"type": ["integer", "null"]},
    },
    "required": ["type", "card_id", "column_id", "title", "description", "position"],
}

_RESPONSE_SCHEMA = {
    "name": "kanban_reply",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "response": {"type": "string"},
            "mutations": {"type": "array", "items": _MUTATION_SCHEMA},
        },
        "required": ["response", "mutations"],
    },
}

_SYSTEM_PROMPT = """You are a project management assistant embedded in a Kanban board app.
You are given the current board as JSON (columns and cards, each with integer ids).
Answer the user's message in the `response` field with a short, friendly summary.

When the user asks you to change the board, express the changes as `mutations`.
Use the integer ids from the provided board. Mutation types and the fields each uses:
- create_card: column_id, title, description
- update_card: card_id, and any of title / description to change
- delete_card: card_id
- move_card: card_id, column_id (target), position (0-based index in the target column)
- rename_column: column_id, title (the new column name)
Leave unused fields null. If no board change is needed, return an empty mutations list."""


class AIOutput(BaseModel):
    response: str
    mutations: list[Mutation] = []


def _client() -> OpenAI:
    if not config.OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")
    return OpenAI(
        api_key=config.OPENROUTER_API_KEY, base_url=config.OPENROUTER_BASE_URL
    )


def ai_test() -> str:
    """Simple connectivity check used by /api/ai/test."""
    completion = _client().chat.completions.create(
        model=config.OPENROUTER_MODEL,
        messages=[
            {"role": "user", "content": "What is 2+2? Reply with only the number."}
        ],
    )
    return completion.choices[0].message.content.strip()


def ai_chat(message: str, history: list[dict], board: BoardOut) -> AIOutput:
    """Send the board context plus the user message, return parsed structured output."""
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {
            "role": "system",
            "content": "Current board:\n" + board.model_dump_json(),
        },
        *history,
        {"role": "user", "content": message},
    ]
    completion = _client().chat.completions.create(
        model=config.OPENROUTER_MODEL,
        messages=messages,
        response_format={"type": "json_schema", "json_schema": _RESPONSE_SCHEMA},
    )
    content = completion.choices[0].message.content
    return AIOutput.model_validate(json.loads(content))
