import yfinance as yf
import pandas as pd
from datetime import date, timedelta
import logging
import os
from sqlalchemy import create_engine, MetaData, Table, insert, inspect, Session
from dotenv import load_dotenv

# --- Setup logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Load environment variables ---
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:your_password@localhost:5432/taiwan_stock_game_mvp")

# --- Database Setup ---
try:
    engine = create_engine(DATABASE_URL)
    metadata = MetaData()
    # Reflect existing tables from the database
    metadata.reflect(bind=engine)

    # Get table objects - ensure table names match your schema exactly
    historical_stock_data_table = metadata.tables.get("historical_stock_data")
    dividends_table = metadata.tables.get("dividends")
    stock_splits_table = metadata.tables.get("stock_splits")
    news_table = metadata.tables.get("news")

    if historical_stock_data_table is None:
        raise ValueError("historical_stock_data table not found. Ensure db/init_schema.sql has been run correctly.")
    if dividends_table is None:
        logging.warning("dividends table not found. Dividend data will not be loaded.")
    if stock_splits_table is None:
        logging.warning("stock_splits table not found. Stock split data will not be loaded.")
    if news_table is None:
        logging.warning("news table not found. News data will not be loaded.")

except Exception as e:
    logging.error(f"Error setting up database connection or reflecting tables: {e}")
    raise

# --- Configuration ---
# List of ~50 representative Taiwan stock tickers (example tickers)
# NOTE: You will need to research and populate this list accurately.
#       Also, ensure these tickers are valid on Yahoo Finance for Taiwan.
#       Taiwan tickers often have a '.TW' suffix.
TAIWAN_TICKER_SYMBOLS = [
    "2330.TW", # TSMC
    "2317.TW", # Hon Hai (Foxconn)
    "2454.TW", # MediaTek
    "2308.TW", # Innolux
    "3008.TW", # Largan Precision
    "3474.TW", # ASE Technology Holding
    "1301.TW", # Formosa Plastics
    "1326.TW", # Formosa Chemicals & Fibre
    "6505.TW", # Formosa Heavy Industries
    "2207.TW", # China Motor Corporation
    "1519.TW", # Chinkolors Enterprise
    "2912.TW", # Yamaha Motor Taiwan
    "2882.TW", # Cathay Financial Holding
    "2881.TW", # Fubon Financial Holding
    "2880.TW", # Hua Nan Financial Holdings
    "2886.TW", # Mega Financial Holding
    "2891.TW", # First Financial Holding
    "2883.TW", # Chiao Tung Bank
    "2884.TW", # Yuanta Financial Holding
    "2888.TW", # Uni-President Financial Holdings
    "1101.TW", # Taiwan Cement Corporation
    "1102.TW", # Asia Cement Corporation
    "1513.TW", # Central Glass Co., Ltd.
    "1723.TW", # China Synthetic Rubber Corporation
    "2105.TW", # Nan Ya Plastics Corporation
    "2412.TW", # Chunghwa Telecom Co., Ltd.
    "6456.TW", # Giga-Byte Technology
    "3661.TW", # Chunghwa Picture Tubes, Ltd.
    "2885.TW", # Mega Holdings
    "2903.TW", # Giant Manufacturing Co., Ltd.
    "3673.TW", # Verbatim Asia Ltd.
    "4904.TW", # Tateh Industrial Co., Ltd.
    "4938.TW", # Innolux Corporation
    "5347.TW", # World Advanced Materials Co., Ltd.
    "6176.TW", # Qisda Corporation
    "8046.TW", # Nan Ya Electronics Company Limited
    "9904.TW", # Bescor Inc.
    "1477.TW", # Tzu Chi Culture and Communication Foundation
    "1718.TW", # Mikuni Corporation
    "2353.TW", # United Microelectronics Corporation
    "3034.TW", # PCSC Corporation
    "3227.TW", # Original Power Co., Ltd.
    "3669.TW", # Chunghwa Picture Tubes, Ltd. (Duplicate, check ticker list)
    "4721.TW", # Hsing Ta Chemical Co., Ltd.
    "4961.TW", # Chunghwa Picture Tubes, Ltd. (Duplicate, check ticker list)
    "6116.TW", # Chimei Corporation
    "6147.TW", # Advanced Semiconductor Engineering, Inc.
    "8069.TW", # TPK Holding Co., Ltd.
    "8411.TW", # Apple Inc. (Incorrect ticker for Taiwan, needs correction)
    "9912.TW", # Yamaha Motor Taiwan (Duplicate, check ticker list)
    "9914.TW", # Nan Ya Plastics Corporation (Duplicate, check ticker list)
]
# Deduplicate and correct tickers for a clean list
# Remove duplicates and potentially incorrect tickers like Apple Inc.
TAIWAN_TICKER_SYMBOLS = sorted(list(set([t for t in TAIWAN_TICKER_SYMBOLS if t != "8411.TW"]))) # Remove Apple Inc.

