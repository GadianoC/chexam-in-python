from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.graphics import Rectangle
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
import os
import logging
from ..utils.secure_storage import save_api_key, get_api_key, delete_api_key, GEMINI_API_KEY
from .base_screen import BaseScreen

logger = logging.getLogger("chexam.ui.settings_screen")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

class SettingsScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(title="Settings", **kwargs)
        
        # Set background
        with self.canvas.before:
            self.bg_rect = Rectangle(source='bg.png', size=self.size, pos=self.pos)
        self.bind(size=self._update_bg, pos=self._update_bg)
        
        # Center the title text
        self.title_label.halign = 'center'
        self.title_label.text_size = self.size
        self.bind(size=lambda *args: setattr(self.title_label, 'text_size', self.size))
        
        self.set_back_destination('home')
        
        # Main layout
        settings_layout = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(20))
        
        # API Key section
        api_key_section = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(200), spacing=dp(10))
        
        api_key_label = Label(
            text='Gemini API Key',
            size_hint_y=None,
            height=dp(30),
            font_size=dp(18),
            halign='left',
            valign='middle'
        )
        api_key_label.bind(size=lambda *args: setattr(api_key_label, 'text_size', api_key_label.size))
        
        api_key_description = Label(
            text='Enter your Gemini API key to use the Gemini Vision API for bubble sheet detection.',
            size_hint_y=None,
            height=dp(60),
            font_size=dp(14),
            halign='left',
            valign='top'
        )
        api_key_description.bind(size=lambda *args: setattr(api_key_description, 'text_size', api_key_description.size))
        
        # Get current API key if it exists
        current_api_key = get_api_key(GEMINI_API_KEY, "")
        
        self.api_key_input = TextInput(
            text=current_api_key,
            hint_text='Enter your Gemini API key',
            password=True,  # Hide the API key by default
            multiline=False,
            size_hint_y=None,
            height=dp(40),
            font_size=dp(16)
        )
        
        # Show/Hide API key button
        self.show_key_btn = Button(
            text='Show Key',
            size_hint=(None, None),
            size=(dp(100), dp(40)),
            pos_hint={'right': 1}
        )
        self.show_key_btn.bind(on_press=self.toggle_key_visibility)
        
        # Save API key button
        save_key_btn = Button(
            text='Save API Key',
            size_hint_y=None,
            height=dp(50),
            background_normal='',
            background_color=(0.2, 0.6, 1, 1),
            color=(1, 1, 1, 1)
        )
        save_key_btn.bind(on_press=self.save_api_key)
        
        # Clear API key button
        clear_key_btn = Button(
            text='Clear API Key',
            size_hint_y=None,
            height=dp(50),
            background_normal='',
            background_color=(0.8, 0.3, 0.3, 1),
            color=(1, 1, 1, 1)
        )
        clear_key_btn.bind(on_press=self.clear_api_key)
        
        # Button row for show/hide and save
        btn_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10))
        btn_row.add_widget(self.show_key_btn)
        
        # Add widgets to API key section
        api_key_section.add_widget(api_key_label)
        api_key_section.add_widget(api_key_description)
        api_key_section.add_widget(self.api_key_input)
        api_key_section.add_widget(btn_row)
        api_key_section.add_widget(save_key_btn)
        api_key_section.add_widget(clear_key_btn)
        
        # Add API key section to main layout
        settings_layout.add_widget(api_key_section)
        
        # Add a spacer
        settings_layout.add_widget(BoxLayout(size_hint_y=1))
        
        # Add settings layout to content area
        self.content_area.add_widget(settings_layout)
        
        # Status message at the bottom
        self.status_label = Label(
            text='',
            size_hint_y=None,
            height=dp(30),
            font_size=dp(14),
            color=(0.2, 0.8, 0.2, 1)
        )
        settings_layout.add_widget(self.status_label)
    
    def _update_bg(self, *args):
        self.bg_rect.size = self.size
        self.bg_rect.pos = self.pos
    
    def toggle_key_visibility(self, instance):
        if self.api_key_input.password:
            self.api_key_input.password = False
            self.show_key_btn.text = 'Hide Key'
        else:
            self.api_key_input.password = True
            self.show_key_btn.text = 'Show Key'
    
    def save_api_key(self, instance):
        api_key = self.api_key_input.text.strip()
        
        if not api_key:
            self.show_status_message('API key cannot be empty', error=True)
            return
        
        # Save the API key to secure storage
        if save_api_key(GEMINI_API_KEY, api_key):
            self.show_status_message('API key saved successfully')
            
            # Update environment variable for the current session
            os.environ['GEMINI_API_KEY'] = api_key
            
            # Reload Gemini Vision module to use the new API key
            try:
                from ..processing import gemini_vision
                gemini_vision.api_key = api_key
                gemini_vision.GEMINI_AVAILABLE = True
                logger.info("Gemini Vision module updated with new API key")
            except Exception as e:
                logger.error(f"Failed to update Gemini Vision module: {e}")
        else:
            self.show_status_message('Failed to save API key', error=True)
            
    def clear_api_key(self, instance):
        # Clear the text input
        self.api_key_input.text = ''
        
        # Delete the API key from secure storage
        if delete_api_key(GEMINI_API_KEY):
            self.show_status_message('API key removed successfully')
            
            # Remove from environment variables for the current session
            if 'GEMINI_API_KEY' in os.environ:
                del os.environ['GEMINI_API_KEY']
            
            # Update Gemini Vision module
            try:
                from ..processing import gemini_vision
                gemini_vision.api_key = None
                gemini_vision.GEMINI_AVAILABLE = False
                logger.info("Gemini Vision module updated - API key removed")
            except Exception as e:
                logger.error(f"Failed to update Gemini Vision module: {e}")
        else:
            self.show_status_message('No API key found to remove', error=True)
    
    def show_status_message(self, message, error=False):
        self.status_label.text = message
        if error:
            self.status_label.color = (1, 0.3, 0.3, 1)  # Red for errors
        else:
            self.status_label.color = (0.2, 0.8, 0.2, 1)  # Green for success
        
        # Clear the message after 3 seconds
        Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', ''), 3)
