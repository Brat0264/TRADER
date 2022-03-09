from datetime import datetime
from abc import ABCMeta, abstractmethod
from typing import List, Dict

from EXCANGES.RepeatTimer import RepeatedTimer
from dataclasses import dataclass
import threading

from EXCANGES import *

from random import randint

class Exchange(metaclass=ABCMeta):

    on_changed  : object    # callback of tick
    on_trade    : object    # callback of update trade
    on_orderbook: object    # callback of update orderbook

    timer: RepeatedTimer
    timezone: str = "UTC"                 # используемая временная зона
    name_instrument    : str              # имя выбранного инструмента
    currencies         : List[str]        # список имен доступных инструментов
    instruments        : List[Instrument] # список доступных инструментов      <Instrument>
    selected_instrument: Instrument       # выбранный инструмент

    trade              : Trade            # последняя сделка
    candle             : Candle           # последняя свеча
    orderbook          : OrderBook        # последний снимок кноги заказов
    marketdata         : MarketData       # словарь словарей списков {trades,candlrs, orderbooks} по инструментам

    stop_trade = threading.Event()        # событие остановки потока данных с биржи
    lock: threading.Lock                  # блокироровщик достура к данным экземрляра биржи

    server_time        : datetime

    #self.is_run_terminal = True
    #self.stop_trade = threading.Event()
    time: int = 0

    '----- Устанавливаются из Конфигурации Биржи ----------------'
    accounts              : List[Account]# Торговыe Счетa на Бирже
    account               : Account      # Торговый Счет на Бирже

    '----- Устанавливаются после Подключения к Бирже ------------'
    server_time: datetime  # Время  Сервера Биржи
    security_price        : float = 0.0  # Последняя Цена
    security_change_day   : float = 0.0  # Изменение за День
    security_change_week  : float = 0.0  # Изменение за Неделю
    security_change_month : float = 0.0  # Изменение за Месяц
    security_change_yahr  : float = 0.0  # Изменение за Год
    security_best_ask     : float = 0.0  # лулуший Bid
    security_best_bid     : float = 0.0  # Изменение за Год
    is_run_terminal       : bool = False # флаг Подклечения к Бирже
    is_connect            : bool = False # флаг Подклечения к Бирже

    def __init__(self, **kwargs):

        self.accounts =[]
        self.account = Account()
        self.accounts.append(self.account)
        self.is_real             = kwargs.get('is_real')

        self.name                = kwargs.get('name')
        self.selected_instrument = kwargs.get('ticker')
        self.currencies          = kwargs.get('tickers')


        self.balance  = 0
        self.server_time = datetime.utcnow()

        self.trade = Trade()
        self.orderbook = OrderBook()


        # https://www.internet-technologies.ru/articles/threading-upravlenie-parallelnymi-potokami.html
        # флаг блокировки
        self.lock = threading.Lock()

        #self.name_instrument = ''
        self.instruments     = []


        self.on_orderbook = lambda ob : print(self.orderbook.info())
        self.on_trade     = lambda ot : print(self.trade.info())

        print(f'{(self.__class__.__name__).ljust(15)}. Init()-->{self.info()}')

    def info(self):
        msg = f'БИРЖА: {self.name} ticker={self.selected_instrument} [{self.currencies}]'
        return msg

    def __call__(self, view= None):
        pass

    @abstractmethod
    def Connect(self):
        pass

    @abstractmethod
    def DisConnect(self):
        pass

    @abstractmethod
    def servertime(self):
        pass

    #------ по Tinkoff API 2.0 gRPC ---------------------------
    '''
    @abstractmethod
    def get_accounts(self):
        pass

    @abstractmethod
    def close_accounts(self):
        pass

    @abstractmethod
    def get_instruments(self):
        pass

    @abstractmethod
    def get_instrument(self, instrument:Instrument ):
        pass

    @abstractmethod
    def post_sandbox_order(
            self,
            *,
            figi: str = "",
            quantity: int = 0,
            price: float = None,
            direction: OrderDirection = OrderDirection(0),
            account_id: str = "",
            order_type: OrderType = OrderType(0),
            order_id: str = "",
    ) -> PostOrderResponse:
        pass

    @abstractmethod
    def get_orders(self, *, account_id: str = "") -> GetOrdersResponse:
        pass

    @abstractmethod
    def cancel_order(
            self, *, account_id: str = "", order_id: str = ""
    ) -> CancelOrderResponse:
        pass

    @abstractmethod
    def get_order_state(
            self, *, account_id: str = "", order_id: str = ""
    ) -> OrderState:
        pass

    @abstractmethod
    def get_positions(self, *, account_id: str = "") -> PositionsResponse:
        pass

    @abstractmethod
    def get_operations(
            self,
            *,
            account_id: str = "",
            from_: Optional[datetime] = None,
            to: Optional[datetime] = None,
            state: OperationState = OperationState(0),
            figi: str = "",
    ) -> OperationsResponse:
        pass

    @abstractmethod
    def get_portfolio(self, *, account_id: str = "") -> PortfolioResponse:
        pass

    @abstractmethod
    def pay_in(self, *, account_id: str = "", amount: Optional[MoneyValue] = None
                       ) -> SandboxPayInResponse:
        pass
    '''

    def tick(self):
        self.server_time = datetime.utcnow()

        self.account.balance       = 10.0 * (950+ randint(1, 100) )
        self.account.casch         = 5.0  * (950+ randint(1, 100) )
        self.security_price        = 0.15 * (950+ randint(1, 100) )
        self.security_change_day   = 0.05 * (950+ randint(1, 100) )
        self.security_change_week  = 0.06 * (950+ randint(1, 100) )
        self.security_change_month = 0.07 * (950+ randint(1, 100) )
        self.security_change_yahr  = 0.04 * (950+ randint(1, 100) )
        self.security_best_bid     = 0.03 * (950+ randint(1, 100) )
        self.security_best_ask     = 0.02 * (950+ randint(1, 100) )

        self.on_changed(self)
        print('',end = f'\r{self.__class__.__name__}: time = {self.time}')
        self.time += 1