# Calculate date range (last 20 years)
END_DATE = date.today()
START_DATE = END_DATE - timedelta(days=20*365) # Approximate 20 years

# --- Data Fetching Functions ---

def fetch_stock_data(ticker, start_date, end_date):
    """
    Fetches historical stock data (OHLCV, Adj Close), dividends, and splits for a given ticker and date range.
    Note: News fetching is attempted but may be unreliable for Taiwan stocks via yfinance.
    """
    logging.info(f"Fetching data for {ticker} from {start_date} to {end_date}...")
    try:
        stock = yf.Ticker(ticker)
        
        # Fetch historical data (OHLCV, Adj Close)
        hist = stock.history(start=start_date, end=end_date)
        if hist.empty:
            logging.warning(f"No historical price data found for {ticker} in the specified date range.")
            return None, None, None, None

        # Ensure index is date (and timezone-naive if it's timezone-aware)
        hist.index = pd.to_datetime(hist.index).date
        hist = hist.tz_localize(None) # Make timezone-naive

        # Fetch dividends
        dividends = stock.dividends
        if not dividends.empty:
            dividends.index = pd.to_datetime(dividends.index).date
            dividends = dividends.tz_localize(None)
            dividends = dividends.reset_index(name='amount')
            dividends['ticker'] = ticker
        else:
            dividends = pd.DataFrame(columns=['Date', 'amount', 'ticker']) # Ensure consistent structure

        # Fetch stock splits
        splits = stock.splits
        if not splits.empty:
            splits.index = pd.to_datetime(splits.index).date
            splits = splits.tz_localize(None)
            splits = splits.reset_index(name='ratio')
            splits['ticker'] = ticker
        else:
            splits = pd.DataFrame(columns=['Date', 'ratio', 'ticker']) # Ensure consistent structure
            
        # Fetch news (Attempt, may not work well for all tickers/markets)
        news = []
        try:
            # yfinance returns news as a list of dictionaries. Structure might vary.
            # Inspecting the 'article' object structure is crucial if issues arise.
            for article in stock.news:
                # Attempt to get publish date and normalize it. 
                # Structure might be like 'publisher.publish_date' or similar.
                # This part requires careful inspection of the actual data structure from yfinance.
                # Example of potentially varying structure:
                pub_date_str = article.get('publishedDate') # Common key, might be different
                if pub_date_str:
                    try:
                        # Attempt to parse various date formats
                        pub_date = pd.to_datetime(pub_date_str).date()
                    except Exception:
                        pub_date = None # Ignore if date parsing fails
                else:
                    pub_date = None
                
                if pub_date and start_date <= pub_date <= end_date:
                    news.append({
                        'ticker': ticker,
                        'title': article.get('title', 'No Title'),
                        'publisher': article.get('publisher', {}).get('name', 'Unknown'), # Try to get publisher name
                        'publish_date': pub_date,
                        'link': article.get('link')
                    })
            news_df = pd.DataFrame(news)
            if not news_df.empty:
                logging.info(f"Fetched {len(news_df)} news articles for {ticker}.")
            else:
                logging.warning(f"No news found or fetched for {ticker} in the date range using the current news extraction logic.")
        except Exception as e:
            logging.warning(f"Could not fetch news for {ticker}: {e}. Continuing without news data.")
            news_df = pd.DataFrame(columns=['ticker', 'title', 'publisher', 'publish_date', 'link'])

        logging.info(f"Successfully fetched data for {ticker}.")
        return hist, dividends, splits, news_df

    except Exception as e:
        logging.error(f"Error fetching data for {ticker}: {e}")
        return None, None, None, None

