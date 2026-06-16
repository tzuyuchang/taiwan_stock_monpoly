# backend/api/v1/endpoints/user.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from ... import schemas
from ...database import models
from ...database import repositories as repo
# Assuming you have a dependency to get the current authenticated user
# from ...core.security import get_current_active_user 
from ...database.session import get_db

router = APIRouter()

# Placeholder for dependency to get current user
# In a real app, this would parse JWT from headers and return the User model
async def get_current_user_placeholder(db: Session = Depends(get_db)):
    # For now, let's assume a user with ID 1 exists for testing purposes
    # In a real app, this would look up the user based on the token's subject (e.g., user ID or username)
    user = db.query(models.User).filter(models.User.id == 1).first()
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

# --- API Endpoints for User Profile ---

@router.get("/profile", response_model=schemas.PlayerProfile)
def get_my_profile(
    # current_user: models.User = Depends(get_current_active_user), # Use this in production
    current_user: models.User = Depends(get_current_user_placeholder), # Placeholder for now
    db: Session = Depends(get_db)
):
    """
    Retrieves the profile of the currently authenticated user.
    """
    player_profile = repo.get_player_profile(db, user_id=current_user.id)
    if not player_profile:
        # This case should ideally not happen if profile is created on user registration
        raise HTTPException(status_code=404, detail="Player profile not found")
        
    # Return as Pydantic schema
    return schemas.PlayerProfile.from_orm(player_profile)

@router.put("/profile", response_model=schemas.PlayerProfile)
def update_my_profile(
    # current_user: models.User = Depends(get_current_active_user), # Use this in production
    current_user: models.User = Depends(get_current_user_placeholder), # Placeholder for now
    profile_update: schemas.PlayerProfileUpdate, # Schema for partial updates
    db: Session = Depends(get_db)
):
    """
    Updates the profile of the currently authenticated user.
    Allows updating fields like display_name, stats, etc.
    """
    player_profile = repo.get_player_profile(db, user_id=current_user.id)
    if not player_profile:
        raise HTTPException(status_code=404, detail="Player profile not found")

    # Convert Pydantic model to dictionary for easier update
    update_data = profile_update.dict(exclude_unset=True) # Only include fields that were provided

    # Example: Prevent direct manipulation of critical fields if needed
    # update_data.pop("cash", None) 
    # update_data.pop("loan_amount", None)
    
    updated_profile = repo.update_player_profile(db, player_profile.id, update_data)
    
    return schemas.PlayerProfile.from_orm(updated_profile)

# --- Placeholder for other user-related endpoints ---
# e.g., get player's assets, get current job status, etc.
# These will likely call services which then use repositories.
