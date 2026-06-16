
# backend/core/time_engine.py

import random
from datetime import date, timedelta, datetime
import asyncio
import logging
import os # Import os module

from sqlalchemy import create_engine, inspect, insert, update, select, MetaData
from sqlalchemy.orm import Session, sessionmaker
from dotenv import load_dotenv

# --- Setup logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Load environment variables ---
# Assumes DATABASE_URL is set in a .env file or environment
load_dotenv() 
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:your_password@localhost:5432/taiwan_stock_game_mvp") # Default if not set

# --- Database Setup ---
try:
    engine = create_engine(DATABASE_URL)
    metadata = MetaData()
    # Reflect existing tables from the database
    metadata.reflect(bind=engine) 

    # --- Debugging: Inspect game_state_table columns ---
    if "game_state" in metadata.tables:
        logging.info("game_state table found. Inspecting columns:")
        for col in metadata.tables["game_state"].columns:
            logging.info(f"  - Column: {col.name}, Type: {col.type}")
    else:
        logging.warning("game_state table not found in metadata reflection.")
    # --- End Debugging ---

    # Get table objects - ensure table names match your schema exactly
    game_state_table = metadata.tables.get("game_state")
    player_profile_table = metadata.tables.get("player_profile")
    historical_stock_data_table = metadata.tables.get("historical_stock_data")
    bank_loans_table = metadata.tables.get("bank_loans")
    
    # Check if all necessary tables were found
    if game_state_table is None or \
       player_profile_table is None or \
       historical_stock_data_table is None or \
       bank_loans_table is None:
        missing_tables = []
        if game_state_table is None: missing_tables.append("game_state_table")
        if player_profile_table is None: missing_tables.append("player_profile_table")
        if historical_stock_data_table is None: missing_tables.append("historical_stock_data_table")
        if bank_loans_table is None: missing_tables.append("bank_loans_table")
        raise ValueError(f"One or more required tables not found: {', '.join(missing_tables)}. Ensure db/init_schema.sql has been run correctly.")

except Exception as e:
    logging.error(f"Error setting up database connection or reflecting tables: {e}")
    # In a real app, you might want more robust error handling or retry logic
    # If DB connection fails critically, subsequent operations will likely fail.
    # For now, we raise the exception to halt further execution if setup fails.
    raise

# --- Database Session Provider ---
# This function creates and yields a DB session. It's intended to be used as a dependency.
def get_db_session():
    """Provides a database session."""
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()

# --- Database Interaction Functions ---

def get_current_game_date(db: Session) -> date | None:
    """Fetches the current game date from the game_state table."""
    try:
        # Select the most recent game date
        stmt = select(game_state_table.c.game_day).order_by(game_state_table.c.created_at.desc()).limit(1)
        result = db.execute(stmt).scalar()
        if result is None:
            logging.warning("No game date found in game_state. Returning today's date as fallback.")
            return date.today()
        return result
    except Exception as e:
        logging.error(f"Error fetching current game date: {e}")
        return date.today() # Fallback

def advance_game_date(db: Session, new_date: date):
    """Updates the game date in the game_state table."""
    try:
        # Find the latest game state entry and update its date
        # Using a subquery to get the ID of the latest entry
        latest_game_state_id_stmt = select(game_state_table.c.id).order_by(game_state_table.c.created_at.desc()).limit(1).scalar_subquery()
        stmt = update(game_state_table).where(game_state_table.c.id == latest_game_state_id_stmt).values(game_day=new_date)
        
        result = db.execute(stmt)
        if result.rowcount == 0:
            logging.warning(f"Could not find a game state entry to update date to {new_date}. Maybe the table is empty?")
            # Attempt to insert a new one if none exists
            insert_stmt = insert(game_state_table).values(game_day=new_date)
            db.execute(insert_stmt)

        db.commit()
        logging.info(f"Advanced game date to {new_date}")
    except Exception as e:
        logging.error(f"Error advancing game date: {e}")
        db.rollback()

