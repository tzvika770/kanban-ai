from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..schemas import LoginRequest, LoginResponse
from ..auth import create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Hardcoded MVP credentials
DEFAULT_USERNAME = "user"
DEFAULT_PASSWORD = "password"


def get_or_create_user(db: Session, username: str) -> User:
    """Get existing user or create default user (for MVP)"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        # For MVP, use empty password hash since we check hardcoded credentials
        user = User(username=username, password_hash="")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Login endpoint with hardcoded credentials for MVP
    
    Default credentials:
    - username: user
    - password: password
    """
    # Check hardcoded credentials
    if request.username != DEFAULT_USERNAME or request.password != DEFAULT_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Get or create user in database
    user = get_or_create_user(db, DEFAULT_USERNAME)
    
    # Generate JWT token
    token = create_access_token({"sub": user.username, "user_id": user.id})
    
    return LoginResponse(
        access_token=token,
        username=user.username
    )


@router.post("/logout")
def logout():
    """
    Logout endpoint
    
    Note: With JWT, logout is mainly handled on the client-side by removing the token.
    This endpoint can be used for future blacklist implementation.
    """
    return {"message": "Logged out successfully"}
