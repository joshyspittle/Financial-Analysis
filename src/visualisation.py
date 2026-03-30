"""Chart formatting and plotting helpers.

Assumptions:
- Input OHLCV data uses capitalized columns and a datetime index.
- Analysis overlays are computed from the asset's ``Close`` column.
- Data is reformatted for ``lightweight-charts`` immediately before plotting.
- Overlay studies render on the main price pane, while oscillators can render
  on dedicated subcharts.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from functools import partial
from typing import Any

import pandas as pd
from lightweight_charts import Chart

DEFAULT_ANALYSIS_LAYOUT = {
    'sma': 'overlay',
    'ema': 'overlay',
    'rsi': 'subchart',
    'macd': 'subchart',
}

DEFAULT_SERIES_STYLE = {
    'default': {
        'type': 'line',
        'color': '#ffcc00',
        'width': 2,
        'line_style': 'solid',
        'price_line': True,
        'price_label': True,
    },
    'rsi': {
        'default': {
            'type': 'line',
            'color': '#c77dff',
            'width': 2,
            'price_line': False,
            'price_label': False,
        },
        'guide_lines': [
            {
                'value': 70,
                'color': '#ef5350aa',
                'width': 1,
                'line_style': 'dashed',
                'text': '70',
                'axis_label_visible': False,
            },
            {
                'value': 50,
                'color': '#9aa4b2aa',
                'width': 1,
                'line_style': 'dotted',
                'text': '50',
                'axis_label_visible': False,
            },
            {
                'value': 30,
                'color': '#26a69aaa',
                'width': 1,
                'line_style': 'dashed',
                'text': '30',
                'axis_label_visible': False,
            },
        ],
    },
    'macd': {
        'MACD': {
            'type': 'line',
            'color': '#4fc3f7',
            'width': 2,
            'price_line': False,
            'price_label': False,
        },
        'Signal': {
            'type': 'line',
            'color': '#ffca28',
            'width': 2,
            'line_style': 'dashed',
            'price_line': False,
            'price_label': False,
        },
        'Histogram': {
            'type': 'histogram',
            'positive_color': '#26a69a88',
            'negative_color': '#ef535088',
            'price_line': False,
            'price_label': False,
            'scale_margin_top': 0.12,
            'scale_margin_bottom': 0.12,
        },
    },
}


def plot_chart(
    ohlcv_data: pd.DataFrame,
    analysis_fn: Callable[..., pd.Series | pd.DataFrame] | None = None,
    analyses: Sequence[Callable[..., pd.Series | pd.DataFrame] | dict[str, Any]] | None = None,
    **kwargs: Any,
) -> None:
    """Render a candlestick chart with optional overlays and subcharts."""

    clean_ohlcv_data = format_ohlcv(ohlcv_data)
    analysis_specs = prepare_analyses(ohlcv_data, analysis_fn=analysis_fn, analyses=analyses, **kwargs)
    chart = plot_price(clean_ohlcv_data, subchart_count=count_subcharts(analysis_specs))

    for analysis_spec in analysis_specs:
        plot_analysis(analysis_spec, chart)

    chart.show(block=True)


def plot_price(ohlcv_data: pd.DataFrame, subchart_count: int = 0) -> Chart:
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

    chart.legend(visible=True)
    chart.set(ohlcv_data)

    if subchart_count > 0:
        chart.resize(height=get_main_chart_height(subchart_count))

    return chart


def plot_analysis(analysis_spec: dict[str, Any], chart: Chart) -> Chart:
    """Add one analysis spec to the chart."""

    layout = analysis_spec['layout']
    target_chart = chart

    if layout == 'subchart':
        if not hasattr(chart, '_subcharts'):
            chart._subcharts = []

        panel = chart.create_subchart(
            position='bottom',
            width=1,
            height=get_subchart_height(analysis_spec['total_subcharts']),
            sync=True,
        )
        chart._subcharts.append(panel)
        style_subchart(panel)
        target_chart = panel

    for series_spec in analysis_spec['series']:
        plot_series(series_spec, target_chart)

    plot_guide_lines(
        analysis_spec.get('guide_lines', []),
        target_chart,
        analysis_spec['series'][0]['data'] if analysis_spec['series'] else None,
    )

    return chart


def plot_series(series_spec: dict[str, Any], chart: Chart) -> None:
    """Plot a single line or histogram series on the supplied chart."""

    style = series_spec['style']
    series_type = style.get('type', 'line')

    if series_type == 'histogram':
        series = chart.create_histogram(
            name=series_spec['name'],
            color=style.get('color', '#26a69a'),
            price_line=style.get('price_line', False),
            price_label=style.get('price_label', False),
            scale_margin_top=style.get('scale_margin_top', 0.1),
            scale_margin_bottom=style.get('scale_margin_bottom', 0.1),
        )
    else:
        series = chart.create_line(
            name=series_spec['name'],
            color=style.get('color', '#ffcc00'),
            style=style.get('line_style', 'solid'),
            width=style.get('width', 2),
            price_line=style.get('price_line', True),
            price_label=style.get('price_label', True),
        )

    series.set(series_spec['data'])


def prepare_analyses(
    ohlcv_data: pd.DataFrame,
    analysis_fn: Callable[..., pd.Series | pd.DataFrame] | None = None,
    analyses: Sequence[Callable[..., pd.Series | pd.DataFrame] | dict[str, Any]] | None = None,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """Normalize requested analyses into render-ready specs."""

    requested = normalize_analysis_requests(analysis_fn, analyses, **kwargs)
    prepared: list[dict[str, Any]] = []

    for request in requested:
        fn = request['fn']
        fn_kwargs = request['kwargs']
        fn_name = fn.__name__
        title = request['name'] or build_analysis_name(fn_name, fn_kwargs)
        layout = request.get('layout') or DEFAULT_ANALYSIS_LAYOUT.get(fn_name, 'overlay')
        style = request.get('style')
        series_styles = request.get('series_styles', {})
        guide_lines = request.get('guide_lines')

        close_data = ohlcv_data['Close']
        result = fn(close_data, **fn_kwargs)
        result = result.reindex(ohlcv_data.index)

        series_specs = format_analysis_series(
            result,
            title,
            fn_name,
            style=style,
            series_styles=series_styles,
        )
        prepared.append({
            'name': title,
            'layout': layout,
            'series': series_specs,
            'guide_lines': guide_lines if guide_lines is not None else get_default_guide_lines(fn_name),
        })

    total_subcharts = sum(1 for spec in prepared if spec['layout'] == 'subchart')
    for spec in prepared:
        spec['total_subcharts'] = total_subcharts

    return prepared


def normalize_analysis_requests(
    analysis_fn: Callable[..., pd.Series | pd.DataFrame] | None = None,
    analyses: Sequence[Callable[..., pd.Series | pd.DataFrame] | dict[str, Any]] | None = None,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """Normalize one or many analysis inputs into a common structure."""

    if analyses is None:
        if analysis_fn is None:
            return []
        analyses = [{'fn': analysis_fn, 'kwargs': kwargs}]

    normalized: list[dict[str, Any]] = []

    for item in analyses:
        if callable(item):
            normalized.append({'fn': item, 'kwargs': {}, 'name': None, 'layout': None})
        else:
            normalized.append({
                'fn': item['fn'],
                'kwargs': item.get('kwargs', {}),
                'name': item.get('name'),
                'layout': item.get('layout'),
                'style': item.get('style'),
                'series_styles': item.get('series_styles', {}),
                'guide_lines': item.get('guide_lines'),
            })

    return normalized


def format_analysis_series(
    analysis: pd.Series | pd.DataFrame,
    title: str,
    fn_name: str,
    style: dict[str, Any] | None = None,
    series_styles: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Convert analysis output into one or more plotted series specs."""

    style = style or {}
    series_styles = series_styles or {}

    if isinstance(analysis, pd.Series):
        clean_analysis = analysis.reset_index()
        clean_analysis.columns = ['date', title]
        clean_analysis['date'] = pd.to_datetime(clean_analysis['date']).astype('datetime64[ns]')
        clean_analysis = clean_analysis.dropna()

        default_style = DEFAULT_SERIES_STYLE.get(fn_name, {}).get('default', DEFAULT_SERIES_STYLE['default'])
        final_style = merge_styles(default_style, style)

        return [{
            'name': title,
            'data': clean_analysis,
            'style': final_style,
        }]

    clean_analysis = analysis.copy().reset_index()
    clean_analysis = clean_analysis.rename(columns={clean_analysis.columns[0]: 'date'})
    clean_analysis['date'] = pd.to_datetime(clean_analysis['date']).astype('datetime64[ns]')

    series_specs: list[dict[str, Any]] = []
    style_map = DEFAULT_SERIES_STYLE.get(fn_name, {})

    for column in analysis.columns:
        series_name = f'{title} - {column}'
        column_data = clean_analysis[['date', column]].dropna().copy()
        column_data = column_data.rename(columns={column: series_name})
        default_style = style_map.get(column, DEFAULT_SERIES_STYLE['default'])
        final_style = merge_styles(default_style, style, series_styles.get(column))

        if final_style.get('type') == 'histogram':
            column_data['color'] = column_data[series_name].apply(
                lambda value: (
                    final_style.get('positive_color', '#26a69a88')
                    if value >= 0
                    else final_style.get('negative_color', '#ef535088')
                )
            )

        series_specs.append({
            'name': series_name,
            'data': column_data,
            'style': final_style,
        })

    return series_specs