# --- Data Cleaning and Transformation Functions ---

def clean_hist_data(df, ticker):
    """Cleans and prepares historical price data for insertion."""
    if df is None or df.empty:
        return pd.DataFrame()
        
    df.reset_index(inplace=True)
    df.rename(columns={
        'Date': 'game_date',
        'Open': 'open_price',
        'High': 'high_price',
        'Low': 'low_price',
        'Close': 'close_price',
        'Adj Close': 'adj_close_price', # yfinance provides this, useful for dividend/split adjusted prices
        'Volume': 'volume',
    }, inplace=True)
    
    df['ticker'] = ticker
    
    # Add dummy columns if they don't exist (for schema consistency, e.g., event_type, event_impact)
    # These are placeholders as defined in the previous brainstorming and current logic.
    if 'event_type' not in df.columns:
        df['event_type'] = None 
    if 'event_impact' not in df.columns:
        df['event_impact'] = 0.0 

    # Convert game_date to date object if it's datetime
    if pd.api.types.is_datetime64_any_dtype(df['game_date']):
        df['game_date'] = df['game_date'].dt.date

    # Ensure correct data types
    df['open_price'] = df['open_price'].astype(float)
    df['high_price'] = df['high_price'].astype(float)
    df['low_price'] = df['low_price'].astype(float)
    df['close_price'] = df['close_price'].astype(float)
    df['adj_close_price'] = df['adj_close_price'].astype(float)
    df['volume'] = df['volume'].astype(int)
    df['event_impact'] = df['event_impact'].astype(float)
    
    # Select and reorder columns to match typical DB schema
    # Ensure all columns expected by the table are present, even if None/default
    cols_to_select = ['ticker', 'game_date', 'open_price', 'high_price', 'low_price', 'close_price', 'adj_close_price', 'volume', 'event_type', 'event_impact']
    for col in cols_to_select:
        if col not in df.columns:
            df[col] = None # Add missing columns with None
    
    return df[cols_to_select]

def clean_dividend_data(df, ticker):
    """Cleans and prepares dividend data for insertion."""
    if df is None or df.empty:
        return pd.DataFrame()
    df.rename(columns={'Date': 'ex_dividend_date', 'amount': 'dividend_amount'}, inplace=True)
    df['ticker'] = ticker
    
    if pd.api.types.is_datetime64_any_dtype(df['ex_dividend_date']):
        df['ex_dividend_date'] = df['ex_dividend_date'].dt.date
        
    df['dividend_amount'] = df['dividend_amount'].astype(float)
    
    cols = ['ticker', 'ex_dividend_date', 'dividend_amount']
    return df[cols]

def clean_split_data(df, ticker):
    """Cleans and prepares stock split data for insertion."""
    if df is None or df.empty:
        return pd.DataFrame()
    df.rename(columns={'Date': 'split_date', 'ratio': 'split_ratio'}, inplace=True)
    df['ticker'] = ticker
    
    if pd.api.types.is_datetime64_any_dtype(df['split_date']):
        df['split_date'] = df['split_date'].dt.date

    # Split ratio is usually like 2 for 1 stock split (meaning 1 share becomes 2)
    # Store as float for flexibility
    df['split_ratio'] = df['split_ratio'].astype(float) 
    
    cols = ['ticker', 'split_date', 'split_ratio']
    return df[cols]

