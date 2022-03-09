from dataclasses import dataclass
from decimal import Decimal

from typing import Any, Optional, List, Dict, Union
from datetime import datetime, timedelta, timezone
import threading
from operator import itemgetter, attrgetter, methodcaller

import numpy
from tinkoff.invest import (
    CandleInstrument,
    CandleInterval,
    SubscriptionInterval,
    Instrument as tiInstrument,
    CurrenciesResponse,
    BondsResponse,
    SharesResponse,
    EtfsResponse,
    FuturesResponse,
    PortfolioResponse,
    PortfolioPosition,
    PositionsResponse,
    TradingSchedule,
    TradeInstrument,
    InstrumentStatus,
    InstrumentIdType,
    Trade as tiTrade,
    Candle as tiCandle 
    )
import time

def cast_money(v):
    """
    https://tinkoff.github.io/investAPI/faq_custom_types/
    :param v:
    :return:
    """
    return v.units + v.nano * 1e-9 # nano - 9 нулей

class Updateable(object):
    def update(self, new: dict):
        for key, value in new.items():
            #print(f'update {key}')
            if hasattr(self, key):
                setattr(self, key, value)


class TradeDirection:
    HOLD = 0
    BUY = 1
    SELL = 2

@dataclass
class Base:
    delay = 0.0
    sum_delay = 0
    n     = 0
    mean_delay: float = 0.0              # средняя задердка потока цен  - с
    # Определение средней задержки получения с Биржи данных о Trade по n_per
    def call_delay(self, time:datetime, n_per:int = 10, typ:str='****'):

        try:
            self.delay = (time - self.time)
        except:
            input(f'Разные UTC:\n{timezone()}')
            exit(-1)
        try:
            self.sum_delay += self.delay.total_seconds()
            self.n = self.n + 1 if self.n < 2147483647 else 0

            self.mean_delay = (1.0 / self.n) * self.sum_delay

            if self.n % n_per == 0 :
               self.mean_delay = (1.0/self.n) * self.sum_delay
               self.sum_delay = 0
        except:
            print(f'call_delay({time}) self.delay={self.delay}')


params: dict={}
@dataclass
class Instrument(Updateable):  # pylint:disable=too-many-instance-attributes

    dict: Dict= None

    figi: str = ''
    ticker: str = ''
    class_code: str = ''
    isin: str = ''
    lot: int = 0
    currency: str = ''
    klong: Decimal = 0.0
    kshort: Decimal = 0.0
    dlong: Decimal = 0.0
    dshort: Decimal = 0.0
    dlong_min: Decimal = 0.0
    dshort_min: Decimal = 0.0
    short_enabled_flag: bool = False
    name: str = ''
    exchange: str = ''
    country_of_risk: str = ''
    country_of_risk_name: str = ''
    instrument_type: str = ''
    trading_status: int = 0  # "SecurityTradingStatus"
    otc_flag: bool = False
    buy_available_flag: bool = False
    sell_available_flag: bool = False
    min_price_increment: Decimal = 0.0
    api_trade_available_flag: bool = False

    def __post_init__(self):

        #print(f'{type(self.dict)}->{self.dict}')

        if isinstance(self.dict, tiInstrument):
            self.update(new=self.dict.__dict__)
            self.ticker = self.dict.__dict__['name']
            #print(f'____________{self.dict.__dict__}')

        elif isinstance(self.dict, Dict):
            self.update(new=self.binance(self.dict))
            return
        else:
            print('Instrument(<НЕИЗВЕСТНЫЙ ТИП>)')
            exit(-1)

        #print(f'{self.__class__.__name__}.__post_init()__: {params}\n')

    def binance(self, symbol:dict)-> Dict:
        s = symbol
        PRICE_FILTER  = s["filters"][0]
        PERCENT_PRICE = s["filters"][1]
        LOT_SIZE      = s['filters'][2]
        msg = {
            'figi'           : s['symbol'],
            'name'           : s['symbol'],
            'ticker'         : s['symbol'],
            'lot'            : LOT_SIZE['minQty'],
            'exchange'       : 'Binance',
            'instrument_type': s['permissions'][0],
            'currency'       : s['quoteAsset'],
            # 'min_price_increment': s[''],
        }
        #print(msg)
        return msg

    def info(self):
        msg = f'figi:{self.figi} ticker:{self.ticker} lot:{self.lot} currency:{self.currency}' \
              f' exchange:{self.exchange} name:{self.name}'
        return msg

