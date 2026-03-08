import csv
import os
import pandas as pd

def load_all_configs(filepath):
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

        file_path = os.path.join(filepath, filename)
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

    return config, headers


