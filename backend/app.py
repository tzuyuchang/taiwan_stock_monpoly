
# backend/app.py

import uvicorn
import os
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text # Import text for potential raw SQL queries if needed

# Import your database setup and session provider
# Assumes you have a database.py with get_db function or similar setup
# For this example, we'll define a basic get_db_session directly here if needed,
# but it's better practice to have it in a separate database utility file.
# --- DB Setup Placeholder ---
# In a real project, you'd import this from e.g., database.py
from core.time_engine import get_db_session, start_time_engine_scheduler, stop_time_engine_scheduler
# --- End DB Setup Placeholder ---

# --- Load environment variables ---
from dotenv import load_dotenv
load_dotenv() 

# --- FastAPI Lifespan Manager ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    # Ensure the database engine and session maker are accessible
    # If get_db_session is a generator function, we need to make it available
    # to the scheduler to create sessions.
    app.state.db_session_maker = get_db_session # Make the session provider available
    
    # Start the time engine scheduler background task
    await start_time_engine_scheduler(app.state, app.state.db_session_maker)
    
    print("FastAPI app lifespan: Time Engine Scheduler started.")
    yield
    # --- Shutdown ---
    # Stop the time engine scheduler task gracefully
    await stop_time_engine_scheduler(app.state)
    print("FastAPI app lifespan: Time Engine Scheduler stopped.")

# --- Initialize FastAPI App ---
app = FastAPI(
    title="Taiwan Stock Monopoly Game Backend",
    description="API for the Taiwan Stock Monopoly Game",
    version="0.1.0",
    lifespan=lifespan # Use the lifespan manager for startup/shutdown tasks
)

# --- Root Endpoint for Health Check ---
@app.get("/")
async def read_root():
    """Basic health check endpoint."""
    return {"message": "Taiwan Stock Monopoly Game Backend API is running!"}

# --- Example Endpoint to Get Current Game Date ---
# This demonstrates how to access the game date and uses the get_db_session dependency
@app.get("/game-date")
async def get_game_date_endpoint(db: Session = Depends(get_db_session)):
    """Returns the current game date."""
    try:
        # Fetch current game date using the function from time_engine
        # Note: Ensure get_current_game_date correctly uses the provided 'db' session
        from core.time_engine import get_current_game_date # Import specifically for this function if needed
        
        current_date = get_current_game_date(db) 
        if current_date:
            return {"current_game_date": current_date.isoformat()}
        else:
            raise HTTPException(status_code=500, detail="Could not retrieve current game date.")
    except Exception as e:
        logging.error(f"Error in /game-date endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

# --- Placeholder for other API endpoints ---
# Example: Player creation, stock market data, gambling endpoints would go here.
# @app.post("/player/create")
# async def create_player(...):
#     pass

# --- Running the app (for local development) ---
# This block allows running the app directly using `python backend/app.py`
# However, it's generally recommended to use `uvicorn backend.app:app --reload`
# as it provides better hot-reloading and development features.
if __name__ == "__main__":
    PORT = int(os.getenv("PORT", 8000))
    HOST = os.getenv("HOST", "0.0.0.0")
    
    print(f"Starting FastAPI server on http://{HOST}:{PORT}")
    # Note: The lifespan events might not trigger reliably when running directly via uvicorn.run().
    # Using `uvicorn main:app --reload` is the standard way.
    # If running directly, the background tasks might not start correctly without explicit asyncio handling.
    uvicorn.run(app, host=HOST, port=PORT)

