import os
from datetime import datetime, time as dt_time, timedelta
from dotenv import load_dotenv
import streamlit as st
from database.database import fetch_event_tickers
from app.market_analyzer import MarketAnalyzer

# Load environment variables
load_dotenv()

def main():
    st.set_page_config(page_title="Market Price Action", layout="wide")
    st.title("Market Price Action")

    analyzer = MarketAnalyzer()

    # Step 1: select an event (market_event_ticker) from the DB
    events = fetch_event_tickers()
    if not events:
        st.error("No event tickers found in the database.")
        return
    selected_event = st.selectbox("Select Event:", options=events)

    # Step 2: retrieve markets by event_ticker
    markets_map = analyzer.fetch_markets_for_event(selected_event)
    if not markets_map:
        st.warning(f"No markets found for event {selected_event}.")
        return
    selected_market = st.selectbox("Select Market:", options=list(markets_map.keys()))
    series_id = markets_map[selected_market]

    # Interval and date range
    interval = st.selectbox("Interval (minutes):", [1, 60, 1440], index=1)
    today = datetime.today().date()
    default_start = today - timedelta(days=1)
    default_end = today
    date_range = st.date_input("Select Date Range:", [default_start, default_end])
    if len(date_range) != 2:
        st.warning("Please select both a start and end date.")
        return
    start_date, end_date = date_range
    start_ts = int(datetime.combine(start_date, dt_time.min).timestamp())
    end_ts = int(datetime.combine(end_date, dt_time.max).timestamp())

    # Fetch candlestick data
    df = analyzer.get_candlestick_dataframe(
        ticker=selected_market,
        series_id=series_id,
        interval=interval,
        start_ts=start_ts,
        end_ts=end_ts
    )
    if df.empty:
        st.warning("No data for the selected market in this date range.")
        return

    # CSV download button
    csv_dir = os.getenv("CSVS_URL", "./csvs")
    file_name = f"{selected_market}-{start_date}_{end_date}.csv"
    csv_path = os.path.join(csv_dir, file_name)
    if st.button("Save CSV"):
        os.makedirs(csv_dir, exist_ok=True)
        df.to_csv(csv_path)
        st.success(f"CSV saved to {csv_path}")

    # Plot
    fig = analyzer.create_price_action_figure(df)
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()