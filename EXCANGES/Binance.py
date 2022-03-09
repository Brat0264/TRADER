import logging
import os
import requests
import sys
import time
import threading
from datetime import datetime

#pip install unicorn-binance-suite --upgrade --force-reinstall

#https://www.lucit.tech/unicorn-binance-websocket-api.html

from unicorn_binance_websocket_api.manager import BinanceWebSocketApiManager
from unicorn_binance_rest_api import BinanceRestApiManager

from EXCANGES.Exchange import Exchange
from EXCANGES.myInstruments import Instrument, Trade, Candle, OrderBook, MarketData
from typing import List, Dict
from unicorn_fy.unicorn_fy import UnicornFy

#channels = {'aggTrade', 'trade', 'kline_1m', 'kline_5m', 'kline_15m', 'kline_30m', 'kline_1h', 'kline_2h', 'kline_4h',
#            'kline_6h', 'kline_8h', 'kline_12h', 'kline_1d', 'kline_3d', 'kline_1w', 'kline_1M', 'miniTicker',
#            'ticker', 'bookTicker', 'depth5', 'depth10', 'depth20', 'depth', 'depth@100ms'}
#arr_channels = {'!miniTicker', '!ticker', '!bookTicker'}

markets = []


def init():


    API_KEY    = 'NuEXVsz2gIRWA31vfP56EXouJwCfLDKD6QXe6vNpM53d0yAZMrUxhdWrJ6dOagZ6'
    API_SECRET = 'GK5bDXYr8eWCSTkATPqm5RyVQBXbXjCnFjRGFYOYRrJTMex8pDG2SDKCySrV5Ixt'
    ubra = BinanceRestApiManager(api_key = API_KEY, api_secret = API_SECRET, exchange="binance.com")

    # get market depth
    depth = ubra.get_order_book(symbol='BNBBTC')
    print(f"{depth}")

    # get all symbol prices
    prices = ubra.get_all_tickers()
    print(f"{prices}")

    # get the used weight:
    # https://github.com/binance-us/binance-official-api-docs/blob/master/rest-api.md#limits
    print(f"Used weight: {ubra.get_used_weight()}")

