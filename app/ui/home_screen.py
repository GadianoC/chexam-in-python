from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.relativelayout import RelativeLayout
from kivy.properties import NumericProperty


class ResizableButton(Button):
    font_scaling_factor = NumericProperty(0.4)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''  # Use background_color directly

    def on_size(self, *args):
        self.font_size = self.height * self.font_scaling_factor


class HomeScreen(Screen):
    def __init__(self, switch_to_scanner, switch_to_answer_key, switch_to_analysis, **kwargs):
        super().__init__(**kwargs)

        root_layout = RelativeLayout()
        background = Image(source='chexambg (1).png', allow_stretch=True, keep_ratio=False)
        root_layout.add_widget(background)

        float_layout = FloatLayout()

        logo = Image(
            source='ChexamLogo.png',
            size_hint=(0.5, 0.5),
            pos_hint={'center_x': 0.5, 'y': 0.3},
            allow_stretch=True,
            keep_ratio=True
        )

        label = Label(
            text='[b]Welcome to Chexam![/b]',
            markup=True,
            font_size=24,
            size_hint=(None, None),
            size=(self.width, 40),
            pos_hint={'center_x': 0.5, 'y': 0.72},
            color=(0, 0, 0, 1),
        )

        # Buttons
        scan_btn = ResizableButton(
            text='Start Scanning',
            size_hint=(0.4, 0.07),
            pos_hint={'center_x': 0.5, 'y': 0.22},
            background_color=(0, 1, 0, 1),  # Green
            color=(1, 1, 1, 1),
        )
        scan_btn.bind(on_press=lambda instance: switch_to_scanner())

        answer_key_btn = ResizableButton(
            text='Set Answer Key',
            size_hint=(0.4, 0.07),
            pos_hint={'center_x': 0.5, 'y': 0.14},
            background_color=(0, 0, 1, 1),  # Blue
            color=(1, 1, 1, 1),
        )
        answer_key_btn.bind(on_press=lambda instance: switch_to_answer_key())

        analysis_btn = ResizableButton(
            text='Analysis',
            size_hint=(0.4, 0.07),
            pos_hint={'center_x': 0.5, 'y': 0.06},
            background_color=(1, 0, 0, 1),  # Red
            color=(1, 1, 1, 1),
        )
        analysis_btn.bind(on_press=lambda instance: switch_to_analysis())

        # Add widgets
        float_layout.add_widget(logo)
        float_layout.add_widget(label)
        float_layout.add_widget(scan_btn)
        float_layout.add_widget(answer_key_btn)
        float_layout.add_widget(analysis_btn)

        root_layout.add_widget(float_layout)
        self.add_widget(root_layout)
