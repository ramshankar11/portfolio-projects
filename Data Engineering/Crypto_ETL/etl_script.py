import requests
import pandas as pd
from datetime import datetime
import os
import sys

# Configuration
COIN_ID = "bitcoin"
VS_CURRENCY = "usd"
DAYS = "30" # Get last 30 days
API_URL = f"https://api.coingecko.com/api/v3/coins/{COIN_ID}/market_chart"

def extract_data():
    """Fetch market chart data from CoinGecko API."""
    params = {
        'vs_currency': VS_CURRENCY,
        'days': DAYS,
        'interval': 'daily'
    }
    
    try:
        print(f"Fetching data for {COIN_ID}...")
        response = requests.get(API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(f"Error fetching data: {e}")
        sys.exit(1)

def transform_data(data):
    """Transform JSON data into a clean DataFrame."""
    prices = data.get('prices', [])
    
    if not prices:
        print("No data found.")
        return pd.DataFrame()

    # Convert to DataFrame
    df = pd.DataFrame(prices, columns=['timestamp', 'price'])
    
    # Convert timestamp to datetime
    df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    # Calculate simple moving average (7-day)
    df['ma_7'] = df['price'].rolling(window=7).mean()
    
    # Add metadata
    df['coin'] = COIN_ID
    df['update_time'] = datetime.now()
    
    # Drop raw timestamp, rearrange
    df = df[['date', 'coin', 'price', 'ma_7', 'update_time']]
    
    # Drop NaN values (first 6 days for MA)
    df = df.dropna()
    
    print(f"Transformed data: {len(df)} rows.")
    return df

def load_data(df):
    """Load data to PostgreSQL."""
    db_user = os.getenv('DB_USER', 'user')
    db_password = os.getenv('DB_PASSWORD', 'password')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'crypto_db')

    connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    try:
        from sqlalchemy import create_engine
        engine = create_engine(connection_string)
        
        print(f"Loading {len(df)} rows to database at {db_host}...")
        # 'replace' invalidates previous data for simplicity in this demo demo
        # For production, use 'append' and handle duplicates
        df.to_sql('market_data', engine, if_exists='replace', index=False)
        print("Data loaded successfully.")
        
    except Exception as e:
        print(f"Error loading to DB: {e}")


def run_pipeline():
    raw_data = extract_data()
    clean_df = transform_data(raw_data)
    load_data(clean_df)

if __name__ == "__main__":
    run_pipeline()