@dataclass
class Candle(Base):
    figi: str = ''
    interval: SubscriptionInterval = SubscriptionInterval.SUBSCRIPTION_INTERVAL_ONE_MINUTE
    open: float  = 0.0
    high: float  = 0.0
    low:  float  = 0.0
    close: float = 0.0
    volume: int  = 0
    time: datetime = datetime.utcnow()

    def __init__(self, candle: tiCandle = None):

        if candle != None: self.update(candle=candle)

    async def call_delay(self, time:datetime, n_per:int = 10):

        self.delay += 0.000001*(time.microsecond - self.time.microsecond)
        if self.time.second != time.second:
            self.delay += (time.second - self.time.second)

        self.n = self.n + 1

        if self.n % n_per != 1000 :
           self.mean_delay = (1.0/self.n)*self.delay
           print(f'Candle {time}-->{self.time} DELAY:{self.mean_delay:.3f} c')

    async def update(self, candle:tiCandle = None):

        if candle == None:  return

        self.figi   = candle.figi
        self.open   = candle.open.units  + 1e-09*candle.open.nano
        self.high   = candle.high.units  + 1e-09*candle.high.nano
        self.low    = candle.low.units   + 1e-09*candle.low.nano
        self.close  = candle.close.units + 1e-09*candle.close.nano
        self.volume = candle.volume
        self.time   = candle.time

        # вычисление средней за N периодов задержки потока сделок
        await self.call_delay(time = datetime.now(timezone.utc), n_per = 10)

'''NEWS'''
@dataclass
class Trade(Base):
    iD: int = 0
    instrument: Instrument = None
    figi: str = ""
    ticker: str=""
    direction: TradeDirection = TradeDirection.HOLD
    price:    float = 0.0
    quantity: float = 0.0
    time: datetime = datetime.now()

    def __init__(self, instrument:Instrument= None, trade:Union[tiTrade, Dict] = None):

        self.instrument = instrument
        if trade != None: self.update(trade=trade)


    def info(self):
        t = self.time.strftime("%d-%m-%y %H:%M:%S%f")
        if len(self.instrument.figi) !=0 :
           msg = f'figi={self.instrument.figi}'
        else:  msg = f'ticker={self.instrument.ticker}'
        return f'{msg} iD:{self.iD} {t}' \
               f'  ${self.price:.2f} [{self.quantity:.6f}] {self.delay:.3f} c'

    def update(self, trade:Union[tiTrade, Dict] = None):
        #print(trade)

        if trade == None:  return
        #print(f'\ntrade={trade}')
        if not isinstance(trade, tiTrade):
           if isinstance(trade, Dict):
              if 's' in trade.keys():
                #print(trade)
                self.figi  = trade['s']
                self.ticker=  trade['s']
                self.price = float(trade['p'])
                self.quantity = float(trade['q'])
                self.iD    = int(trade['t'])
                # Время - UTC !!!
                self.time  = datetime.fromtimestamp(0.001*trade['T'], tz=timezone.utc)
                self.call_delay(time=datetime.now(timezone.utc), n_per=10, typ='sync')
                return
              else:
                    try:
                       time_trade = trade['event_time']
                       #print(trade['event_type'])
                       self.figi     = '' #trade['s']
                       self.ticker   = trade['symbol']
                       self.price    = float(trade['price'])
                       self.quantity = float(trade['quantity'])
                       self.iD       = int(trade['trade_id'])
                       # Время - UTC !!!

                       self.time = datetime.fromtimestamp(0.001 * float(time_trade),tz=timezone.utc)

                       _time = datetime.now(timezone.utc)
                       self.delay = (_time-self.time).total_seconds()
                       #self.call_delay(time=_time, n_per=10, typ='sync')
                       #print(f'                trade:{self.time}'
                       #      f'\n                _time:{_time} --> {self.delay}')
                       return
                    except :
                       print(f'Error: {trade}')

        elif isinstance(trade, tiTrade):
            self.figi      = trade.figi
            self.ticker    = 'SBER'
            self.direction = trade.direction
            self.price     = trade.price.units + 1e-09*trade.price.nano
            self.quantity  = trade.quantity
            self.time      = trade.time

            self.call_delay(time=datetime.now(timezone.utc), n_per=10, typ='sync')
            # вычисление средней за N периодов задержки потока сделок


    async def async_update(self, trade:tiTrade = None):

        if trade == None:  return

        if not isinstance(trade, tiTrade)  and isinstance(trade, Dict):
            self.figi  = trade['s']
            self.price = float(trade['p'])
            self.float = float(trade['q'])
            self.time  = datetime.fromtimestamp(0.001*trade['T'])

        elif isinstance(trade, tiTrade):
            self.figi      = trade.figi
            self.direction = trade.direction
            self.price     = trade.price.units + 1e-09*trade.price.nano
            self.quantity  = trade.quantity
            self.time      = trade.time

        #print(f'\nTIME={self.time}')

        # вычисление средней за N периодов задержки потока сделок
        self.call_delay(time = datetime.now(timezone.utc), n_per = 10, typ='async')

