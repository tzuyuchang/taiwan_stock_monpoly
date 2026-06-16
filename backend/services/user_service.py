# backend/services/user_service.py

from sqlalchemy.orm import Session
from ...database import models, repositories as repo
from ...core.time_engine import TimeEngine
from ... import schemas
from fastapi import HTTPException # For raising API errors

class UserService:
    def __init__(self, db: Session, time_engine: TimeEngine):
        self.db = db
        self.time_engine = time_engine

    def get_player_profile(self, player_profile_id: int) -> models.PlayerProfile:
        """Fetches player profile, raising 404 if not found."""
        profile = repo.get_player_profile(self.db, player_profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Player profile not found")
        return profile

    def execute_work_action(self, player_profile_id: int) -> models.PlayerProfile:
        """
        Handles the logic for a player performing their assigned work action.
        Advances time, applies rewards, and updates stats.
        """
        player_profile = self.get_player_profile(player_profile_id)
        
        # 1. Check if player has an active job assignment
        active_job_assignment = repo.get_active_player_job(self.db, player_profile_id)
        if not active_job_assignment or active_job_assignment.completed_at is not None:
            raise HTTPException(status_code=400, detail="No active job assignment found.")
            
        job = repo.get_job_by_id(self.db, active_job_assignment.job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Assigned job not found.")

        # 2. Check for sufficient stamina (MVP: assume always sufficient for now)
        # In a future version:
        # if player_profile.stamina < job.stamina_cost:
        #     raise HTTPException(status_code=400, detail="Not enough stamina to work.")

        # 3. Advance Game Time by the duration of the job cycle
        # The time engine handles advancing time and triggering daily events if a day boundary is crossed.
        hours_to_advance = job.work_cycle_duration_hours
        updated_player_profile = self.time_engine.advance_game_time(player_profile, hours_to_advance)

        # 4. Apply Rewards and Stat Gains
        updated_player_profile.cash += job.base_salary
        updated_player_profile.experience += job.experience_gain
        updated_player_profile.intelligence += job.intelligence_gain
        updated_player_profile.work_ethic += job.work_ethic_gain
        # player_profile.stamina -= job.stamina_cost # Deduct stamina

        # 5. Mark Job Assignment as Completed
        repo.complete_player_job(self.db, active_job_assignment.id)

        # 6. Save all updates to the database
        # We update the profile itself, and also the job assignment status.
        # The time engine already commits its time updates.
        update_data = {
            "cash": updated_player_profile.cash,
            "experience": updated_player_profile.experience,
            "intelligence": updated_player_profile.intelligence,
            "work_ethic": updated_player_profile.work_ethic,
            # "stamina": player_profile.stamina,
        }
        final_profile = repo.update_player_profile(self.db, player_profile_id, update_data)

        return final_profile

    # --- Add other user-related service methods here ---
    # e.g., methods for managing investments, gambling, etc.

# --- Helper function to get DB and TimeEngine dependency ---
# This would typically be injected where needed, e.g., in API endpoints
def get_user_service(db: Session = Depends(repo.get_db)): # Use repo.get_db for consistency
    time_engine = TimeEngine(db=db) # Instantiate TimeEngine with the DB session
    return UserService(db=db, time_engine=time_engine)

# Example of how to use this service in an API endpoint:
# from fastapi import Depends, FastAPI
# app = FastAPI()
#
# @app.post("/api/v1/work")
# async def work_endpoint(
#     user_service: UserService = Depends(get_user_service)
#     # ... other dependencies like current_user
# ):
#     # Assume current_user is available and has an ID
#     current_user_id = 1 # Placeholder
#     profile = user_service.execute_work_action(player_profile_id=current_user_id)
#     return profile

