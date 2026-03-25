import os
import time
import pandas as pd
from src.config_loader import load_all_configs
from src.data_getter import fetch_data
import src.paths as paths

# Load asset configuration (grouped by category)
config, headers = load_all_configs(paths.WATCHLIST_DIR)

# Process each asset category separately (eg crypto, equities, macro)
for category, assets in config.items():
    storage_file = os.path.join(paths.DATA_DIR, f'{category}_data.parquet')

    # Load existing data if available, otherwise initialise empty DataFrame
    if os.path.exists(storage_file):
        existing_df = pd.read_parquet(storage_file)
    else:
        os.makedirs(os.path.dirname(storage_file), exist_ok=True)
        existing_df = pd.DataFrame()
    
    # Iterate through each asset in the category
    for identifier, item in assets.items():

        # Optional: throttle API requests if needed
        #if item['Source'] == 'yfinance':
         #   time.sleep(1)

        print(f"\n--- Processing {identifier} ---")
        
        # Determine start date for incremental updates
        # If data already exists, fetch only new (or slightly overlapping) data
        if not existing_df.empty and identifier in existing_df.columns.get_level_values(0):

            asset_df = existing_df[identifier]

            if not asset_df.isna().all().all():
                last_date = asset_df['Close'].last_valid_index()

                if category == 'macro':
                    # For macro data, pull extra data to account for revisions
                    start_date = last_date - pd.Timedelta(days=90)
                else:
                    start_date = last_date
                print(f"updating from {start_date.date()}...")

            else:
                # Column exists but contains no valid data
                start_date = None
                print("No valid data found, fetching full history...")

        else:
            # New asset: fetch entire history
            start_date = None
            print("New asset, fetching full history...")
        
        # Fetch latest data for the asset
        print(f"Fetching {identifier} ({item['Full_Name']}) from {item['Source']}...")
        new_data = fetch_data(item['Ticker'], item['Source'], identifier, start_date=start_date)
        
        if new_data is None or new_data.empty:
            print(f"❌ No data returned for {identifier}")
            continue
        
        print(f"✓ Fetched {len(new_data)} rows: {new_data.index[0].date()} to {new_data.index[-1].date()}")
        
        # Merge new data into existing dataset
        if not existing_df.empty and identifier in existing_df.columns.get_level_values(0):
            # Existing asset: update values and remove duplicate timestamps
            existing_asset = existing_df[identifier]
            new_asset = new_data[identifier]

            combined = pd.concat([existing_asset, new_asset], axis=0)
            combined = combined[~combined.index.duplicated(keep='last')]
            combined = combined.sort_index()
            
            for col in combined.columns:
                existing_df[(identifier, col)] = combined[col]
            print(f"✓ Updated existing column")

        else:
            # New asset: append as a new column
            existing_df = pd.concat([existing_df, new_data], axis=1, sort=True)
            print(f"✓ Added as new column")
    
    # Final cleanup and standardisation before saving
    if not existing_df.empty:
        # Ensure chronological order
        existing_df = existing_df.sort_index()
        
        # Forward-fill missing values with category-specific limits
        if category == 'crypto':
            existing_df = existing_df.ffill(limit=1)
        elif category == 'macro':
            existing_df = existing_df.ffill()
        else:
            existing_df = existing_df.ffill(limit=4)
        
        # Keep only configured assets and enforce alphabetical column order
        existing_df = existing_df.loc[:, existing_df.columns.get_level_values(0).isin(assets.keys())]
        existing_df = existing_df.sort_index(axis=1)
        
        # Standardise index naming
        existing_df.index.name = 'Date'
        
        # Persist cleaned dataset
        existing_df.to_parquet(storage_file)
        print(f"\n✅ Saved {category} data: {existing_df.shape[0]} rows × {existing_df.shape[1]} cols")
        print(f"   Date range: {existing_df.index[0].date()} to {existing_df.index[-1].date()}")
    else:
        print(f"\n⚠️ No data for {category}")