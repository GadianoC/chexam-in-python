from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

class HomeScreen(Screen):
    def __init__(self, switch_to_scanner, go_to_answer_key, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', spacing=20, padding=40)

        # Welcome label
        label = Label(text='[b]Welcome to BubbleScanner![/b]', markup=True, font_size=28, size_hint_y=0.7)

        # Start Scanning button
        btn_scanner = Button(text='Start Scanning', size_hint_y=0.3, font_size=22)
        btn_scanner.bind(on_press=lambda instance: switch_to_scanner())

        # Add button to go to Answer Key screen
        btn_answer_key = Button(text='Go to Answer Key', size_hint_y=0.3, font_size=22)
        btn_answer_key.bind(on_press=lambda instance: go_to_answer_key())

        # Add widgets to layout
        layout.add_widget(label)
        layout.add_widget(btn_scanner)
        layout.add_widget(btn_answer_key)

        # Add layout to the screen
        self.add_widget(layout)

