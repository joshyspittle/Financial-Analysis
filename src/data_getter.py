import os
import yfinance as yf
import pandas as pd
from fredapi import Fred
from dotenv import load_dotenv

load_dotenv()

FRED_API = os.getenv('FRED_API_KEY')
fred = Fred(api_key=FRED_API)

def fetch_data(Ticker, Source, Identifier, start_date=None):

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




    

    
