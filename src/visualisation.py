"""Chart formatting and plotting helpers.

Assumptions:
- Input OHLCV data uses capitalized columns and a datetime index.
- Analysis overlays are computed from the asset's ``Close`` column.
- Data is reformatted for ``lightweight-charts`` immediately before plotting.
"""

from functools import partial
from typing import Any, Callable

import pandas as pd
from lightweight_charts import Chart


def plot_chart(
    ohlcv_data: pd.DataFrame,
    analysis_fn: Callable[..., pd.Series | pd.DataFrame] | None = None,
    **kwargs: Any,
) -> None:
    """Render a candlestick chart with an optional analysis overlay."""

    clean_ohlcv_data = format_ohlcv(ohlcv_data)
    chart = plot_price(clean_ohlcv_data)

    if analysis_fn is not None:
        fn = partial(analysis_fn, **kwargs) if kwargs else analysis_fn
        clean_analysis_data, name = format_analysis(ohlcv_data, fn)
        chart = plot_analysis(clean_analysis_data, name, chart)

    chart.show(block=True)


def plot_price(ohlcv_data: pd.DataFrame) -> Chart:
    """Create and populate the base candlestick chart."""

    chart = Chart()

    chart.layout(
        background_color='#0b0e11',
        text_color='#d1d4dc',
        font_size=12,
        font_family='Trebuchet MS',
    )

    chart.grid(vert_enabled=True, horz_enabled=True, color='#2B2B43')

    chart.candle_style(
        up_color='#26a69a',
        down_color='#ef5350',
        wick_up_color='#26a69a',
        wick_down_color='#ef5350',
        border_visible=False,
    )

    chart.volume_config(up_color='#26a69a55', down_color='#ef535055')
    chart.crosshair(mode='normal')
    chart.time_scale(right_offset=5, min_bar_spacing=0.1)
    chart.topbar.textbox('symbol', 'BTC-USD')

    def on_scale_selection(chart: Chart) -> None:
        selection = chart.topbar['Scale'].value
        if selection == 'Linear':
            chart.price_scale(mode='normal')
        else:
            chart.price_scale(mode=selection.lower())

    chart.topbar.menu(
        name='Scale',
        options=('Linear', 'Logarithmic', 'Percentage'),
        default='Linear',
        func=on_scale_selection,
    )

    chart.set(ohlcv_data)
    return chart


def plot_analysis(analysis_data: pd.DataFrame, name: str, chart: Chart) -> Chart:
    """Add one line-based analysis overlay to an existing chart."""

    line = chart.create_line(
        name=name,
        color='#ffcc00',
        style='solid',
        width=2,
        price_line=True,
        price_label=True,
    )
    chart.legend(visible=True)
    line.set(analysis_data)

    return chart


def format_ohlcv(ohlcv_data: pd.DataFrame) -> pd.DataFrame:
    """Convert project OHLCV format into lightweight-charts format."""

    df = ohlcv_data.copy().reset_index()
    df.columns = [c.lower() for c in df.columns]
    df['date'] = pd.to_datetime(df['date']).astype('datetime64[ns]')
    df = df.dropna(subset=['open', 'high', 'low', 'close'])

    return df[['date', 'open', 'high', 'low', 'close', 'volume']]


def format_analysis(
    ohlcv_data: pd.DataFrame,
    analysis_fn: Callable[..., pd.Series | pd.DataFrame],
) -> tuple[pd.DataFrame, str]:
    """Run an analysis function and format its output for charting."""

    fn_name = analysis_fn.func.__name__ if hasattr(analysis_fn, 'func') else analysis_fn.__name__
    name = fn_name.replace('_', ' ').title()

    close_data = ohlcv_data['Close']
    analysis = analysis_fn(close_data)
    analysis = analysis.reindex(ohlcv_data.index)

    clean_analysis = analysis.reset_index()
    clean_analysis.columns = ['date', name]
    clean_analysis['date'] = pd.to_datetime(clean_analysis['date']).astype('datetime64[ns]')
    clean_analysis = clean_analysis.dropna()

    return clean_analysis, name
