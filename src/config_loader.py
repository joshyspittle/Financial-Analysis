"""Watchlist loading utilities.

This module reads the CSV watchlists in ``watchlist/`` and returns a nested
dictionary keyed first by category, then by asset identifier.

Conventions:
- ``Identifier`` must be present in each CSV.
- Identifiers are stripped of surrounding whitespace before validation.
- Duplicate identifiers within a file are rejected.
- All watchlists are assumed to share the same column layout.
"""

from pathlib import Path
from typing import TypeAlias

import pandas as pd

ConfigRow: TypeAlias = dict[str, str]
CategoryConfig: TypeAlias = dict[str, ConfigRow]
WatchlistConfig: TypeAlias = dict[str, CategoryConfig]


def load_all_configs(watchlist_dir: str | Path) -> tuple[WatchlistConfig, list[str]]:
    """Load all configured watchlists from disk."""

    data_files = [
        'commodities.csv',
        'crypto.csv',
        'macro.csv',
        'equities.csv',
        'forex.csv',
        'indices.csv',
    ]

    config: WatchlistConfig = {}
    headers: list[str] = []

    for filename in data_files:
        file_path = Path(watchlist_dir) / filename
        category_name = filename.replace('.csv', '')

        try:
            df = pd.read_csv(file_path, skipinitialspace=True)
            headers = df.columns.tolist()

            if 'Identifier' not in df.columns:
                raise KeyError

            df['Identifier'] = df['Identifier'].astype(str).str.strip()

            duplicate_identifiers = df.loc[df['Identifier'].duplicated(), 'Identifier'].unique()
            if len(duplicate_identifiers) > 0:
                duplicates = ', '.join(sorted(duplicate_identifiers))
                raise ValueError(f"Duplicate Identifier values in {filename}: {duplicates}")

            indexed_df = df.set_index('Identifier')
            category_config = indexed_df.to_dict('index')
            config[category_name] = category_config

            print(f"Loaded and processed: {category_name} ({len(category_config)} items)")

        except FileNotFoundError:
            print(f"ERROR: File not found at {file_path}. Skipping.")

        except pd.errors.EmptyDataError:
            print(f"WARNING: {filename} is empty. Skipping.")

        except KeyError:
            print(f"ERROR: Missing 'Identifier' column in {filename}. Check file headers.")

        except ValueError as e:
            print(f"ERROR: {e}")

    return config, headers
