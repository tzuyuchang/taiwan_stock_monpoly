# backend/api/v1/endpoints/jobs.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ... import schemas # Import Pydantic schemas
from ...database import models # Import SQLAlchemy models
from ...database import repositories as repo
from ...core.time_engine import TimeEngine # Import TimeEngine
from ...database.session import get_db # Import DB dependency

router = APIRouter()

# --- API Endpoints for Jobs ---

@router.get("/jobs", response_model=List[schemas.Job])
def get_available_jobs(
    career_type: models.CareerType = None, # Optional filter by career
    db: Session = Depends(get_db)
):
    """
    Retrieves a list of available jobs.
    Optionally filters by career type.
    """
    jobs = repo.get_jobs_by_career(db, career_type) if career_type else db.query(models.Job).all()
    if not jobs:
        # Return empty list if no jobs found, rather than 404
        return [] 
    
    # Manually convert SQLAlchemy models to Pydantic schemas for response
    job_schemas = [schemas.Job.from_orm(job) for job in jobs]
    return job_schemas

@router.post("/jobs/{job_id}/assign", response_model=schemas.PlayerJobAssignment)
def assign_player_to_job_endpoint(
    job_id: int,
    player_profile_id: int, # Assumes we can get player_profile_id from auth context
    db: Session = Depends(get_db)
):
    """
    Assigns the player to a specific job.
    For MVP, we assume player_profile_id is known. In a real app, this would come from JWT.
    """
    db_job = repo.get_job_by_id(db, job_id)
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Basic validation: Check if player is eligible for this job career-wise
    # In a real app, you'd fetch player_profile using player_profile_id from auth
    db_player_profile = db.query(models.PlayerProfile).filter(models.PlayerProfile.id == player_profile_id).first()
    if not db_player_profile:
         raise HTTPException(status_code=404, detail="Player profile not found")
         
    if db_job.career_requirement and db_player_profile.current_career != db_job.career_requirement:
        raise HTTPException(status_code=400, detail=f"Player is not of career type {db_job.career_requirement.value} required for this job.")

    # Assign player to job
    try:
        player_job_assignment = repo.assign_player_to_job(db, player_profile_id, job_id)
        return schemas.PlayerJobAssignment.from_orm(player_job_assignment)
    except Exception as e:
        # Log the error properly
        print(f"Error assigning player to job: {e}")
        raise HTTPException(status_code=500, detail="Failed to assign player to job")

# Note: Endpoint for completing a job is handled within the 'work' action service,
# as it's tied to the action's completion logic and time advancement.
