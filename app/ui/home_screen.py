from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

class HomeScreen(Screen):
    def __init__(self, switch_to_scanner, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', spacing=20, padding=40)
        label = Label(text='[b]Welcome to BubbleScanner![/b]', markup=True, font_size=28, size_hint_y=0.7)
        btn = Button(text='Start Scanning', size_hint_y=0.3, font_size=22)
        btn.bind(on_press=lambda instance: switch_to_scanner())
        layout.add_widget(label)
        layout.add_widget(btn)
        self.add_widget(layout)