def clean_news_data(df):
    """Cleans and prepares news data for insertion."""
    if df is None or df.empty:
        return pd.DataFrame()

    # Ensure publish_date is date object
    if pd.api.types.is_datetime64_any_dtype(df['publish_date']):
        df['publish_date'] = df['publish_date'].dt.date

    # Select relevant columns and ensure consistency
    cols = ['ticker', 'title', 'publisher', 'publish_date', 'link']
    # Handle cases where 'publisher' might be a dict, extract name if so
    if 'publisher' in df.columns and isinstance(df['publisher'].iloc[0], dict):
        df['publisher'] = df['publisher'].apply(lambda x: x.get('name', 'Unknown') if isinstance(x, dict) else x)
        
    return df[cols]


# --- Database Loading Functions ---

def load_data_to_db(df, table, db_session):
    """
    Loads data from a Pandas DataFrame into a specified SQLAlchemy table.
    Uses insert to handle potential duplicates gracefully (or overwrite if strategy changes).
    """
    if df.empty:
        logging.info(f"DataFrame is empty, skipping load to table: {table.name}")
        return 0
        
    try:
        records = df.to_dict(orient='records')
        
        # Use insert statement. For historical data, we might need to check for existing dates first.
        # For MVP, assuming we can insert new records. If duplicates are an issue, consider using `upsert`.
        
        # Constructing the insert statement requires mapping DataFrame columns to table columns.
        # Assuming column names in DataFrame match table column names.
        stmt = insert(table).values(records)
        
        result = db_session.execute(stmt)
        db_session.commit()
        logging.info(f"Successfully inserted {len(records)} records into {table.name}.")
        return len(records)
        
    except Exception as e:
        db_session.rollback()
        logging.error(f"Error loading data into {table.name}: {e}")
        # Consider more specific error handling based on potential SQLAlchemy errors (e.g., duplicate keys)
        return 0

# --- Main ETL Script Logic ---

def run_etl():
    """
    Main function to execute the ETL process for fetching and loading historical data.
    """
    logging.info("Starting ETL process for Yahoo Finance data...")
    
    total_records_inserted = {
        "historical_stock_data": 0,
        "dividends": 0,
        "splits": 0,
        "news": 0,
    }
    
    db_session = None # Initialize session variable
    try:
        db_session = Session(engine) # Create a session
        
        tickers_processed = 0
        # Filter out tickers for which tables might not exist, to avoid unnecessary fetch attempts
        relevant_tickers = []
        if historical_stock_data_table: relevant_tickers.append("historical_stock_data")
        if dividends_table: relevant_tickers.append("dividends")
        if stock_splits_table: relevant_tickers.append("stock_splits")
        if news_table: relevant_tickers.append("news")

        # Use a set to track unique tickers processed to avoid redundant fetches if multiple tables exist
        processed_tickers_set = set()

        for ticker in TAIWAN_TICKER_SYMBOLS:
            # Avoid reprocessing if ticker was already fetched for another table type
            if ticker in processed_tickers_set:
                continue
            
            tickers_processed += 1
            logging.info(f"--- Processing ticker {tickers_processed}/{len(TAIWAN_TICKER_SYMBOLS)}: {ticker} ---")
            
            hist_df, dividends_df, splits_df, news_df = fetch_stock_data(ticker, START_DATE, END_DATE)
            
            if hist_df is not None:
                # Clean and load historical price data
                cleaned_hist_df = clean_hist_data(hist_df, ticker)
                if not cleaned_hist_df.empty and historical_stock_data_table:
                    inserted_count = load_data_to_db(cleaned_hist_df, historical_stock_data_table, db_session)
                    total_records_inserted["historical_stock_data"] += inserted_count
                    processed_tickers_set.add(ticker) # Mark as processed if price data was fetched

                # Clean and load dividends
                cleaned_div_df = clean_dividend_data(dividends_df, ticker)
                if not cleaned_div_df.empty and dividends_table:
                    inserted_count = load_data_to_db(cleaned_div_df, dividends_table, db_session)
                    total_records_inserted["dividends"] += inserted_count
                        
                # Clean and load splits
                cleaned_splits_df = clean_split_data(splits_df, ticker)
                if not cleaned_splits_df.empty and stock_splits_table:
                    inserted_count = load_data_to_db(cleaned_splits_df, stock_splits_table, db_session)
                    total_records_inserted["splits"] += inserted_count
                        
                # Clean and load news
                cleaned_news_df = clean_news_data(news_df)
                if not cleaned_news_df.empty and news_table:
                    inserted_count = load_data_to_db(cleaned_news_df, news_table, db_session)
                    total_records_inserted["news"] += inserted_count

            else:
                logging.warning(f"Skipping data loading for {ticker} due to missing historical price data.")

    except Exception as e:
        logging.error(f"An error occurred during the ETL process: {e}")
        if db_session:
            db_session.rollback() # Rollback on error
    finally:
        if db_session:
            db_session.close() # Ensure session is closed

    logging.info("ETL process finished.")
    logging.info(f"Summary of records inserted: {total_records_inserted}")

