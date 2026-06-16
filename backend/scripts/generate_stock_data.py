
import random
from datetime import date, timedelta

def generate_dummy_stock_data(num_stocks=5, num_days=30):
    """Generates dummy historical stock data for a specified number of stocks and days."""
    
    tickers = [f"STOCK{i:03d}" for i in range(1, num_stocks + 1)]
    start_date = date.today() - timedelta(days=num_days)
    
    stock_data = []
    
    for ticker in tickers:
        # Initial price can vary
        initial_price = round(random.uniform(50.0, 500.0), 2)
        current_price = initial_price
        
        for i in range(num_days):
            current_date = start_date + timedelta(days=i)
            
            # Simulate daily price fluctuation
            # Use a more gentle random walk for prices
            price_change_percent = random.uniform(-0.05, 0.05) # Max 5% change per day
            
            # Ensure price doesn't go below a minimum (e.g., 1.00)
            new_price = max(1.00, round(current_price * (1 + price_change_percent), 2))
            
            open_price = current_price # Open price is previous close price
            high_price = max(new_price, open_price) + round(random.uniform(0, abs(new_price - open_price)*0.5), 2) # High is above open/close
            low_price = min(new_price, open_price) - round(random.uniform(0, abs(new_price - open_price)*0.5), 2) # Low is below open/close
            low_price = max(1.00, low_price) # Ensure low price is not below minimum
            
            # Simulate volume - generally higher volume on bigger price changes
            volume_change_factor = abs(price_change_percent) * 1000000 # Scale factor for volume
            volume = int(max(10000, random.gauss(1000000, volume_change_factor))) # Base volume + fluctuation

            # Simulate occasional events (e.g., earnings report, news)
            event_type = None
            event_impact = 0.0
            if random.random() < 0.05: # 5% chance of an event
                event_type = random.choice(['earnings_positive', 'earnings_negative', 'news_positive', 'news_negative', 'dividend'])
                impact_multiplier = random.uniform(0.02, 0.15) # Event impact between 2% and 15%
                if 'positive' in event_type:
                    event_impact = round(new_price * impact_multiplier, 2)
                    new_price = max(1.00, round(new_price * (1 + impact_multiplier), 2))
                elif 'negative' in event_type:
                    event_impact = round(new_price * -impact_multiplier, 2)
                    new_price = max(1.00, round(new_price * (1 - impact_multiplier), 2))
                elif event_type == 'dividend':
                    event_impact = round(new_price * random.uniform(0.01, 0.03), 2) # Small dividend payout
            
            stock_data.append({
                "ticker": ticker,
                "game_date": current_date.isoformat(),
                "open_price": open_price,
                "high_price": high_price,
                "low_price": low_price,
                "close_price": new_price,
                "volume": volume,
                "event_type": event_type,
                "event_impact": event_impact
            })
            
            current_price = new_price # Update current price for next day's open
            
    return stock_data

if __name__ == "__main__":
    dummy_data = generate_dummy_stock_data(num_stocks=5, num_days=30)
    
    # This part would typically insert into a database.
    # For now, we'll just print it to show the structure.
    # In a real FastAPI app, you'd use SQLAlchemy or similar ORM.
    
    import json
    print(json.dumps(dummy_data, indent=2))

    # Example of how to potentially insert into DB (requires DB connection setup)
    # from sqlalchemy import create_engine
    # from models import HistoricalStockData # Assuming you have a SQLAlchemy model defined
    #
    # DATABASE_URL = "postgresql://user:password@host:port/dbname" # Replace with your actual DB URL
    # engine = create_engine(DATABASE_URL)
    #
    # with engine.connect() as connection:
    #     for data in dummy_data:
    #         # Create an instance of your SQLAlchemy model
    #         # stock_entry = HistoricalStockData(**data)
    #         # connection.execute(HistoricalStockData.__table__.insert().values(**data))
    #         pass # Placeholder for actual DB insertion
    #
    # print(f"Generated and printed {len(dummy_data)} dummy data entries.")

