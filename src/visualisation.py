import yfinance as yf
import pandas as pd
from lightweight_charts import Chart

if __name__ == "__main__":

    # --- Data ingestion (same as before) ---
    df = yf.download('BTC-USD', interval='1d', period='max')
    
    df = df.droplevel(1, axis=1)
    df.index.name = 'Date'
    df = df.reset_index()
    df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
    df.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
    
    df['date'] = pd.to_datetime(df['date']).astype('datetime64[ns]')#.dt.strftime('%Y-%m-%d')

    # Drop any NaN rows
    df = df.dropna(subset=['open', 'high', 'low', 'close'])
    print(df.head().to_string())
    # --- Chart ---
    chart = Chart()

    chart.layout(
        background_color='#0f0f0f',
        text_color='#d1d4dc',
        font_size=12,
    )

    chart.candle_style(
        up_color='#26a69a',
        down_color='#ef5350',
        wick_up_color='#26a69a',
        wick_down_color='#ef5350',
    )

    chart.volume_config(up_color='#26a69a55', down_color='#ef535055')

    chart.crosshair(mode='normal')

    chart.time_scale(right_offset=5, min_bar_spacing=2)

    chart.topbar.textbox('symbol', 'BTC-USD')

    # Pass the OHLCV data
    chart.set(df)

    # Save data same as before
    df.to_csv('btc_data.csv', index=False)

    chart.show(block=True)