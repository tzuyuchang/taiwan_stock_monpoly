# backend/api/v1/endpoints/game_actions.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from ... import schemas
from ...database import models
from ...database import repositories as repo
from ...core.time_engine import TimeEngine
from ...services import user_service # Import the user service
from ...database.session import get_db

router = APIRouter()

# Placeholder for getting current user (replace with actual auth dependency)
async def get_current_user_placeholder(db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == 1).first()
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

# --- API Endpoints for Game Actions ---

@router.post("/work", response_model=schemas.PlayerProfile)
def perform_work_action_endpoint(
    # current_user: models.User = Depends(get_current_active_user), # Use in production
    current_user: models.User = Depends(get_current_user_placeholder), # Placeholder
    db: Session = Depends(get_db)
):
    """
    Executes the "Work" action for the player's current job.
    This will advance game time, apply rewards, and update player stats.
    """
    player_profile = repo.get_player_profile(db, user_id=current_user.id)
    if not player_profile:
        raise HTTPException(status_code=404, detail="Player profile not found")

    # Use the service layer to handle the business logic
    # The service will interact with TimeEngine and repositories
    try:
        updated_player_profile = user_service.execute_work_action(
            db=db, 
            player_profile_id=player_profile.id
        )
        # Return the updated profile schema
        return schemas.PlayerProfile.from_orm(updated_player_profile)
        
    except HTTPException as e:
        # Re-raise HTTP exceptions (e.g., Not Found, Bad Request)
        raise e
    except Exception as e:
        # Log the error properly in a real application
        print(f"Error performing work action: {e}")
        raise HTTPException(status_code=500, detail="Failed to perform work action")

# --- Endpoints related to fetching job info ---
# (These might be merged with the existing jobs router or kept separate depending on preference)

@router.get("/jobs/available", response_model=List[schemas.Job])
def get_available_jobs_for_player(
    # current_user: models.User = Depends(get_current_active_user), # Use in production
    current_user: models.User = Depends(get_current_user_placeholder), # Placeholder
    db: Session = Depends(get_db)
):
    """
    Retrieves jobs available for the player's current career.
    """
    player_profile = repo.get_player_profile(db, user_id=current_user.id)
    if not player_profile:
        raise HTTPException(status_code=404, detail="Player profile not found")
        
    # Get jobs matching the player's current career
    available_jobs = repo.get_jobs_by_career(db, player_profile.current_career)
    
    # Filter out jobs the player might not be ready for (e.g., stat requirements - future)
    
    return [schemas.Job.from_orm(job) for job in available_jobs]

# Endpoint to assign player to a job (moved from jobs.py for clarity if preferred)
@router.post("/jobs/assign/{job_id}", response_model=schemas.PlayerJobAssignment)
def assign_player_to_job_endpoint(
    job_id: int,
    # current_user: models.User = Depends(get_current_active_user), # Use in production
    current_user: models.User = Depends(get_current_user_placeholder), # Placeholder
    db: Session = Depends(get_db)
):
    """
    Assigns the player to a specific job.
    """
    player_profile = repo.get_player_profile(db, user_id=current_user.id)
    if not player_profile:
        raise HTTPException(status_code=404, detail="Player profile not found")

    db_job = repo.get_job_by_id(db, job_id)
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Validate career requirement
    if db_job.career_requirement and player_profile.current_career != db_job.career_requirement:
        raise HTTPException(status_code=400, detail=f"Player is not of career type {db_job.career_requirement.value} required for this job.")

    # Assign player to job using repository
    try:
        player_job_assignment = repo.assign_player_to_job(db, player_profile.id, job_id)
        return schemas.PlayerJobAssignment.from_orm(player_job_assignment)
    except Exception as e:
        print(f"Error assigning player to job: {e}")
        raise HTTPException(status_code=500, detail="Failed to assign player to job")

