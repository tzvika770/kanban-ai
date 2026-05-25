from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Card, KanbanBoard, KanbanColumn, User
from ..schemas import (
    BoardOut,
    CardCreate,
    CardOut,
    CardUpdate,
    ColumnOut,
    ColumnRename,
)

router = APIRouter(prefix="/api", tags=["kanban"])

# Default board layout seeded on first access. Mirrors the frontend demo board.
SEED_COLUMNS = ["Backlog", "Discovery", "In Progress", "Review", "Done"]
SEED_CARDS = {
    "Backlog": [
        ("Align roadmap themes", "Draft quarterly themes with impact statements and metrics."),
        ("Gather customer signals", "Review support tags, sales notes, and churn feedback."),
    ],
    "Discovery": [
        ("Prototype analytics view", "Sketch initial dashboard layout and key drill-downs."),
    ],
    "In Progress": [
        ("Refine status language", "Standardize column labels and tone across the board."),
        ("Design card layout", "Add hierarchy and spacing for scanning dense lists."),
    ],
    "Review": [
        ("QA micro-interactions", "Verify hover, focus, and loading states."),
    ],
    "Done": [
        ("Ship marketing page", "Final copy approved and asset pack delivered."),
        ("Close onboarding sprint", "Document release notes and share internally."),
    ],
}


# --- Helpers (shared with the AI route) ---


def get_or_create_board(db: Session, user: User) -> KanbanBoard:
    """Return the user's board, seeding columns and demo cards on first access."""
    board = db.query(KanbanBoard).filter(KanbanBoard.user_id == user.id).first()
    if board:
        return board

    board = KanbanBoard(user_id=user.id, title="My Board")
    db.add(board)
    db.flush()  # assign board.id without a full commit

    for position, name in enumerate(SEED_COLUMNS):
        column = KanbanColumn(board_id=board.id, title=name, position=position)
        db.add(column)
        db.flush()
        for card_position, (title, description) in enumerate(SEED_CARDS.get(name, [])):
            db.add(
                Card(
                    column_id=column.id,
                    title=title,
                    description=description,
                    position=card_position,
                )
            )
    db.commit()
    db.refresh(board)
    return board


def board_columns(db: Session, board: KanbanBoard) -> list[KanbanColumn]:
    return (
        db.query(KanbanColumn)
        .filter(KanbanColumn.board_id == board.id)
        .order_by(KanbanColumn.position)
        .all()
    )


def serialize_board(db: Session, board: KanbanBoard) -> BoardOut:
    columns = board_columns(db, board)
    column_ids = [c.id for c in columns]
    cards = (
        db.query(Card)
        .filter(Card.column_id.in_(column_ids))
        .order_by(Card.position)
        .all()
        if column_ids
        else []
    )
    return BoardOut(
        columns=[ColumnOut.model_validate(c) for c in columns],
        cards=[CardOut.model_validate(c) for c in cards],
    )


def _column_for_user(db: Session, board: KanbanBoard, column_id: int) -> KanbanColumn:
    column = (
        db.query(KanbanColumn)
        .filter(KanbanColumn.id == column_id, KanbanColumn.board_id == board.id)
        .first()
    )
    if column is None:
        raise HTTPException(status_code=404, detail="Column not found")
    return column


def _card_for_user(db: Session, board: KanbanBoard, card_id: int) -> Card:
    column_ids = [c.id for c in board_columns(db, board)]
    card = (
        db.query(Card)
        .filter(Card.id == card_id, Card.column_id.in_(column_ids))
        .first()
    )
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")
    return card


def _renumber(db: Session, column_id: int) -> None:
    """Reassign contiguous positions 0..n to a column's cards by current order."""
    cards = (
        db.query(Card)
        .filter(Card.column_id == column_id)
        .order_by(Card.position, Card.id)
        .all()
    )
    for index, card in enumerate(cards):
        card.position = index


def create_card_db(
    db: Session, board: KanbanBoard, column_id: int, title: str, description: str
) -> Card:
    _column_for_user(db, board, column_id)
    if not title.strip():
        raise HTTPException(status_code=400, detail="Title is required")
    count = db.query(Card).filter(Card.column_id == column_id).count()
    card = Card(
        column_id=column_id, title=title, description=description, position=count
    )
    db.add(card)
    db.commit()
    db.refresh(card)
    return card


def update_card_db(db: Session, board: KanbanBoard, card_id: int, data: CardUpdate) -> Card:
    card = _card_for_user(db, board, card_id)

    if data.title is not None:
        card.title = data.title
    if data.description is not None:
        card.description = data.description

    moving = data.column_id is not None or data.position is not None
    if moving:
        source_column_id = card.column_id
        target_column_id = data.column_id if data.column_id is not None else card.column_id
        _column_for_user(db, board, target_column_id)

        # Build the target ordering excluding the card, then insert it.
        siblings = (
            db.query(Card)
            .filter(Card.column_id == target_column_id, Card.id != card.id)
            .order_by(Card.position, Card.id)
            .all()
        )
        insert_at = data.position if data.position is not None else len(siblings)
        insert_at = max(0, min(insert_at, len(siblings)))

        card.column_id = target_column_id
        siblings.insert(insert_at, card)
        for index, sibling in enumerate(siblings):
            sibling.position = index

        if source_column_id != target_column_id:
            # Flush so the moved card's new column_id is visible to the
            # source-column query below (the session has autoflush off).
            db.flush()
            _renumber(db, source_column_id)

    db.commit()
    db.refresh(card)
    return card


def delete_card_db(db: Session, board: KanbanBoard, card_id: int) -> None:
    card = _card_for_user(db, board, card_id)
    column_id = card.column_id
    db.delete(card)
    db.commit()
    _renumber(db, column_id)
    db.commit()


def rename_column_db(
    db: Session, board: KanbanBoard, column_id: int, title: str
) -> KanbanColumn:
    if not title.strip():
        raise HTTPException(status_code=400, detail="Name is required")
    column = _column_for_user(db, board, column_id)
    column.title = title
    db.commit()
    db.refresh(column)
    return column


# --- Routes ---


@router.get("/kanban", response_model=BoardOut)
def get_kanban(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    board = get_or_create_board(db, user)
    return serialize_board(db, board)


@router.post("/cards", response_model=CardOut, status_code=201)
def create_card(
    payload: CardCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    board = get_or_create_board(db, user)
    card = create_card_db(db, board, payload.column_id, payload.title, payload.description)
    return CardOut.model_validate(card)


@router.patch("/cards/{card_id}", response_model=CardOut)
def update_card(
    card_id: int,
    payload: CardUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    board = get_or_create_board(db, user)
    card = update_card_db(db, board, card_id, payload)
    return CardOut.model_validate(card)


@router.delete("/cards/{card_id}")
def delete_card(
    card_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    board = get_or_create_board(db, user)
    delete_card_db(db, board, card_id)
    return {"status": "ok", "id": card_id}


@router.patch("/columns/{column_id}", response_model=ColumnOut)
def rename_column(
    column_id: int,
    payload: ColumnRename,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    board = get_or_create_board(db, user)
    column = rename_column_db(db, board, column_id, payload.title)
    return ColumnOut.model_validate(column)
