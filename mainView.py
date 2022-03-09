#https://stackoverflow.com/questions/36609017/kivy-spinner-widget-with-multiple-selection

import time
from datetime import datetime

from kivy.config import Config
Config.set('kivy', 'exit_on_escape', '0')

from kivy.lang import Builder
from kivy.properties import ListProperty, ObjectProperty, StringProperty

#  импорт классов для  .kv - файла
from SpinnerExchange import ExchangeSpinner
from SpinnerExchange import StrategySpinner
from SpinnerExchange import CurrencySpinner

from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.popup import Popup


#https://stackoverflow.com/questions/16981921/relative-imports-in-python-3

#  импорт классов для отображения
from EXCANGES import Exchange, Trade, OrderBook

Builder.load_file('Color.kv')
Builder.load_file('ColorWidget.kv')
Builder.load_file('mainView.kv')


class View(BoxLayout):

    exchange_values        = ListProperty([])   # cписок Бирж для ExchangeSpinner
    exchange               = ObjectProperty()   # Установленная Биржа
    name_exchange          = StringProperty('') # имя выбранной биржи
    btn_connect_exchange   = ObjectProperty()   # кнопка подключения Биржи


    '---- Отображаемые  Параметры Exchange -------------------------------------'
    account               = StringProperty()    # Номер Счета
    balance               = StringProperty()    # Баланс Счета
    casch                 = StringProperty()    # Чистый Баланс Счета
    server_time           = StringProperty()    # Время Сервера

    #  ИНСТРУМЕНТ
    currency_values       = ListProperty([])    # cписок Бирж для CurrencySpinner
    currency              = ObjectProperty()    # выбраннsq инструмент
    name_currency         = StringProperty()    # имя выбранного инструмента

    security_price        = StringProperty('$15336.89')
    secyrity_change_day   = StringProperty('+30.35 %')
    security_price        = StringProperty('price')    # Изменеия цены за День
    security_change_day   = StringProperty('day')      # Изменеия цены за День
    security_change_week  = StringProperty('week')     # Изменеия цены за День
    security_change_month = StringProperty('month')    # Изменеия цены за День
    security_change_yahr  = StringProperty('yahr')     # Изменеия цены за День
    security_best_bid     = StringProperty('best_bid') # Изменеия цены за День
    security_best_ask     = StringProperty('best_ask') # Изменеия цены за День

    strategy_values       = ListProperty([])           # cписок Стратегий для StrategySpinner
    name_strategy         = StringProperty()           # имя стратегии

    strategy_profit       = StringProperty('$1111.56')
    strategy_profit_change= StringProperty('(+1.23%)')
    strategy_dropdown     = StringProperty('$1333.00')
    strategy_dropdown_level= StringProperty('(+3.44%)')

    strategy_profit_buy            = StringProperty('231234.56')
    strategy_profit_sell           = StringProperty('39865.34')
    strategy_profit_total          = StringProperty('123.0')
    strategy_trades_sell           = StringProperty('354')
    strategy_trades_buy            = StringProperty('151')
    strategy_summ                  = StringProperty('545.21')
    strategy_volume                = StringProperty('56')
    strategy_open_price            = StringProperty('#123.89')
    strategy_direction             = StringProperty('SELL')
    strategy_open_time             = StringProperty(datetime.now().strftime(f'%d-%m-%y %H:%M:%S'))
    strategy_time_start   = StringProperty(datetime.now().strftime(f'%d-%m-%y %H:%M:%S'))
    strategy_time_work    = StringProperty(datetime.now().strftime(f'%H:%M:%S'))

    logger                 = ObjectProperty()   # окно логгинга
    logging_info           = StringProperty('') # техт окна логгера

    def __init__(self, **kwargs):
        super(View, self).__init__(**kwargs)
        Window.bind(on_request_close=self.on_request_close)

        # Установка списка Имен Бирж из разработтанных наследников классa <Exchange> '
        self.exchanges = [cl for cl in Exchange.__subclasses__()]
        print(f'self.exchanges==>{self.exchanges}')
        # список имен Бирж
        self.exchange_values = [str(cls.__name__) for cls in self.exchanges]
        print(f'self.exchange_values==>{self.exchange_values}')

        # имя биржи по умолчанию
        #self.name_exchange = "Unicorn"
        self.name_exchange = "Binance"
        self.exchange = next(cl for cl in self.exchanges if cl.__name__ == self.name_exchange)()

        print(f'Создан экземпляр  класс биржи : {self.exchange}')

        # установка CаllBack function в exchange_spinner '
        self.exchange_spinner.update = self.on_select_exchange

        ######################################################################
        # установка CаllBack function изменения состояния биржи
        self.exchange.on_changed    = self.on_tick
        self.exchange.on_trade      = self.on_trade
        self.exchange.on_orderbook  = self.on_orderbook
        #####################################################################

        ' Установка списка Имен Инструментов из инструментов выбранной Биржи'
        self.name_currency = self.exchange.currencies[1]
        self.exchange.name_instrument = self.name_currency
        self.currency_values = self.exchange.currencies
        self.currency_spinner.values = self.currency_values
        self.currency_spinner.update = self.on_select_currency


        self.strategy_values =['MACD','Impuls','DeepRL']
        self.strategy = 'MACD'
        self.strategy_spinner.update = self.on_select_strategy

        self.logging_info = f'Exchange: {self.exchange.name}\n' \
                            f'Security: {self.name_currency}'
        print(f'{(self.__class__.__name__).ljust(15)}. Init() {datetime.now()} exchange:{self.exchange}')

    def on_request_close(self, *args):
        print("View.Close !!!")
        self.exchange.DisConnect()
        time.sleep(10)

    def on_select_exchange(self, instance, value):
        self.name_exchange = value
        self.exchange = next(cl for cl in self.exchanges if cl.__name__ == value)()

        # setup callback from Exchange
        self.exchange.on_changed   = self.on_tick
        self.exchange.on_trade     = self.on_trade
        self.exchange.on_orderbook = self.on_orderbook

        self.currency_values = self.exchange.currencies



        self.on_tick(self.exchange)
        self.on_trade(self.exchange)
        self.on_orderbook(self.exchange)

        # имя выбранноого инструмента
        self.name_currency = self.exchange.currencies[1]

        self.logging_info += f'\nВыбрана {self.exchange.name}'

    def on_select_currency(self, instance, value):
        # имя выбранноого инструмента
        self.name_currency = value
        self.exchange.name_instrument = value

        print(f'===>{instance.__class__.__name__} : {value}')
        self.logging_info += f'\nВыбрана {self.name_currency}'
        #self.on_tick()

        self.exchange.on_changed = self.on_tick
        #self.update(self.exchange)

    def on_select_strategy(self, instance, value):
        self.name_strategy = value
        #print(f'===>{instance.__class__.__name__} : {value}')
        self.logging_info += f'\nВыбрана {self.name_strategy}'

    def on_tick(self, exchange):
        self.server_time = exchange.server_time.strftime(f'%d-%m-%y %H:%M:%S.%f')[:-3]
        self.account = f'{exchange.account.id}'
        if exchange.account.currency == "RUB":
            self.balance = f'{exchange.account.balance:.2f} {exchange.account.currency}'
            self.casch   = f'{exchange.account.casch:.2f} {exchange.account.currency}'
        else:
            self.balance = f'{exchange.account.currency} {exchange.account.balance:.2f}'
            self.casch   = f'{exchange.account.currency} {exchange.account.casch:.2f}'

        #return
        self.security_price        = f'${exchange.security_price:.2f}'
        self.security_change_day   = f'{exchange.security_change_day:.3}%'
        self.security_change_week  = f'{exchange.security_change_week:.3}%'
        self.security_change_month = f'{exchange.security_change_month:.3}%'
        self.security_change_yahr  = f'{exchange.security_change_yahr:.3}%'
        self.security_best_bid     = f'${exchange.security_best_bid:.2f}'
        self.security_best_ask     = f'${exchange.security_best_ask:.2f}'

    def on_trade(self,ex: Exchange):
        if ex.trade == None : return
        self.server_time = ex.trade.time.strftime(f'%d-%m-%y %H:%M:%S.%f')[:-3]
        self.security_price = f'${ex.trade.price:.2f}'
        #print(f'View: {self.server_time} : {self.security_price}')

    def on_orderbook(self, ex: Exchange):
        if ex.orderbook == None       : return
        if len(ex.orderbook.bids) ==0 : return
        if len(ex.orderbook.asks) ==0 : return

        self.security_best_bid = f'${ex.orderbook.bids[0].price:.2f}'
        self.security_best_ask = f'${ex.orderbook.asks[0].price:.2f}'

    def changed_currency(self,instance, value):
        self.currency = (next(cl for cl in self.currencys if cl.__name__ == value))()
        print(self.name_currency)
        self.exchange.name_instrument = self.currency
        #self.exchange.on_changed = self.on_changed

    def CanStart(self):
        return not self.exchange.is_run_terminal

    def CanStop(self):
        #self.logger.text +=f'\n CanStop()'
        return self.exchange.is_run_terminal

    #  запуск биржи
    def press_connect_exchange(self):

        #print(f'press_connect_exchange()')

        if self.CanStart():
           if not self.exchange_spinner.text in self.exchange_spinner.values:
               #print('Не Выбрана Биржа !!!')
               self.logging_info += f'\nНе Выбрана Биржа !!!'
               return
           if self.exchange.Connect():
              self.btn_connect_exchange.text = "STOP ??? "

        elif self.CanStop():
             self.btn_connect_exchange.text = "START ??? "
             self.exchange.DisConnect()
             self.logging_info += f'\n{self.name_exchange} DisConnect !!!'
             return

        self.logging_info=f'{self.name_exchange} Connect !!!'

    def switch_callback(self, active):
        print(f'switch_callback({active})')

    def press_connect_strategy(self):
        print(f'press__connect_strategy()')
        self.logging_info += f'\n{self.name_strategy} Connect ...'

    def release_connect_strategy(self):
        print(f'release_connect_strategy()')
        self.logging_info += f'\n{self.name_strategy} ... Connect'

    def press_stop_strategy(self):
        #print(f'press__connect_strategy()')
        self.logging_info += f'\n{self.name_strategy} Stop ...'

    def release_stop_strategy(self):
        #print(f'release_stop_strategy()')
        self.logging_info += f'\n{self.name_strategy} ... Stop'

    def on_request_close(self, *args):
        #self.textpopup(title='Exit', text='Are you sure?')
        self.exchange.DisConnect()
        print(f'\n... stop {self.exchange.name.upper()} is_run_terminal={self.exchange.is_run_terminal}')
        print('EXIT !!!')
        exit(0)


    def textpopup(self, title='', text=''):
        """Open the pop-up with the name.

        :param title: title of the pop-up to open
        :type title: str
        :param text: main text of the pop-up to open
        :type text: str
        :rtype: None
        """
        box = BoxLayout(orientation='vertical')
        box.add_widget(Label(text=text))
        mybutton = Button(text='OK', size_hint=(1, 0.25))
        box.add_widget(mybutton)
        popup = Popup(title=title, content=box, size_hint=(None, None), size=(600, 300))
        mybutton.bind(on_release=self.stop)
        popup.open()

    def stop(self):

        exit(0)
