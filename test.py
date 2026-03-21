import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd

df = pd.read_csv("watchlist/crypto.csv")

config={}
category_name = 'crypto'

headers = df.columns.tolist()

indexed_df = df.set_index('Identifier')

category_config = indexed_df.to_dict('index')

config[category_name] = category_config

print(config['crypto']['BTC'])
print(config)
print(headers)