#import src.config_loader as config_loader
import src.features as features
#import src.models as models
#import src.metrics as metrics
#import src.visualisation as visualisation
import src.paths as paths
from src.data_getter import load_data
import src.visualisation as vis

crypto_ohlcv = load_data(paths.CRYPTO_DATA_PARQUET, '1d')
crypto_close = crypto_ohlcv.xs('Close', axis=1, level=1)
#print(crypto_data['AAVE']['Close'])
#print(close_data)
print(features.simple_moving_average(crypto_close, 'BTC', window=30))
print(features.exponential_moving_average(crypto_close, 'BTC', span=30))

crypto_ohlc_window = load_data(paths.CRYPTO_DATA_PARQUET, '1d', start_date='01-01-2024')
crypto_close_window = crypto_ohlc_window.xs('Close', axis=1, level=1)
print(features.simple_moving_average(crypto_close_window, 'BTC', window=30))
print(features.exponential_moving_average(crypto_close_window, 'BTC', span=30))

print(crypto_ohlcv['BTC'])

if __name__ == '__main__':
    vis.price_chart(crypto_ohlcv['BTC'], 'BTC')