def build_analysis_name(fn_name: str, fn_kwargs: dict[str, Any]) -> str:
    """Create a readable analysis label, including kwargs when supplied."""

    base_name = fn_name.replace('_', ' ').title()

    if not fn_kwargs:
        return base_name

    params = ', '.join(f'{key}={value}' for key, value in fn_kwargs.items())
    return f'{base_name} ({params})'


def merge_styles(*styles: dict[str, Any] | None) -> dict[str, Any]:
    """Merge one or more style dictionaries from left to right."""

    merged: dict[str, Any] = {}

    for style in styles:
        if style:
            merged.update(style)

    return merged


def get_default_guide_lines(fn_name: str) -> list[dict[str, Any]]:
    """Return default guide lines for an analysis, if defined."""

    return [line.copy() for line in DEFAULT_SERIES_STYLE.get(fn_name, {}).get('guide_lines', [])]


def plot_guide_lines(
    guide_lines: Sequence[dict[str, Any]],
    chart: Chart,
    reference_data: pd.DataFrame | None = None,
) -> None:
    """Plot horizontal guide lines on a chart or subchart."""

    if reference_data is None or reference_data.empty:
        return

    for line in guide_lines:
        line_name = line.get('text') or f"Guide {line['value']}"
        guide_data = pd.DataFrame({
            'date': reference_data['date'],
            line_name: line['value'],
        })

        guide_series = chart.create_line(
            name=line_name,
            color=line.get('color', '#9aa4b2aa'),
            style=line.get('line_style', 'dashed'),
            width=line.get('width', 1),
            price_line=line.get('price_line', False),
            price_label=line.get('axis_label_visible', False),
        )
        guide_series.set(guide_data)


