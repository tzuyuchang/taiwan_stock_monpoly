# backend/api/v1/endpoints/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from ... import schemas # Import Pydantic schemas
from ...database import models # Import SQLAlchemy models
from ...database import repositories as repo
from ...core.security import verify_password, create_access_token # Assumes security.py exists
from ...database.session import get_db
from ...config import settings # Assumes settings.py exists for JWT secret etc.

router = APIRouter()

# --- API Endpoints for Authentication ---

@router.post("/register", response_model=schemas.User)
def register_user(
    user_create: schemas.UserCreate, 
    db: Session = Depends(get_db)
):
    """
    Registers a new user.
    """
    db_user = repo.get_user_by_username(db, username=user_create.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    # Hash the password before creating the user
    hashed_password = user_create.password # In a real app, use security.hash_password(user_create.password)
    
    # Create user in DB
    user_data = {"username": user_create.username, "hashed_password": hashed_password}
    db_user = repo.create_user(db, user_data)
    
    # Create initial player profile for the new user
    # Default values will be used from models.py, but we can override here
    # Example: Set starting destiny based on some logic or user choice
    player_profile_data = {
        "user_id": db_user.id,
        "starting_destiny": schemas.StartingDestinyType.ACADEMIC_ELITE, # Defaulting for now
        "cash": 50000.0, # Example starting cash
        "intelligence": 15, # Example stat boost
        "analysis": 15
    }
    repo.create_player_profile(db, player_profile_data)
    
    return schemas.User.from_orm(db_user)

@router.post("/token", response_model=schemas.Token)
def login_for_access_token(
    form_data: schemas.OAuth2PasswordRequestForm = Depends(), # Use form data for username/password
    db: Session = Depends(get_db)
):
    """
    Logs in a user and returns an access token.
    """
    user = repo.get_user_by_username(db, username=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password): # Assumes verify_password exists
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Define token expiration (e.g., 1 hour)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Example of how to protect an endpoint (requires Authorization header)
# @router.get("/users/me", response_model=schemas.User)
# def read_users_me(current_user: models.User = Depends(get_current_user)): # Assumes get_current_user dependency
#     return current_user

