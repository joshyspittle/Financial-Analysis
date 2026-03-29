"""Incremental data update script.

Workflow:
- Load watchlists by category.
- Read the existing parquet file for each category if present.
- Fetch either full history or incremental updates per asset.
- Merge updates, apply category-specific forward fill rules, and save.

Assumptions:
- Stored category files use a two-level column MultiIndex: ``(Asset, Field)``.
- Macro series use ``Close`` as their single field and are refreshed with a
  90-day overlap to catch revisions.
- ``load_data`` cache entries are cleared after saving to avoid stale reads in
  the same Python session.
"""

import os

import pandas as pd

import src.paths as paths
from src.config_loader import load_all_configs
from src.data_getter import clear_cache, fetch_data

config, headers = load_all_configs(paths.WATCHLIST_DIR)

for category, assets in config.items():
    storage_file = os.path.join(paths.DATA_DIR, f'{category}_data.parquet')

    if os.path.exists(storage_file):
        existing_df = pd.read_parquet(storage_file)
    else:
        os.makedirs(os.path.dirname(storage_file), exist_ok=True)
        existing_df = pd.DataFrame()

    for identifier, item in assets.items():
        print(f"\n--- Processing {identifier} ---")

        if not existing_df.empty and identifier in existing_df.columns.get_level_values(0):
            asset_df = existing_df[identifier]

            if not asset_df.isna().all().all():
                last_date = asset_df['Close'].last_valid_index()

                if category == 'macro':
                    start_date = last_date - pd.Timedelta(days=90)
                else:
                    start_date = last_date

                print(f"updating from {start_date.date()}...")
            else:
                start_date = None
                print("No valid data found, fetching full history...")

        else:
            start_date = None
            print("New asset, fetching full history...")

        print(f"Fetching {identifier} ({item['Full_Name']}) from {item['Source']}...")
        new_data = fetch_data(item['Ticker'], item['Source'], identifier, start_date=start_date)

        if new_data is None or new_data.empty:
            print(f"âŒ No data returned for {identifier}")
            continue

        print(f"âœ“ Fetched {len(new_data)} rows: {new_data.index[0].date()} to {new_data.index[-1].date()}")

        if not existing_df.empty and identifier in existing_df.columns.get_level_values(0):
            existing_asset = existing_df[identifier]
            new_asset = new_data[identifier]

            combined = pd.concat([existing_asset, new_asset], axis=0)
            combined = combined[~combined.index.duplicated(keep='last')]
            combined = combined.sort_index()

            combined.columns = pd.MultiIndex.from_product([[identifier], combined.columns])
            existing_without_asset = existing_df.drop(columns=identifier, level=0)
            existing_df = pd.concat([existing_without_asset, combined], axis=1, sort=True)
            print(f"âœ“ Updated existing column")

        else:
            existing_df = pd.concat([existing_df, new_data], axis=1, sort=True)
            print(f"âœ“ Added as new column")

    if not existing_df.empty:
        existing_df = existing_df.sort_index()

        if category == 'crypto':
            existing_df = existing_df.ffill(limit=1)
        elif category == 'macro':
            existing_df = existing_df.ffill()
        else:
            existing_df = existing_df.ffill(limit=4)

        existing_df = existing_df.loc[:, existing_df.columns.get_level_values(0).isin(assets.keys())]
        existing_df = existing_df.sort_index(axis=1)
        existing_df.index.name = 'Date'

        existing_df.to_parquet(storage_file)
        clear_cache(storage_file)
        print(f"\nâœ… Saved {category} data: {existing_df.shape[0]} rows Ã— {existing_df.shape[1]} cols")
        print(f"   Date range: {existing_df.index[0].date()} to {existing_df.index[-1].date()}")
    else:
        print(f"\nâš ï¸ No data for {category}")
