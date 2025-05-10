from kivy.uix.boxlayout import BoxLayout 
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.metrics import dp
from kivy.graphics import Rectangle
from .base_screen import BaseScreen

class HomeScreen(BaseScreen):
    def __init__(self, switch_to_scanner, go_to_answer_key, go_to_students, go_to_analysis, go_to_settings, **kwargs):
        super().__init__(title="Chexam", **kwargs)
        
        # Set background image
        with self.canvas.before:
            self.bg_rect = Rectangle(source='bg.png', size=self.size, pos=self.pos)
        self.bind(size=self._update_bg, pos=self._update_bg)

        # Hide back button
        self.back_btn.opacity = 0
        self.back_btn.disabled = True
        
        # Main layout
        content_layout = BoxLayout(orientation='vertical', spacing=dp(5), padding=dp(10))

        # Title label (black font)
        label = Label(
            text='[b]Welcome to Chexam[/b]', 
            markup=True, 
            font_size=dp(24), 
            size_hint_y=None, 
            height=dp(50),
            color=(0, 0, 0, 1)  # Black
        )

        # Logo
        logo_image = Image(
            source='ChexamLogo.png',
            size_hint_y=None,
            height=dp(200),
            allow_stretch=True,
            keep_ratio=True
        )

        # Description label (black font)
        desc_label = Label(
            text='Scan and analyze bubble sheets easily on your mobile device', 
            font_size=dp(14), 
            size_hint_y=None, 
            height=dp(30),
            halign='center',
            color=(0, 0, 0, 1)  # Black
        )
        desc_label.bind(size=desc_label.setter('text_size'))

        # Function to style and center buttons
        def create_centered_button(text, color, callback):
            btn = Button(
                text=text,
                background_normal='',
                background_color=color,
                color=(1, 1, 1, 1),
                font_size=dp(16),
                size_hint=(None, None),
                height=dp(50),
                width=dp(250)
            )
            btn.bind(on_press=lambda instance: callback())
            anchor = AnchorLayout(anchor_x='center')
            anchor.add_widget(btn)
            return anchor

        # Add components in the right order
        content_layout.add_widget(label)                # Title above logo
        content_layout.add_widget(logo_image)           # Logo
        content_layout.add_widget(desc_label)           # Description below logo
        content_layout.add_widget(create_centered_button('📷 Start Scanning', (0, 0.75, 0.39, 1), switch_to_scanner))
        content_layout.add_widget(create_centered_button('🔑 Answer Key Management', (1.0, 0.3529, 0.3333, 1), go_to_answer_key))
        content_layout.add_widget(create_centered_button('👥 Student Management', (0.2745, 0.651, 1.0, 1), go_to_students))
        content_layout.add_widget(create_centered_button('📊 Class Analysis', (1.0, 0.576, 0.2745, 1), go_to_analysis))
        content_layout.add_widget(create_centered_button('⚙️ Settings', (0.5, 0.5, 0.5, 1), go_to_settings))

        # Add to main screen
        self.content_area.add_widget(content_layout)

    def _update_bg(self, *args):
        self.bg_rect.size = self.size
        self.bg_rect.pos = self.pos
