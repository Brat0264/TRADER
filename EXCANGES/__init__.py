from  EXCANGES.myInstruments import \
    (Instrument,
     Account,
     Candle,
     Trade,
     OrderBook,
     Price,
     MarketData,
    )

figi_AAPL = 'BBG000B9XRY4'
figi_SBER = 'BBG004730N88'
figi_USD  = 'USD000UTSTOM'

#from EXCANGES.BinanceOLD  import Binance
#from EXCANGES.TinkoffOLD  import Tinkoff

from EXCANGES.Exchange import Exchange, Tinkoff, Binance


def info(cls):
    for k,v in (cls.__dict__).items(): print(f'{k.ljust(12)}: {v}')

