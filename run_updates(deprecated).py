import os
import pandas as pd
from src.config_loader import load_all_configs
from src.data_getter import fetch_data

WATCHLIST_FOLDER = 'watchlist'
MACRO_STORAGE_FILE = 'data/macro_data.csv'

config, headers = load_all_configs(WATCHLIST_FOLDER)

if os.path.exists(MACRO_STORAGE_FILE):
    existing_df = pd.read_csv(MACRO_STORAGE_FILE, index_col=0, parse_dates=True)
    start_date = existing_df.index[-1]
    print(f"Updating data from {start_date}...")
else:
    os.makedirs(os.path.dirname(MACRO_STORAGE_FILE), exist_ok=True)
    existing_df = pd.DataFrame()
    start_date = None

print(config['macro']['VIX']['Source'])
print(config, headers)

series_list = []

for identifier, item in config['macro'].items():
    print(item['Full_Name'])
    data = fetch_data(item['Ticker'], item['Source'], identifier, start_date=start_date)
    print(data)
    print('\n')

    if data is not None:
        series_list.append(data)

new_data_df = pd.concat(series_list, axis=1, sort=True)
final_df = pd.concat([existing_df, new_data_df], axis=0, sort=True)
final_df = final_df[~final_df.index.duplicated(keep='last')]

final_df = final_df.sort_index().ffill()
#final_df = final_df.dropna(subset=['VIX'])
valid_columns = list(config['macro'].keys())
final_df = final_df[[col for col in final_df.columns if col in valid_columns]]
final_df.to_csv(MACRO_STORAGE_FILE)

print(final_df['US10Y'].tail())

    