def get_players_for_daily_update(db: Session):
    """Fetches players whose stats need daily updates."""
    try:
        # Fetch players who are not bankrupt (cash > 0) and potentially active
        stmt = select(player_profile_table).where(player_profile_table.c.cash > 0) 
        result = db.execute(stmt).fetchall()
        players = [dict(row._mapping) for row in result] # Convert SQLAlchemy Row to dictionary
        logging.debug(f"Fetched {len(players)} players for daily update.")
        return players
    except Exception as e:
        logging.error(f"Error fetching players for daily update: {e}")
        return []

def get_player_loans(db: Session, player_id: int):
    """Gets active (not defaulted) loans for a player."""
    try:
        stmt = select(bank_loans_table).where(
            bank_loans_table.c.player_id == player_id,
            bank_loans_table.c.is_defaulted == False
        )
        result = db.execute(stmt).fetchall()
        loans = [dict(row._mapping) for row in result]
        logging.debug(f"Fetched {len(loans)} active loans for player {player_id}.")
        return loans
    except Exception as e:
        logging.error(f"Error fetching loans for player {player_id}: {e}")
        return []

def get_loan_interest_rate(loan_type: str) -> float:
    """Returns the daily interest rate for a loan type."""
    rates = {
        "credit": 0.000137,  # Approx 5% APR / 365 days
        "loan_shark": 0.1,   # High daily rate, e.g., 10% daily for loan sharks
    }
    return rates.get(loan_type, 0.0) # Default to 0 if type unknown

def update_player_cash(db: Session, player_id: int, new_cash: float):
    """Updates a player's cash balance."""
    try:
        # Ensure cash doesn't go below zero due to floating point issues
        new_cash = max(0.0, new_cash)
        stmt = update(player_profile_table).where(player_profile_table.c.player_id == player_id).values(cash=new_cash)
        db.execute(stmt)
        # Commit will happen at the end of the daily tick process
    except Exception as e:
        logging.error(f"Error updating cash for player {player_id}: {e}")
        # Rollback handled by caller

def update_player_stamina(db: Session, player_id: int, new_stamina: int):
    """Updates a player's stamina."""
    try:
        # Ensure stamina stays within bounds (0-100)
        new_stamina = max(0, min(100, new_stamina))
        stmt = update(player_profile_table).where(player_profile_table.c.player_id == player_id).values(stamina=new_stamina)
        db.execute(stmt)
    except Exception as e:
        logging.error(f"Error updating stamina for player {player_id}: {e}")

def update_loan_balance(db: Session, loan_id: int, new_balance: float):
    """Updates a loan's current balance."""
    try:
        # Ensure balance doesn't go below zero
        new_balance = max(0.0, new_balance)
        stmt = update(bank_loans_table).where(bank_loans_table.c.loan_id == loan_id).values(current_balance=new_balance)
        db.execute(stmt)
    except Exception as e:
        logging.error(f"Error updating loan balance for loan {loan_id}: {e}")

def mark_loan_as_defaulted(db: Session, loan_id: int):
    """Marks a loan as defaulted."""
    try:
        stmt = update(bank_loans_table).where(bank_loans_table.c.loan_id == loan_id).values(is_defaulted=True)
        db.execute(stmt)
        logging.warning(f"Loan {loan_id} marked as defaulted.")
    except Exception as e:
        logging.error(f"Error marking loan {loan_id} as defaulted: {e}")

def get_active_stock_tickers(db: Session):
    """Gets a list of unique stock tickers currently considered active."""
    try:
        # Assuming historical_stock_data contains all tickers we care about.
        stmt = select(historical_stock_data_table.c.stock_ticker.distinct())
        result = db.execute(stmt).scalars().fetchall()
        logging.debug(f"Fetched {len(result)} active stock tickers.")
        return result if result else []
    except Exception as e:
        logging.error(f"Error fetching active stock tickers: {e}")
        return []

