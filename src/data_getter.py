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

    series = None

    try:

        if Source == 'FRED':
            series = fred.get_series(Ticker, observation_start=start_date)
            series.name = Identifier

        elif Source == 'yfinance':

            if start_date:
                df = yf.download(Ticker, start=start_date, progress=False, auto_adjust=False)
            else:
                df = yf.download(Ticker, period='max', progress=False, auto_adjust=False)

            if not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                if 'Close' in df.columns:
                    series = df['Close'].copy()
                    series.name = Identifier
        else:
            print('other')

    except Exception as e:
        print(f"Error fetching data for {Identifier} from {Source}: {e}")

    return series




    

    
