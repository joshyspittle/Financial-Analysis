import csv
import pandas as pd
import numpy as np
import matplotlib as plt
import os
from fredapi import Fred

WATCHLIST_FOLDER = 'watchlist'
FRED_API = 'e3ec277e29815fad9585404576f4d4d9'

data_files = [
    'commodities.csv',
    'crypto.csv',
    'macro.csv',
    'equities.csv',
    'forex.csv',
    'indices.csv'
    ]

config = {}
for filename in data_files:

    file_path = os.path.join(WATCHLIST_FOLDER, filename)
    category_name = filename.replace('.csv', '')

    try:

        df = pd.read_csv(file_path, skipinitialspace=True)

        headers = df.columns.tolist()

        indexed_df = df.set_index('Identifier')

        category_config = indexed_df.to_dict('index')

        config[category_name] = category_config

        print(f"✅ Loaded and processed: {category_name} ({len(category_config)} items)")
                
    except FileNotFoundError:
        print(f"❌ ERROR: File not found at {file_path}. Skipping.")
        
    except pd.errors.EmptyDataError:
        print(f"⚠️ WARNING: {filename} is empty. Skipping.")
        
    except KeyError:
        print(f"❌ ERROR: Missing 'Identifier' column in {filename}. Check file headers.")
    
print(config['macro']['VIX']['Source'])
print(headers)


