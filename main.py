#https://stackoverflow.com/questions/36609017/kivy-spinner-widget-with-multiple-selection

#Мобильное приложение под Android за 12 минут / уроки Kivy / Как получить APK
#https://www.youtube.com/watch?v=s7kNe5o86yYimport logging

import logging
logging.disable(logging.INFO)

from kivy.core.window import Window
from kivy.config import Config

from kivy.base import runTouchApp

Window.size = (360, 800)
Config.set('kivy', 'keyboard_mode', 'systemanddock')    # Экранная клавиатура

#Создаем apk приложения для Android на Python
#https://python-scripts.com/kivy-android-ios-exe


# Олег МОЛЧАНОВ - Уроки Kivy #1: Установка Kivy и сборка apkpip3 install pyenvpip install.com/kivy/buildozer.gitpJrrQU
#https://kivy.org/doc/stable/guide/packaging-android.html#buildozer

# GIT
#https://github.com/kivy/buildozer

#buildozer init
#buildozer -v android debug

from mainView import View

#https://kivy.org/doc/stable/api-kivy.uix.tabbedpanel.html
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.uix.tabbedpanel import TabbedPanelHeader
if __name__ == '__main__':

    tablepanel = TabbedPanel(tab_height=30, tab_width=180)
    tablepanel.default_tab_text = "View"

    logger = TabbedPanelHeader(text='Loger')
    tablepanel.add_widget(logger)

    tablepanel.default_tab_content = View()

    print('------------------')
    deepRL = TabbedPanelHeader(text='Deep RL')
    tablepanel.add_widget(deepRL)

    tablepanel.switch_to(logger)
    tablepanel.tab_pos = 'bottom_left'

    runTouchApp(tablepanel)
