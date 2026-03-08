import yfinance as yf
from datetime import datetime, timedelta

# Test your exact tickers
test_tickers = {
    'DOW': '^DJI',  # What ticker are you using?
    'BXY': '^XDB',
    'NIKKEI': '^N225',
    'Canadian Dollar Index': '^XDC'
}

for name, ticker in test_tickers.items():
    print(f"\n=== {name} ({ticker}) ===")
    try:
        data = yf.Ticker(ticker).history(period='5d')
        if data.empty:
            print("❌ No data returned")
        else:
            print(f"✓ Last 3 days:")
            print(data.tail(3))
    except Exception as e:
        print(f"❌ Error: {e}")