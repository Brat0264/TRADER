
import asyncio, time, threading
from typing import List, Dict
from datetime import datetime

from tinkoff.invest import (
    CandleInstrument,
    Client,
    AsyncClient,
    MarketDataRequest,
    SubscribeCandlesRequest,
    SubscribeTradesRequest,
    SubscriptionAction,
    SubscriptionInterval,
    InstrumentIdType
)

TOKEN_API = 't.45xwA2y5grFqjLQykSOckG90CKHdvSdJIFtwZ5RYbwo1RxKzqWVVRU3tNaDqRWIrlrg4AYnxFZLheNUZ92DOAA'
TOKEN_EMU = 't.m4MxUYNbnJMm92I0Vr17enlhcDit7sEaS7BMKGZH93o9H-gQiXXR8sr73p0GfX_Tb5QAZNewwGHf5hSZBk-hkQ'
async_client = AsyncClient(token=TOKEN_API, sandbox_token= TOKEN_EMU)


from myInstruments import Instrument, Trade, Candle,  TradeInstrument, Account
from EXCANGES import figi_SBER, figi_AAPL, figi_USD
from EXCANGES import Exchange


def sync_stream_trade(figi=figi_SBER) -> int:

    def trades_iterator(figi=figi):

        yield MarketDataRequest(
            subscribe_trades_request = SubscribeTradesRequest(
                 subscription_action = SubscriptionAction.SUBSCRIPTION_ACTION_SUBSCRIBE,
                         instruments = [TradeInstrument(figi=figi)])
        )

        while True: time.sleep(1)

    with Client(token=TOKEN_API) as client:
        trade  = Trade()
        for marketdata in client.market_data_stream.market_data_stream(trades_iterator()):
            #print(marketdata.trade)
            trade.update(marketdata.trade)
    return 0

def sync_stream_candle(figi=figi_SBER) -> int:

    def candles_iterator(figi=figi):
        TIMEFRAME = SubscriptionInterval.SUBSCRIPTION_INTERVAL_ONE_MINUTE
        yield MarketDataRequest(
            subscribe_candles_request = SubscribeCandlesRequest(
                  subscription_action = SubscriptionAction.SUBSCRIPTION_ACTION_SUBSCRIBE,
                          instruments = [CandleInstrument( figi=figi, interval= TIMEFRAME)],
                            )
                            )
        while True: time.sleep(0.01)

    with Client(token=TOKEN_API) as client:
        candle = Candle()
        for marketdata in client.market_data_stream.market_data_stream(candles_iterator()):
            candle.update(marketdata.candle)
    return 0

async def async_stream_candle(figi=figi_SBER) -> int:

    async def candles_iterator(figi=figi):
        TIMEFRAME = SubscriptionInterval.SUBSCRIPTION_INTERVAL_ONE_MINUTE
        yield MarketDataRequest(
            subscribe_candles_request = SubscribeCandlesRequest(
                  subscription_action = SubscriptionAction.SUBSCRIPTION_ACTION_SUBSCRIBE,
                          instruments = [CandleInstrument( figi=figi, interval= TIMEFRAME)],
                            )
                            )
        while True: await asyncio.sleep(0.01)

    async with async_client as client:
        candle = Candle()
        async for marketdata in client.market_data_stream.market_data_stream(candles_iterator()):
            await candle.update(marketdata.candle)
    return 0




