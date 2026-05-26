from sqlalchemy import Column, Integer, String, DateTime, func
from .database import Base


class User(Base):
    """User model for authentication"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"


class KanbanBoard(Base):
    """Kanban board model"""
    __tablename__ = "kanban_boards"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, unique=True, index=True)
    title = Column(String(100), nullable=False, default="My Board")
    created_at = Column(DateTime, server_default=func.now())


class KanbanColumn(Base):
    """Kanban column model"""
    __tablename__ = "kanban_columns"

    id = Column(Integer, primary_key=True, index=True)
    board_id = Column(Integer, nullable=False, index=True)
    title = Column(String(50), nullable=False)
    position = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class Card(Base):
    """Kanban card model"""
    __tablename__ = "kanban_cards"

    id = Column(Integer, primary_key=True, index=True)
    column_id = Column(Integer, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(String(1000), nullable=True)
    position = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class AIMessage(Base):
    """AI chat message model"""
    __tablename__ = "ai_messages"

    id = Column(Integer, primary_key=True, index=True)
    board_id = Column(Integer, nullable=False, index=True)
    role = Column(String(10), nullable=False)  # "user" or "assistant"
    content = Column(String(2000), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
