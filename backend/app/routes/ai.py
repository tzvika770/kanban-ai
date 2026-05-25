from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import ai
from ..auth import get_current_user
from ..database import get_db
from ..models import KanbanBoard, User
from ..schemas import AIChatRequest, AIChatResponse, Mutation
from .kanban import (
    create_card_db,
    delete_card_db,
    get_or_create_board,
    rename_column_db,
    serialize_board,
    update_card_db,
)
from ..schemas import CardUpdate

router = APIRouter(prefix="/api/ai", tags=["ai"])


def _apply_mutation(db: Session, board: KanbanBoard, m: Mutation) -> None:
    if m.type == "create_card":
        create_card_db(db, board, m.column_id, m.title or "", m.description or "")
    elif m.type == "update_card":
        update_card_db(
            db, board, m.card_id, CardUpdate(title=m.title, description=m.description)
        )
    elif m.type == "delete_card":
        delete_card_db(db, board, m.card_id)
    elif m.type == "move_card":
        update_card_db(
            db, board, m.card_id, CardUpdate(column_id=m.column_id, position=m.position)
        )
    elif m.type == "rename_column":
        rename_column_db(db, board, m.column_id, m.title or "")


@router.post("/test")
def ai_test_endpoint(user: User = Depends(get_current_user)):
    try:
        return {"response": ai.ai_test()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"AI error: {exc}")


@router.post("/chat", response_model=AIChatResponse)
def ai_chat_endpoint(
    payload: AIChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message is required")

    board = get_or_create_board(db, user)
    history = [m.model_dump() for m in payload.history]

    try:
        output = ai.ai_chat(payload.message, history, serialize_board(db, board))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"AI error: {exc}")

    # Apply each mutation independently; skip ones that reference missing
    # cards/columns so a single bad suggestion doesn't fail the whole reply.
    applied: list[Mutation] = []
    for mutation in output.mutations:
        try:
            _apply_mutation(db, board, mutation)
            applied.append(mutation)
        except HTTPException:
            db.rollback()

    return AIChatResponse(
        response=output.response,
        mutations=applied,
        updated_board=serialize_board(db, board),
    )