class Tinkoff(Exchange):

    def __init__(self, **kwargs):
        self.currencies = [figi_USD, figi_AAPL, figi_SBER]
        self.is_run_terminal = True
        self.stop_trade = threading.Event()

        #super(Tinkoff, self).__init__(**params)

    async def get_instrument(self,figi: str = figi_SBER) -> Instrument:
        id_type = InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI
        async with AsyncClient(token=TOKEN_API) as client:
            resp = client.instruments.get_instrument_by(id=figi, id_type=id_type)
            cur = await resp
            instrument = Instrument(dict=cur.instrument)
            #print(instrument)
            return instrument

    async def get_instruments(self, tickers = None ) -> List[Instrument]:

        tickers = self.currencies if tickers == None else tickers
        tasks = []
        for arg in tickers:
            #print(arg)
            # создаем задачи
            task = self.get_instrument(figi=arg)
            #print(f'INSTRUMENT: {task}')
            # складываем задачи в список
            tasks.append(task)
        # планируем одновременные вызовы
        self.instruments = await asyncio.gather(*tasks)

        return self.instruments

    async def run_stream_trade(self,loop, figi=figi_SBER) -> int:

        print(f'STREAM TRADE ==> figi:{figi}')
        instrument = await self.get_instrument(figi=figi)
        # ins= Instrument(data = ins)
        #instrument.info()

        async def trades_iterator(figi=figi):

            yield MarketDataRequest(
                subscribe_trades_request=SubscribeTradesRequest(
                    subscription_action=SubscriptionAction.SUBSCRIPTION_ACTION_SUBSCRIBE,
                    instruments=[TradeInstrument(figi=figi)])
            )

            while True:
                # остановка stream_trade При закрытии окнв или нажатие кнопки СТОП
                if self.stop_trade.is_set():   return
                await asyncio.sleep(0.01)

        async with AsyncClient(token=TOKEN_API) as client:

            trade = Trade(instrument=instrument)
            # input('=======================================')
            async for marketdata in client.market_data_stream.market_data_stream(trades_iterator()):
                await trade.async_update(marketdata.trade)
                print('', end = f'\r {trade.info()}' )



        return 0

    def loop_in_thread(self, loop, ticker):
        loop.run_until_complete(self.run_stream_trade(loop=loop, figi=ticker))

    # ПОДКЛЮЧЕНИЕ  БИРЖИ
    def Connect(self):

        self.selected_instrument = figi_SBER
        self.stop_trade.clear()

        loop = asyncio.get_event_loop()
        asyncio.set_event_loop(loop)

        # Получение экземпляров Instrument по списку рабочих figi
        try:
            loop.run_until_complete(self.get_instruments(tickers=self.currencies))
            #[print(ins) for ins in self.instruments ]
        except  BaseException as ex:
            print(f'ERROR {self.__class__.__name__}.Connect()'
                  f'\n  get_instruments({self.currencies}): {str(ex)}')

        print(f'\nПОЛУЧЕНЫ ИНСТРУМЕНТЫ:')
        list_ins = [print(f'{ins.figi}:{ins.ticker}') for ins in self.instruments]


        print(f'{self.__class__.__name__}.currentis:{self.currencies}')

        '''
        task = loop.create_task(self.run_stream_trade(loop=loop, figi=figi_AAPL))
        # task = loop.create_task(async_stream_candle(figi=figi_AAPL))
        bundle = asyncio.wait([task])
        try:
            loop.run_until_complete(bundle)
        finally:
            loop.close()
        '''
        selected_instrument = next((x for x in self.instruments if x.figi == self.selected_instrument), None)
        if selected_instrument == None:
            print(f'{self.name} - Не подтверждено наличие {self.selected_instrument} !!!')
            return
        self.selected_instrument = selected_instrument

        print(f'self.selected_instrument === {self.selected_instrument.figi}:{self.selected_instrument.ticker}')

        # Запуск Службы Сервиса Кoтировок
        stream_trade = threading.Thread(target=self.loop_in_thread,
                                        name='stram_trades',
                                        args=(loop,self.selected_instrument.figi))
        stream_trade.start()

        time.sleep(0.5)

        return self.is_run_terminal



    def DisConnect(self):
        self.stop_trade.set()
        self.is_run_terminal = False
        print('\n ... DisConnect')

    def servertime(self):
        pass

if __name__ == "__main__":

    params = {'name': 'Tinkoff', 'account': 'BI_76', 'is_real': False,
              'ticker': figi_USD,
              'currencies': [figi_USD, figi_SBER, figi_AAPL]}

    ex= Tinkoff(**params)

    ex.Connect()

    for n in range(10):
        print('',end = f'\r\ntick={n}')
        time.sleep(1)

    ex.DisConnect()


    '''
    Tinkoff= Tinkoff()
    #asyncio.run(Tinkoff.run_stream_trade(figi=figi_AAPL))

    time.sleep(10)
    Tinkoff.DisConnect()
    print('.... Wait')

    '''