@dataclass
class Price(Base):

    price : float = 0.0
    volume: float = 0.0

    def __init__(self, price, volume ):
        self.price  = float(price)
        self.volume = float(volume)

    def from_binance(self, ):
        pass


@dataclass
class OrderBook(Updateable):
    figi: str
    ticker: str
    time: datetime
    bids: List[Price]
    asks: List[Price]

    def __init__(self, ticker: str = None, order_book: dict = None, time: datetime=None):
        self.bids = []
        self.asks = []
        self.ticker = ticker
        self.time = time

        if   order_book == None: self.ID   = 0
        else :
            self.ID   = order_book['lastUpdateId']
            for bid in order_book['bids']:  self.bids.append(Price(price=bid[0],volume=bid[1]))
            for ask in order_book['asks']:  self.asks.append(Price(price=ask[0],volume=ask[1]))
        #print(f'{self.bids[0]}\n{self.asks[0]}')
        #asks = order_book['asks']

    def info(self):
        msg = f'order_book: {self.time} {self.ID}' \
              f'  bestBid=${self.bids[0].price}' \
              f'  bestAsk=${self.asks[0].price}'
        return msg


@dataclass
class Account:
    opened_date: datetime = None
    closed_date: datetime = None
    name: str = ""
    id: str = ""
    portfolio:List[Instrument] = None
    currency: str = "RUB"
    balance: float = 0.0
    casch:   float = 0.0

    def update(self, portfolio:PositionsResponse= None):

        '''
        account: PortfolioResponse(total_amount_shares=MoneyValue(currency='rub', units=0, nano=0),
                                   total_amount_bonds=MoneyValue(currency='rub', units=0, nano=0),
                                   total_amount_etf=MoneyValue(currency='rub', units=0, nano=0),
                                   total_amount_currencies=MoneyValue(currency='rub', units=1003, nano=0),
                                   total_amount_futures=MoneyValue(currency='rub', units=0, nano=0),
                                   expected_yield=Quotation(units=0, nano=140000000), positions=[])
        '''
        if portfolio != None:
            self.casch = portfolio.total_amount_currencies.units+1e-09*portfolio.total_amount_currencies.nano
            self.balance = self.casch
            self.balance += portfolio.total_amount_shares.units+1e-09*portfolio.total_amount_shares.nano
            self.balance += portfolio.total_amount_futures.units + 1e-09 * portfolio.total_amount_futures.nano
            self.balance += portfolio.total_amount_bonds.units + 1e-09 * portfolio.total_amount_bonds.nano
            self.balance += portfolio.total_amount_etf.units + 1e-09 * portfolio.total_amount_etf.nano
            self.currency = portfolio.total_amount_currencies.currency.upper()
            #print(f'portfolio: {portfolio.total_amount_currencies} {self.currency}')

@dataclass
class MarketData:
    exchange: str
    figi:     str
    bids:    List[Price]
    asks:    List[Price]
    trades:  List[Price]
    candles: List[Price]

    def __init__(self):
        pass

    def __call__(self, instrument:Instrument, *args, **kwargs):
        self.figi = instrument.figi