class Unicorn(Exchange):

    API_KEY = 'NuEXVsz2gIRWA31vfP56EXouJwCfLDKD6QXe6vNpM53d0yAZMrUxhdWrJ6dOagZ6'
    API_SECRET = 'GK5bDXYr8eWCSTkATPqm5RyVQBXbXjCnFjRGFYOYRrJTMex8pDG2SDKCySrV5Ixt'

    def __init__(self, **kwargs):

        super(Unicorn, self).__init__(**kwargs)

        try:
            self.rest_client = BinanceRestApiManager(api_key=self.API_KEY,
                                                     api_secret= self.API_SECRET)
            self.webs_client = BinanceWebSocketApiManager(exchange="binance.com")
            self.webs_client.enable_stream_signal_buffer=True

        except requests.exceptions.ConnectionError:
            print("No internet connection?")
            sys.exit(1)

    def get_instrument(self, figi:str):
        res = self.rest_client.get_symbol_info(symbol="BTCUSDT")
        print(res)
        return Instrument(res)

    def client_socket(self, client):
        #https://www.lucit.tech/unicorn-binance-websocket-api.html

        self.stream = client.create_stream(channels= ['trade'], #'kline_1m'],
                                           markets = [self.selected_instrument])
        n=0
        self.trade = Trade()
        while True:

            # остановка stream_trade При закрытии окнв или нажатие кнопки СТОП
            if self.stop_trade.is_set()               : break

            if self.webs_client.is_manager_stopping() : break

            _data = client.pop_stream_data_from_stream_buffer()

            try:
                data = UnicornFy.binance_com_websocket(_data)

                if data != False:
                    if data != None :
                        if not 'result' in data.keys():

                            if self.trade.iD < int(data['trade_id']):
                               self.trade = Trade(instrument=self.instrument,
                                                  trade=data)
                               if self.trade != None:
                                  self.on_trade(self)

                            #print(f'{type(data)}:{data}')
                            #print('',end =  f'\r{self.trade.info()} stop_trade={self.stop_trade.is_set()}')
                            #self.get_order_book(self.selected_instrument)
            except ex:
                print(f'Error Unicorn.client_socket({_data}) {ex}')
                break

        client.unsubscribe_from_stream(self.stream, channels=['trade'], markets=[self.selected_instrument])
        client.stop_stream(self.stream)
        client.stop_manager_with_all_streams()

        #stream_ID = list(client.stream_list.values())[0]["stream_id"]
        #print(f' stream_id = {stream_ID}')
        #time.sleep(2.0)
         #stream_id=stream_ID)

        #print(f'\n******************** {res} stream:{self.stream}\n')

    def servertime(self) -> datetime:
        return self.rest_client.get_server_time()

    def get_instruments(self, tickers = None ) -> List[Instrument]:
        pass

    def get_order_book(self, symbol) -> OrderBook:

        e_time = datetime.utcnow()
        try:
            order_book = self.rest_client.get_order_book(symbol = self.selected_instrument)
        except :
            print(f'ERROR: UNICORN.get_order_book{self.selected_instrument}\n')
            return None

        self.orderbook = OrderBook(ticker=symbol, order_book=order_book, time=e_time)
        return self.orderbook

    def get_last_price(self, symbol) -> OrderBook:

        e_time = datetime.utcnow()
        try:
            last_trade = self.rest_client.get_symbol_ticker(symbol = self.selected_instrument)
        except :
            print(f'ERROR: UNICORN.get_order_book{self.selected_instrument}\n')
            return None

        self.trade = Trade()
        return

    def stream_signals(self):
        while True:
            if self.webs_client.is_manager_stopping():
                break
            stream_signal = self.webs_client.pop_stream_signal_from_stream_signal_buffer()
            if stream_signal is False:
                time.sleep(0.001)
            else:
                print(stream_signal)

    def Connect(self):

        self.instrument = self.get_instrument(figi='BTCUSDT')

        #return
        self.stop_trade.clear()
        # запуск потока обработки Сообзений Службы Котировок
        #worker_thread = threading.Thread(target=self.stream_signals, args=())
        #worker_thread.start()


        # Запуск Службы Сервиса Кoтировок
        self.trade_stream_id = self.webs_client.create_stream(["trade"], ['BTCUSDT'])

        self.stream_trade= threading.Thread(name='socket_trade',
                                            target=self.client_socket,
                                            args=(self.webs_client,))
        self.stream_trade.start()


        print(f'\nConnect() : start {self.trade_stream_id}')
        self.is_run_terminal = True
        return self.is_run_terminal

    def DisConnect(self):
        print(f'\n\nDisconnect:')

        self.stop_trade.set()

        self.rest_client.session.close()
        self.webs_client.stop_stream(self.trade_stream_id)
        self.webs_client.stop_manager_with_all_streams()


        '''
        while self.stream_trade.is_alive():
            FL = True if self.stop_trade.is_set() else False
            print(f'поток: {self.stream_trade.name} = {self.stream_trade.is_alive()}')
            time.sleep(0.1)
        '''
        self.is_run_terminal = False
        print('... DisConnect')

        '''
        stream_ID = list(self.webs_client.stream_list.values())[0]["stream_id"]
        print(f' stream_id = {stream_ID}')
        self.webs_client.stop_stream(stream_ID)
        th = self.webs_client.stream_list
        print(f'th:[{len(th)}]\n'
              f'  [{len(th.keys())}] {th.keys()}\n'
              f'  [{len(th.values())}] {th.values()}\n'
              )
        '''
        n=0
        while True:
            if self.webs_client.is_manager_stopping():
               break
            print(f'time={n}')
            n += 1
            time.sleep(1.0)

        return


from subprocess import Popen, PIPE


#Do whatever filtering and processing is needed

if __name__ == "__main__":

    params = {'name': 'Binance', 'account': 'BI_76', 'is_real': False,
              'ticker': 'BTCUSDT',
              'tickers': ['BTCUSDT', 'BTCRUB', 'BTCEUR', 'BTCGBP']}
    for _ in range(1):
        ex = Unicorn(**params)
        ex.Connect()
        time.sleep(5)
        ex.DisConnect()
    exit(0)
