import os
from dotenv import load_dotenv
import sqlite3

# Load environment variables from .env
load_dotenv()

# Database path from .env
DATABASE_PATH = os.getenv("DATABASE_URL", "selected_markets.sqlite")

def get_connection():
    """
    Returns a SQLite connection to the selected markets database.
    """
    return sqlite3.connect(DATABASE_PATH, check_same_thread=False)


def fetch_event_tickers():
    """
    Fetches all distinct market_event_ticker values from the selected_markets table.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT market_event_ticker FROM selected_markets")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]