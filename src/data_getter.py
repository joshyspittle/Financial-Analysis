import os
import yfinance as yf
import pandas as pd
from fredapi import Fred
from dotenv import load_dotenv

load_dotenv()

FRED_API = os.getenv('FRED_API_KEY')
fred = Fred(api_key=FRED_API)

def fetch_data(Ticker, Source, Identifier, start_date=None):
    """
    Fetch time series data from supported data sources.

    This function retrieves historical data for a given ticker using the
    specified data source. The returned data is standardised as a pandas
    Series indexed by date.

    Supported sources:
    - 'FRED'     : Uses the FRED API via fredapi
    - 'yfinance' : Uses Yahoo Finance via yfinance (returns 'Close' prices)

    Parameters
    ----------
    Ticker : str
        Ticker or series ID used by the data source.
    Source : str
        Data source identifier ('FRED' or 'yfinance').
    Identifier : str
        Name assigned to the returned series (used as the Series.name).
    start_date : str, optional
        Start date for the time series (format: 'YYYY-MM-DD').
        If None, the full available history is fetched.

    Returns
    -------
    series : pandas.Series or None
        Time series of the requested data indexed by date.
        Returns None if the data could not be fetched or is empty.

    Notes
    -----
    - For yfinance data, only the 'Close' price is returned.
    - MultiIndex columns from yfinance outputs are flattened automatically.
    - Errors are caught and logged; the function fails silently by returning None.
    """

    data = None

    try:

        if Source == 'FRED':
            series = fred.get_series(Ticker, observation_start=start_date)
            df = series.to_frame(name='Close')
            df.columns = pd.MultiIndex.from_product([[Identifier], df.columns])
            data = df

        elif Source == 'yfinance':

            if start_date:
                df = yf.download(Ticker, start=start_date, progress=False, auto_adjust=False)
            else:
                df = yf.download(Ticker, period='max', progress=False, auto_adjust=False)

            if not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                
                df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
                df.columns = pd.MultiIndex.from_product([[Identifier], df.columns])
                data = df
        else:
            print(f"Unsupported source: {Source}")

    except Exception as e:
        print(f"Error fetching data for {Identifier} from {Source}: {e}")

    return data

_cache = {}

def load_data(path, time_period, start_date=None, end_date=None):
    """
    Load time series data from a CSV file with in-memory caching.

    The function reads a CSV file into a pandas DataFrame indexed by dates.
    The full dataset is cached on first load to avoid repeated disk I/O on
    subsequent calls. Optionally, a date range can be specified to return
    a filtered subset of the data.

    Parameters
    ----------
    path : str
        File path to the CSV data file.
    start_date : str or pandas.Timestamp, optional
        Start date for slicing the data (inclusive). If None, data is
        returned from the beginning.
    end_date : str or pandas.Timestamp, optional
        End date for slicing the data (inclusive). If None, data is
        returned up to the latest available date.

    Returns
    -------
    pandas.DataFrame
        DataFrame containing the requested date range of the dataset,
        indexed by datetime.

    Notes
    -----
    - The full dataset is cached in memory after the first load.
    - Date filtering is applied after loading the cached data.
    - The CSV file is expected to have a datetime index in the first column.
    """
        
    if path not in _cache:
        _cache[path] = pd.read_parquet(path)

    df = _cache[path]

    return df.loc[start_date:end_date]


    

    
