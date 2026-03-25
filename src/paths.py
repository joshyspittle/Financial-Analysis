from pathlib import Path

# 1. Get the Project Root (Assuming paths.py is in src/)
# .parent takes us to 'src/', .parent.parent takes us to the root folder
PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# 2. Define Main Folders
DATA_DIR = PROJECT_ROOT / "data"
WATCHLIST_DIR = PROJECT_ROOT / "watchlist"
#LOGS_DIR = PROJECT_ROOT / "logs"

# 3. Define Specific File Paths
CRYPTO_WATCHLIST_CSV = WATCHLIST_DIR / "crypto.csv"
MACRO_WATCHLIST_CSV = WATCHLIST_DIR / "macro.csv"
FOREX_WATCHLIST_CSV = WATCHLIST_DIR / "forex.csv"
COMMODITIES_WATCHLIST_CSV = WATCHLIST_DIR / "commodities.csv"
EQUITIES_WATCHLIST_CSV = WATCHLIST_DIR / "equities.csv"
INDICES_WATCHLIST_CSV = WATCHLIST_DIR / "indices.csv"

CRYPTO_DATA_PARQUET = DATA_DIR / "crypto_data.parquet"
MACRO_DATA_PARQUET = DATA_DIR / "macro_data.parquet"
FOREX_DATA_PARQUET = DATA_DIR / "forex_data.parquet"
COMMODITIES_DATA_PARQUET = DATA_DIR / "commodities_data.parquet"
EQUITIES_DATA_PARQUET = DATA_DIR / "equities_data.parquet"
INDICES_DATA_PARQUET = DATA_DIR / "indices_data.parquet"
#CRYPTO_DATA_CSV = DATA_DIR / "crypto_data.csv"
#MACRO_DATA_CSV = DATA_DIR / "macro_data.csv"
#FOREX_DATA_CSV = DATA_DIR / "forex_data.csv"
#COMMODITIES_DATA_CSV = DATA_DIR / "commodities_data.csv"
#EQUITIES_DATA_CSV = DATA_DIR / "equities_data.csv"
#INDICES_DATA_CSV = DATA_DIR / "indices_data.csv"

# 4. Auto-create folders if they don't exist
for folder in [DATA_DIR, WATCHLIST_DIR]: #, LOGS_DIR]:
    folder.mkdir(parents=True, exist_ok=True)