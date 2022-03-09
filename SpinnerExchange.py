#https://stackoverflow.com/questions/36609017/kivy-spinner-widget-with-multiple-selection

from kivy.factory import Factory
from kivy.properties import ListProperty, ObjectProperty, StringProperty
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button

from datetime import datetime

class Spinner(Button):

    dropdown = ObjectProperty(None)
    values = ListProperty([])
    selected_values = StringProperty()  # ListProperty([])

    def __init__(self, **kwargs):
        self.bind(dropdown=self.update_dropdown)
        self.bind(values=self.update_dropdown)
        super(Spinner, self).__init__(**kwargs)
        self.bind(on_release=self.toggle_dropdown)

    def toggle_dropdown(self, *args):
        if self.dropdown.parent:
            self.dropdown.dismiss()
        else:
            self.dropdown.open(self)

    def update_dropdown(self, *args):
        if not self.dropdown:
            self.dropdown = DropDown()
        values = self.values
        if values:
            if self.dropdown.children:
                self.dropdown.clear_widgets()
            for value in values:
                b = Factory.MultiSelectOption(text=value)
                b.bind(state=self.select_value)
                self.dropdown.add_widget(b)

    def select_value(self, instance, value):
        #print(f'selected_values : {instance.__class__.__name__}.text={instance.text} {value}')
        self.selected_values = instance.text
        self.dropdown.dismiss()
        '''
        if value == 'down':
            #if instance.text not in self.selected_values:
                #self.selected_values.append(instance.text)

        return

        else:
            if instance.text in self.selected_values:
                #self.selected_values.remove(instance.text)
                self.selected_values = instance.text
        '''

    def callback(self, instance, value):
        print(f'{instance}   {value} {type(value)}')

    def on_selected_values(self, instance, value):
        #print(f'on_selected_values : {instance.__class__.__name__} {value}')
        self.update(self, value)
        if value:
            self.text = value
        else:
            self.text = ''

class ExchangeSpinner(Spinner):

    def __init__(self, **kwargs):
        super(ExchangeSpinner, self).__init__(**kwargs)

        print(f'{(self.__class__.__name__).ljust(15)}. Init() {datetime.now()}')

class StrategySpinner(Spinner):

    def __init__(self, **kwargs):
        super(StrategySpinner, self).__init__(**kwargs)

        print(f'{(self.__class__.__name__).ljust(15)}. Init() {datetime.now()}')

class CurrencySpinner(Spinner):

    def __init__(self, **kwargs):
        super(CurrencySpinner, self).__init__(**kwargs)

        print(f'{(self.__class__.__name__).ljust(15)}. Init() {datetime.now()}')