class Tinkoff(Exchange):

    def __init__(self, **kwargs):
        params = {'name': 'Tinkoff', 'account': 'BI_76', 'is_real': False,
                  'ticker': figi_USD,
                  'tickers': [figi_USD, figi_SBER, figi_AAPL]}

        super(Tinkoff, self).__init__(**params)

    def servertime(self):
        self.server_time = datetime.utcnow()
        return self.server_time


    def Connect(self):
        print(f'Connect ...')
        self.stop_trade.clear()
        self.timer = RepeatedTimer(interval=0.5, function=self.tick)

        self.is_run_terminal = True
        return self.is_run_terminal

    def DisConnect(self):
        print(f'\n\nDisconnect:')
        self.stop_trade.set()
        self.timer.stop()
        self.is_run_terminal = False
        return self.is_run_terminal

class Binance(Exchange):

    def __init__(self, **kwargs):
        params = {'name': 'Binance', 'account': 'BI_76', 'is_real': False,
                  'ticker': 'BTCUSDT',
                  'tickers': ['BTCUSDT', 'BTCRUB', 'BTCEUR', 'BTCGBP']}

        super(Binance, self).__init__(**params)


    def servertime(self):
        self.server_time = datetime.utcnow()
        return self.server_time


    def Connect(self):
        print(f'Connect ...')
        self.stop_trade.clear()
        self.timer = RepeatedTimer(interval=0.5, function=self.tick)

        self.is_run_terminal = True
        return self.is_run_terminal

    def DisConnect(self):
        print(f'\n\nDisconnect:')
        self.stop_trade.set()
        self.timer.stop()
        self.is_run_terminal = False
        return self.is_run_terminal

