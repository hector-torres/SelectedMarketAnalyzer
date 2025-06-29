import os
import time
import logging
import pandas as pd
import requests
from typing import Dict, Any

# Configure debug logging based on DEBUG env var
DEBUG = os.getenv("DEBUG", "0") == "1"
logger = logging.getLogger(__name__)
if DEBUG:
    logging.basicConfig(level=logging.DEBUG)

class MarketAnalyzer:
    # Base endpoint for listing markets
    MARKET_LISTING_URL = "https://api.elections.kalshi.com/trade-api/v2/markets"
    SERIES_URL = "https://api.elections.kalshi.com/trade-api/v2/series"

    def fetch_markets_for_event(self, event_ticker: str) -> Dict[str, Dict[str, Any]]:
        """
        Retrieves all market info for a given event_ticker.
        Returns mapping ticker -> {"series_id": ..., "title": ...}.
        """
        url = f"{self.MARKET_LISTING_URL}?event_ticker={event_ticker}"
        if DEBUG:
            logger.debug(f"Listing markets for event: {url}")
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json().get("markets", [])
        result = {}
        for m in data:
            ticker = m.get("ticker")
            series_id = m.get("event_ticker")
            title = m.get("title")
            if ticker and series_id:
                result[ticker] = {"series_id": series_id, "title": title}
        return result

    def get_candlestick_dataframe(
        self,
        ticker: str,
        series_id: str,
        interval: int = 60,
        start_ts: int = None,
        end_ts: int = None,
    ) -> pd.DataFrame:
        """
        Fetches candlestick data for a market under its series.
        """
        now = int(time.time())
        end_ts = end_ts or now
        start_ts = start_ts or (end_ts - 24 * 3600)

        url = f"{self.SERIES_URL}/{series_id}/markets/{ticker}/candlesticks"
        params = {"start_ts": start_ts, "end_ts": end_ts, "period_interval": interval}
        if DEBUG:
            req = requests.Request("GET", url, params=params).prepare()
            logger.debug(f"Fetching candlesticks: {req.url}")

        resp = requests.get(url, params=params)
        resp.raise_for_status()
        candles = resp.json().get("candlesticks", [])

        records = []
        for candle in candles:
            ts = candle.get("end_period_ts")
            time_dt = pd.to_datetime(ts, unit="s")
            price_info = candle.get("price", {})
            price_close = price_info.get("close") if price_info.get("close") is not None else price_info.get("previous")
            records.append({"ticker": ticker, "price_close": price_close, "time": time_dt})

        df = pd.DataFrame(records)
        if df.empty:
            return df
        return df.set_index("time").sort_index()

    def create_price_action_figure(self, df: pd.DataFrame, chart_title: str):
        """
        Creates a Plotly line chart showing price action for each ticker.
        """
        import plotly.graph_objects as go
        fig = go.Figure()
        for ticker in df["ticker"].unique():
            ticker_df = df[df["ticker"] == ticker]
            fig.add_trace(go.Scatter(
                x=ticker_df.index,
                y=ticker_df["price_close"],
                mode="lines+markers",
                name=ticker,
                line=dict(width=2, shape="hvh"),
                hovertemplate=(
                    f"<b>Ticker:</b> {ticker}<br>" +
                    "<b>Time:</b> %{x}<br>" +
                    "<b>Price:</b> %{y:.2f}<br>" +
                    "<extra></extra>"
                )
            ))
        fig.update_layout(
            template="plotly_dark",
            title=chart_title,
            xaxis=dict(title="Time"),
            yaxis=dict(title="Price", range=[0, 100]),
            showlegend=True,
            margin=dict(t=40, b=40, l=40, r=40),
            height=600
        )
        return fig