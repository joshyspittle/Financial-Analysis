import os
import time
import pandas as pd
from src.config_loader import load_all_configs
from src.data_getter import fetch_data

WATCHLIST_FOLDER = 'watchlist'
DATA_FOLDER = 'data'

config, headers = load_all_configs(WATCHLIST_FOLDER)

for category, assets in config.items():
    storage_file = os.path.join(DATA_FOLDER, f'{category}_data.csv')

    if os.path.exists(storage_file):
        existing_df = pd.read_csv(storage_file, index_col=0, parse_dates=True)
    else:
        os.makedirs(os.path.dirname(storage_file), exist_ok=True)
        existing_df = pd.DataFrame()
    
    # Process each asset individually
    for identifier, item in assets.items():

        #if item['Source'] == 'yfinance':
         #   time.sleep(1)

        print(f"\n--- Processing {identifier} ---")
        
        # Determine start date for THIS specific asset
        if identifier in existing_df.columns and not existing_df[identifier].isna().all():
            last_date = existing_df[identifier].last_valid_index()
            
            if last_date is not None:
                if category == 'macro':
                    start_date = last_date - pd.Timedelta(days=90)
                else:
                    start_date = last_date
                print(f"Updating from {start_date.date()}...")
            else:
                start_date = None
                print(f"No valid data found, fetching full history...")
        else:
            start_date = None
            print(f"New asset, fetching full history...")
        
        # Fetch data for this asset
        print(f"Fetching {identifier} ({item['Full_Name']}) from {item['Source']}...")
        new_data = fetch_data(item['Ticker'], item['Source'], identifier, start_date=start_date)
        
        if new_data is None or new_data.empty:
            print(f"❌ No data returned for {identifier}")
            continue
        
        print(f"✓ Fetched {len(new_data)} rows: {new_data.index[0].date()} to {new_data.index[-1].date()}")
        
        # Add/update THIS asset in the existing dataframe
        if identifier in existing_df.columns:
            # Update existing asset: combine old and new data
            combined = pd.concat([existing_df[identifier], new_data], axis=0)
            combined = combined[~combined.index.duplicated(keep='last')]
            combined = combined.sort_index()
            existing_df[identifier] = combined
            print(f"✓ Updated existing column")
        else:
            # New asset: add as new column
            existing_df = pd.concat([existing_df, new_data], axis=1, sort=True)
            print(f"✓ Added as new column")
    
    # After processing all assets, clean up the dataframe
    if not existing_df.empty:
        # Sort index
        existing_df = existing_df.sort_index()
        
        # Apply forward fill with appropriate limits
        if category == 'crypto':
            existing_df = existing_df.ffill(limit=1)
        else:
            existing_df = existing_df.ffill(limit=4)
        
        # Keep only valid columns and SORT ALPHABETICALLY
        valid_columns = list(assets.keys())
        existing_columns = [col for col in valid_columns if col in existing_df.columns]
        existing_columns.sort()  # Sort alphabetically
        existing_df = existing_df[existing_columns]
        
        # Set index name to "Date"
        existing_df.index.name = 'Date'
        
        # Save
        existing_df.to_csv(storage_file)
        print(f"\n✅ Saved {category} data: {existing_df.shape[0]} rows × {existing_df.shape[1]} cols")
        print(f"   Date range: {existing_df.index[0].date()} to {existing_df.index[-1].date()}")
        print(f"   Columns (alphabetical): {', '.join(existing_columns)}")
    else:
        print(f"\n⚠️ No data for {category}")