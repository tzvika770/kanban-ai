from typing import Literal

from pydantic import BaseModel, ConfigDict


# --- Auth ---


class LoginRequest(BaseModel):
    """Login request schema"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response schema"""
    access_token: str
    token_type: str = "bearer"
    username: str


# --- Kanban ---


class ColumnOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    position: int


class CardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    column_id: int
    title: str
    description: str | None = None
    position: int


class BoardOut(BaseModel):
    columns: list[ColumnOut]
    cards: list[CardOut]


class CardCreate(BaseModel):
    column_id: int
    title: str
    description: str = ""


class CardUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    column_id: int | None = None
    position: int | None = None


class ColumnRename(BaseModel):
    title: str


# --- AI ---


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class AIChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


class Mutation(BaseModel):
    """A single board change proposed by the AI.

    Fields are shared across mutation types; only those relevant to `type`
    are populated. rename_column uses `title` as the new column name.
    """
    type: Literal[
        "create_card", "update_card", "delete_card", "move_card", "rename_column"
    ]
    card_id: int | None = None
    column_id: int | None = None
    title: str | None = None
    description: str | None = None
    position: int | None = None


class AIChatResponse(BaseModel):
    response: str
    mutations: list[Mutation] = []
    updated_board: BoardOut
