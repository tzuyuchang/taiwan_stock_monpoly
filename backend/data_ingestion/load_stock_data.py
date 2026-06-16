# backend/data_ingestion/load_stock_data.py

import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime
import os

# --- Configuration ---
# Use the same database URL as defined in models.py
# For production, this would point to your PostgreSQL instance.
# For local development, it might point to a local PostgreSQL or remain SQLite for initial testing.
# Ensure the URL is correctly configured for your environment.
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./stock_data.db") # Default to a local SQLite for simplicity if env var not set

# Define the path to your sample historical stock data CSV file.
# IMPORTANT: You'll need to provide this file. For MVP, a small subset is fine.
# Example: 'data/historical_stock_data/sample_stocks.csv'
SAMPLE_DATA_PATH = os.environ.get("SAMPLE_STOCK_DATA_PATH", "data/historical_stock_data/sample_stocks.csv")

# Define the table name in the database
STOCK_DATA_TABLE_NAME = "historical_stock_data"

def load_stock_data(data_path: str = SAMPLE_DATA_PATH, db_url: str = DATABASE_URL):
    """
    Loads historical stock data from a CSV file into the database.
    Assumes CSV has columns like: Date, Ticker, Open, High, Low, Close, Volume
    """
    print(f"Attempting to load stock data from: {data_path}")
    print(f"Connecting to database: {db_url}")

    try:
        # Create database engine
        engine = create_engine(db_url)

        # Read the CSV file using pandas
        df = pd.read_csv(data_path)

        # --- Data Cleaning and Transformation ---
        # 1. Convert 'Date' column to datetime objects and ensure it's in a standard format (e.g., UTC)
        #    Make sure your CSV date format is correctly parsed. Adjust format string if needed.
        try:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce') 
            # Assuming dates are in local time, convert to UTC if needed for consistency
            # df['Date'] = df['Date'].dt.tz_localize('Asia/Taipei').dt.tz_convert('UTC') 
        except Exception as e:
            print(f"Warning: Could not parse Date column automatically. Error: {e}. Please ensure date format is consistent.")
            # Attempt with a specific format if default fails
            # df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d', errors='coerce')

        # Drop rows where Date could not be parsed
        df.dropna(subset=['Date'], inplace=True)
        
        # Ensure Ticker is string
        df['Ticker'] = df['Ticker'].astype(str)
        
        # Ensure numeric columns are numeric, coercing errors to NaN then dropping
        numeric_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        df.dropna(subset=numeric_cols, inplace=True) # Remove rows with invalid numeric data

        # Rename columns to match potential database schema if necessary (e.g., snake_case)
        df.columns = df.columns.str.lower().str.replace(' ', '_') # Convert to snake_case
        # Example: If CSV has 'Date', 'Ticker', 'Open', 'High', 'Low', 'Close', 'Volume'
        # it becomes 'date', 'ticker', 'open', 'high', 'low', 'close', 'volume'

        print(f"Data loaded successfully. Found {len(df)} valid rows.")
        print("Sample data head:")
        print(df.head())

        # --- Load data into PostgreSQL ---
        # Use 'replace' to drop the table if it exists and create a new one,
        # or 'append' to add data to an existing table.
        # For initial loading, 'replace' is often safer to start fresh.
        df.to_sql(STOCK_DATA_TABLE_NAME, con=engine, if_exists='replace', index=False)

        print(f"Successfully loaded {len(df)} rows into table '{STOCK_DATA_TABLE_NAME}'.")

    except FileNotFoundError:
        print(f"Error: Data file not found at {data_path}")
    except Exception as e:
        print(f"An error occurred during data loading: {e}")

if __name__ == "__main__":
    # Ensure the data directory exists if not present
    data_dir = os.path.dirname(SAMPLE_DATA_PATH)
    if data_dir and not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"Created directory: {data_dir}")

    # Create a dummy CSV file for testing if it doesn't exist
    if not os.path.exists(SAMPLE_DATA_PATH):
        print(f"Creating dummy data file at {SAMPLE_DATA_PATH} for demonstration.")
        dummy_data = {
            'Date': ['2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05', '2023-01-06'],
            'Ticker': ['2330.TW', '2330.TW', '2330.TW', '2330.TW', '2330.TW'],
            'Open': [450.0, 455.0, 460.0, 458.0, 462.0],
            'High': [455.0, 461.0, 462.0, 460.0, 465.0],
            'Low': [448.0, 452.0, 458.0, 455.0, 460.0],
            'Close': [455.0, 460.0, 462.0, 459.0, 464.0],
            'Volume': [100000, 120000, 110000, 90000, 130000]
        }
        dummy_df = pd.DataFrame(dummy_data)
        dummy_df.to_csv(SAMPLE_DATA_PATH, index=False)
        print("Dummy CSV created.")

    load_stock_data()

