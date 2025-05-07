from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.metrics import dp
from .base_screen import BaseScreen

class HomeScreen(BaseScreen):
    def __init__(self, switch_to_scanner, go_to_answer_key, go_to_students, go_to_analysis, **kwargs):
        super().__init__(title="Chexam", **kwargs)
        
        # Hide back button on home screen
        self.back_btn.opacity = 0
        self.back_btn.disabled = True
        
        # Create content layout
        content_layout = BoxLayout(orientation='vertical', spacing=dp(20), padding=dp(15))

        # Welcome label
        label = Label(
            text='[b]Welcome to Chexam[/b]', 
            markup=True, 
            font_size=dp(28), 
            size_hint_y=None, 
            height=dp(60)
        )
        
        # Description label
        desc_label = Label(
            text='Scan and analyze bubble sheets easily on your mobile device', 
            font_size=dp(16), 
            size_hint_y=None, 
            height=dp(40),
            halign='center'
        )
        desc_label.bind(size=desc_label.setter('text_size'))
        
        # Button style function
        def style_button(btn):
            btn.background_normal = ''
            btn.background_color = (0.2, 0.6, 1, 1)
            btn.border = (0, 0, 0, 0)
            btn.color = (1, 1, 1, 1)
            btn.size_hint_y = None
            btn.height = dp(70)
            btn.font_size = dp(20)
            return btn

        # Start Scanning button
        btn_scanner = style_button(Button(text='📷 Start Scanning'))
        btn_scanner.bind(on_press=lambda instance: switch_to_scanner())

        # Add button to go to Answer Key screen
        btn_answer_key = style_button(Button(text='🔑 Answer Key Management'))
        btn_answer_key.bind(on_press=lambda instance: go_to_answer_key())
        
        # Add button to go to Students screen
        btn_students = style_button(Button(text='👥 Student Management'))
        btn_students.bind(on_press=lambda instance: go_to_students())
        
        # Add button to go to Analysis screen
        btn_analysis = style_button(Button(text='📊 Class Analysis'))
        btn_analysis.bind(on_press=lambda instance: go_to_analysis())
        
        # Add spacers for better layout
        top_spacer = BoxLayout(size_hint_y=None, height=dp(20))
        bottom_spacer = BoxLayout(size_hint_y=None, height=dp(20))

        # Add widgets to content layout
        content_layout.add_widget(top_spacer)
        content_layout.add_widget(label)
        content_layout.add_widget(desc_label)
        content_layout.add_widget(BoxLayout(size_hint_y=None, height=dp(30)))
        content_layout.add_widget(btn_scanner)
        content_layout.add_widget(BoxLayout(size_hint_y=None, height=dp(10)))
        content_layout.add_widget(btn_answer_key)
        content_layout.add_widget(BoxLayout(size_hint_y=None, height=dp(10)))
        content_layout.add_widget(btn_students)
        content_layout.add_widget(BoxLayout(size_hint_y=None, height=dp(10)))
        content_layout.add_widget(btn_analysis)
        content_layout.add_widget(bottom_spacer)

        # Add content layout to the content area
        self.content_area.add_widget(content_layout)

