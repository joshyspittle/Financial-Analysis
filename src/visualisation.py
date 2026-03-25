import yfinance as yf
import pandas as pd
from lightweight_charts import Chart

def price_chart(ohlcv_data, identifier):

    df = ohlcv_data.copy().reset_index()
    df.columns = [c.lower() for c in df.columns]
    df['date'] = pd.to_datetime(df['date']).astype('datetime64[ns]')#.dt.strftime('%Y-%m-%d')
    df = df.dropna(subset=['open', 'high', 'low', 'close'])
    df = df[['date', 'open', 'high', 'low', 'close', 'volume']]

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

    chart.show(block=True)