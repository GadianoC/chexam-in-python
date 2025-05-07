from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.app import App
from kivy.metrics import dp
from kivy.core.window import Window

class BaseScreen(Screen):
    """
    Base screen class that provides a consistent back button in the top left corner.
    All screens should inherit from this class to maintain UI consistency.
    Optimized for mobile devices.
    """
    def __init__(self, title="Screen", **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self._create_layout()
        
    def _create_layout(self):
        """Create the base layout with header (including back button) and content area."""
        # Main layout
        self.main_layout = BoxLayout(orientation='vertical', spacing=dp(8))
        
        # Header with back button and title
        self.header = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60), padding=[dp(8), dp(8), dp(8), dp(8)])
        
        # Back button - larger for touch targets
        self.back_btn = Button(
            text='←', 
            font_size=dp(28),
            size_hint_x=None,
            width=dp(60),
            background_color=(0.2, 0.6, 1, 1),
            background_normal='',
            border=(0, 0, 0, 0)
        )
        self.back_btn.bind(on_press=self.go_back)
        
        # Title label
        self.title_label = Label(
            text=f'[b]{self.title}[/b]', 
            markup=True, 
            font_size=dp(22),
            size_hint_x=1,
            halign='center'
        )
        self.title_label.bind(size=self.title_label.setter('text_size'))
        
        # Add widgets to header
        self.header.add_widget(self.back_btn)
        self.header.add_widget(self.title_label)
        
        # Content area (to be filled by child classes)
        self.content_area = BoxLayout(orientation='vertical', padding=[dp(10), dp(10), dp(10), dp(10)])
        
        # Add header and content area to main layout
        self.main_layout.add_widget(self.header)
        self.main_layout.add_widget(self.content_area)
        
        # Add main layout to screen
        self.add_widget(self.main_layout)
    
    def go_back(self, *args):
        """Navigate back to the previous screen or home screen."""
        app = App.get_running_app()
        sm = app.root
        
        # Default behavior: go back to home screen
        sm.current = 'home'
    
    def set_back_destination(self, screen_name):
        """
        Set a specific destination for the back button.
        
        Args:
            screen_name (str): The name of the screen to navigate to when back button is pressed
        """
        def custom_back(*args):
            app = App.get_running_app()
            sm = app.root
            sm.current = screen_name
            
        self.back_btn.unbind(on_press=self.go_back)
        self.back_btn.bind(on_press=custom_back)