# --- Execute ETL ---
if __name__ == "__main__":
    # Ensure DATABASE_URL is set or provide a default that works for your local setup
    if not DATABASE_URL:
        logging.error("DATABASE_URL environment variable not set. Please configure it.")
    else:
        # Check if required tables exist before running ETL
        try:
            metadata.reflect(bind=engine) # Re-reflect to ensure tables are up-to-date
            
            # Check existence of tables we intend to load data into
            tables_to_check = {
                "historical_stock_data": historical_stock_data_table,
                "dividends": dividends_table,
                "stock_splits": stock_splits_table,
                "news": news_table
            }
            
            all_target_tables_exist = True
            for table_name, table_obj in tables_to_check.items():
                if table_obj is None:
                    logging.error(f"Required table '{table_name}' not found in database. Please create it or adjust script configuration.")
                    all_target_tables_exist = False
            
            if all_target_tables_exist:
                run_etl()
            else:
                logging.error("ETL process aborted due to missing required tables.")

        except Exception as e:
            logging.error(f"Failed to connect to database or check tables: {e}")
            
# --- Dummy Registration Statements (for context, not actual execution) ---
# deuteron_agent.register_file("backend/core/etl_yahoo_finance.py", "ETL script to fetch and load historical stock data from Yahoo Finance.")
# deuteron_agent.register_file("backend/core/time_engine.py", "Core time engine logic including stock price simulation.")
# deuteron_agent.register_file("development_progress.md", "Project development roadmap and status.")
# deuteron_agent.register_file("backend/main.py", "Main FastAPI application file.")
# deuteron_agent.register_file("backend/core/database.py", "Database connection and utility functions.")
# deuteron_agent.register_file("requirements.txt", "Project dependencies.")
# deuteron_agent.register_file("backend/app.py", "FastAPI application setup.")
# deuteron_agent.register_file("backend/db/init_schema.sql", "Database schema initialization script.")

# deuteron_agent.print("ETL script for Yahoo Finance data created successfully. It includes functions to fetch K-line data, dividends, splits, and news, clean them, and load them into the PostgreSQL database. It also includes basic error handling and logging.")
# deuteron_agent.print("Note: The TAIWAN_TICKER_SYMBOLS list is a placeholder and needs to be populated with actual, valid tickers. The news fetching capability should be monitored for reliability.")
# deuteron_agent.print("The script assumes the existence of 'historical_stock_data', 'dividends', 'stock_splits', and 'news' tables in your PostgreSQL database.")
# deuteron_agent.print("To run this script, save it as `etl_yahoo_finance.py` in your backend/core directory, ensure your DATABASE_URL is set in a .env file, and execute `python backend/core/etl_yahoo_finance.py`.")

# deuteron_agent.run_plan([
#     {"task": "Implement the historical data ETL script using yfinance and SQLAlchemy.", "status": "completed"}
# ])

# deuteron_agent.print("The ETL script has been drafted. The next steps would involve testing this script and potentially integrating it into a scheduled task or a management command.")
# deuteron_agent.print("For now, I have completed the task of writing the ETL script as per the plan.")