def get_todays_stock_data(db: Session, ticker: str, game_date: date):
    """
    Fetches simulated stock data for a specific ticker and game day from the database.
    """
    try:
        stmt = select(historical_stock_data_table).where(
            historical_stock_data_table.c.stock_ticker == ticker,
            historical_stock_data_table.c.game_date == game_date
        )
        result = db.execute(stmt).fetchone()
        if result:
            # Convert SQLAlchemy Row to dictionary
            return dict(result._mapping)
        else:
            logging.warning(f"No historical data found for {ticker} on {game_date}. Returning mock data.")
            # Fallback to mock data if specific day's data isn't found
            # This fallback should ideally not be hit if dummy data generation is comprehensive
            return {
                "open_price": round(random.uniform(50, 500), 2),
                "close_price": round(random.uniform(50, 500), 2),
                "high_price": round(random.uniform(50, 500), 2),
                "low_price": round(random.uniform(50, 500), 2),
                "volume": random.randint(10000, 10000000),
                "event_type": None,
                "event_impact": 0.0
            }
    except Exception as e:
        logging.error(f"Error fetching historical data for {ticker} on {game_date}: {e}")
        return None # Indicate failure

def update_stock_market_price(db: Session, ticker: str, current_game_date: date):
    """
    Fetches and simulates the update for a stock's market price for the given game date.
    In a real game, this might update a central 'market_status' or similar table.
    For MVP, we simply log the intended update.
    """
    stock_data = get_todays_stock_data(db, ticker, current_game_date)
    if stock_data:
        # In a real game, you'd have a mechanism to store/update "current" market prices
        # For MVP, we'll just log that it would be updated based on the fetched data.
        logging.info(f"Simulating market update for {ticker} on {current_game_date}: Close Price = {stock_data.get('close_price')}")
        # Placeholder for actual market price update logic (e.g., updating a 'current_market_prices' table)
        pass
    else:
        logging.warning(f"Could not get stock data for {ticker} on {current_game_date}, market price not updated.")


# --- Main Daily Tick Logic ---

async def process_daily_tick(db: Session):
    """
    Executes the daily updates for the game.
    This function is called by the scheduler at the defined interval.
    """
    logging.info("Starting daily tick process...")
    
    # 1. Get current game date and determine next date
    current_date = get_current_game_date(db)
    if current_date is None: 
        logging.error("Could not retrieve current game date. Aborting daily tick.")
        return
        
    next_date = current_date + timedelta(days=1)
    
    # 2. Advance Game Date
    advance_game_date(db, next_date)
    
    # 3. Process Players
    players = get_players_for_daily_update(db)
    for player_data in players:
        player_id = player_data['player_id']
        current_cash = float(player_data['cash']) # Ensure cash is float for calculations
        
        # --- Stamina Update ---
        stamina_recovery_base = 5 # Base recovery per day
        housing = player_data.get('housing', 'Rooftop Rental') # Default housing if not specified
        
        if housing == "City Apartment":
            stamina_recovery_base += 5
        elif housing == "Luxury Mansion":
            stamina_recovery_base += 10
            
        new_stamina = player_data['stamina'] + stamina_recovery_base
        update_player_stamina(db, player_id, new_stamina)

        # --- Loan Processing ---
        active_loans = get_player_loans(db, player_id)
        player_cash_after_loans = current_cash # Track cash remaining after loan payments
        
        # Sort loans by due date or type if needed, for now process in order fetched
        for loan in active_loans:
            loan_id = loan['loan_id']
            loan_type = loan['loan_type']
            current_balance = float(loan['current_balance'])
            interest_rate_daily = get_loan_interest_rate(loan_type)
            
            daily_interest_amount = current_balance * interest_rate_daily
            
            # Determine payment: prioritize paying interest. If not enough cash, check for default.
            payment_possible = player_cash_after_loans
            
            if payment_possible >= daily_interest_amount:
                # Player can afford at least the interest
                payment_to_make = min(daily_interest_amount, current_balance) # Cannot pay more than the loan balance
                
                update_loan_balance(db, loan_id, current_balance - payment_to_make)
                player_cash_after_loans -= payment_to_make # Deduct from player's available cash for this tick
                logging.debug(f"Player {player_id} paid {payment_to_make:.2f} interest on loan {loan_id}. Remaining cash: {player_cash_after_loans:.2f}")
            else:
                # Player cannot afford even the interest, mark as defaulted
                mark_loan_as_defaulted(db, loan_id)
                logging.warning(f"Player {player_id} defaulted on loan {loan_id} (balance: {current_balance:.2f}, interest: {daily_interest_amount:.2f}, available cash: {payment_possible:.2f})")
                # In a real game, this would trigger game events (asset seizure, etc.)

        # Update player's cash after all loan processing for the day
        update_player_cash(db, player_id, player_cash_after_loans)

    # 4. Process Stocks
    active_tickers = get_active_stock_tickers(db)
    for ticker in active_tickers:
        # Fetch and simulate market update using data for the *next* game day
        # This ensures that when players check the market, they see the prices for the day that just advanced.
        update_stock_market_price(db, ticker, next_date) 

    # Commit all DB changes for this tick
    try:
        db.commit()
        logging.info("Daily tick process completed and committed successfully.")
    except Exception as e:
        logging.error(f"Error committing daily tick changes: {e}")
        db.rollback()