def count_subcharts(analysis_specs: Sequence[dict[str, Any]]) -> int:
    """Count how many prepared analyses should render as subcharts."""

    return sum(1 for spec in analysis_specs if spec['layout'] == 'subchart')


def get_main_chart_height(subchart_count: int) -> float:
    """Return the main chart height fraction for the number of subcharts."""

    return max(0.5, 1 - (0.25 * subchart_count))


def get_subchart_height(subchart_count: int) -> float:
    """Return the height fraction for each subchart."""

    if subchart_count <= 0:
        return 0.3

    return (1 - get_main_chart_height(subchart_count)) / subchart_count


def style_subchart(panel: Chart) -> None:
    """Apply the project's default visual style to a subchart."""

    panel.layout(
        background_color='#0b0e11',
        text_color='#d1d4dc',
        font_size=12,
        font_family='Trebuchet MS',
    )
    panel.grid(vert_enabled=True, horz_enabled=True, color='#2B2B43')
    panel.legend(visible=True)


def format_ohlcv(ohlcv_data: pd.DataFrame) -> pd.DataFrame:
    """Convert project OHLCV format into lightweight-charts format."""

    df = ohlcv_data.copy().reset_index()
    df.columns = [c.lower() for c in df.columns]
    df['date'] = pd.to_datetime(df['date']).astype('datetime64[ns]')
    df = df.dropna(subset=['open', 'high', 'low', 'close'])

    return df[['date', 'open', 'high', 'low', 'close', 'volume']]