# --- Scheduler Task ---

async def run_daily_updates_scheduler(db_session_maker):
    """
    Scheduler task that runs the process_daily_tick at a set interval.
    Interval is set to 3600 seconds (1 hour) to simulate 1 game day per real hour.
    """
    UPDATE_INTERVAL_SECONDS = 3600 # 1 hour = 1 game day
    
    logging.info(f"Daily updates scheduler started. Will run every {UPDATE_INTERVAL_SECONDS} seconds.")
    
    while True:
        db = None # Initialize db to None
        try:
            # Get a DB session for this tick using the provided maker function
            # db_session_maker should be a callable (like a generator function) that provides a session
            db_generator = db_session_maker()
            db = next(db_generator) # Get the session
            
            await process_daily_tick(db)
            
        except Exception as e:
            logging.error(f"An unhandled exception occurred during daily tick processing: {e}")
            # Ensure session is closed even if error occurs
            if db: db.rollback() # Rollback if an error occurred before commit
        finally:
            # Ensure session is closed
            if db: 
                db.close()
        
        # Wait for the next interval
        await asyncio.sleep(UPDATE_INTERVAL_SECONDS)

# --- Utility to get DB session maker (if not provided externally) ---
# This is a fallback if app.py doesn't provide a get_db_session compatible function
# and assumes direct access to engine.
def get_default_db_session_maker():
    """Creates a sessionmaker and returns a function that yields sessions."""
    local_engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=local_engine)
    
    def db_session_generator():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    return db_session_generator

# --- Functions to be called from FastAPI lifespan ---
# These are placeholders for how the scheduler would be started/stopped.
# The actual task creation and cancellation will happen in app.py's lifespan.

async def start_time_engine_scheduler(app_state, db_session_maker_func):
    """
    Starts the time engine scheduler task. 'app_state' is FastAPI's app.state.
    'db_session_maker_func' is the callable that provides DB sessions (e.g., get_db_session).
    """
    if not callable(db_session_maker_func):
        logging.error("Invalid db_session_maker_func provided to start_time_engine_scheduler.")
        return
        
    logging.info("Attempting to start Time Engine Scheduler task...")
    # Create a task that runs the scheduler loop indefinitely
    app_state.time_engine_task = asyncio.create_task(
        run_daily_updates_scheduler(db_session_maker_func)
    )
    logging.info("Time Engine Scheduler task created.")

async def stop_time_engine_scheduler(app_state):
    """
    Stops the time engine scheduler task gracefully. 'app_state' is FastAPI's app.state.
    """
    logging.info("Attempting to stop Time Engine Scheduler...")
    if hasattr(app_state, 'time_engine_task') and app_state.time_engine_task:
        app_state.time_engine_task.cancel()
        try:
            await app_state.time_engine_task
        except asyncio.CancelledError:
            logging.info("Time Engine Scheduler task cancelled successfully.")
    else:
        logging.warning("Time Engine Scheduler task not found or already stopped.")
    logging.info("Time Engine Scheduler stop sequence finished.")

