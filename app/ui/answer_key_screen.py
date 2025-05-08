from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle
from app.ui.answer_key import AnswerKey
from .base_screen import BaseScreen
import logging

class AnswerKeyScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(title="Answer Key Management", **kwargs)
        
        # Set bg.png as the background
        with self.canvas.before:
            self.bg_rect = Rectangle(source='bg.png', size=self.size, pos=self.pos)
        self.bind(size=self._update_bg, pos=self._update_bg)

        # Set back destination
        self.set_back_destination('home')
        
        self.answer_key = None  # Will initialize after the number of questions is set
        self.logger = logging.getLogger("chexam.ui.answer_key_screen")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('[%(levelname)s] %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        # Create main content layout - vertical for mobile
        main_content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(15))
        
        # Style function for buttons
        def style_button(btn):
            btn.background_normal = ''
            btn.background_color = (0.2, 0.6, 1, 1)
            btn.color = (1, 1, 1, 1)
            btn.size_hint_y = None
            btn.height = dp(60)
            btn.width = dp(150)  # Shortened button length
            btn.font_size = dp(18)
            return btn
        
        # Create new key section
        create_section = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None, height=dp(180))
        create_label = Label(
            text="Create New Answer Key", 
            bold=True, 
            font_size=dp(20),
            size_hint_y=None,
            height=dp(40),
            color=(0.2, 0.6, 1, 1)
        )
        create_section.add_widget(create_label)
        
        # Number of questions input
        num_questions_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50))
        num_questions_label = Label(
            text="Questions:", 
            size_hint_x=0.4,
            font_size=dp(18)
        )
        self.num_questions_input = TextInput(
            hint_text="10-60", 
            multiline=False, 
            size_hint_x=0.6,
            font_size=dp(18)
        )
        self.num_questions_input.bind(on_text_validate=self.on_num_questions_entered)
        num_questions_box.add_widget(num_questions_label)
        num_questions_box.add_widget(self.num_questions_input)
        create_section.add_widget(num_questions_box)
        
        # Create button
        create_button = style_button(Button(text="Create New Key"))
        create_button.bind(on_press=self.create_answer_fields)
        create_section.add_widget(create_button)
        
        # Separator
        separator = BoxLayout(size_hint_y=None, height=dp(2))
        separator.canvas.add(Color(0.8, 0.8, 0.8, 1))
        separator.canvas.add(Rectangle(pos=separator.pos, size=separator.size))
        
        # Load existing key section
        load_section = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None, height=dp(120))
        load_label = Label(
            text="Load Existing Answer Key", 
            bold=True, 
            font_size=dp(20),
            size_hint_y=None,
            height=dp(40),
            color=(0.2, 0.6, 1, 1)
        )
        load_section.add_widget(load_label)
        
        # Load button
        load_button = style_button(Button(text="Load Existing Key"))
        load_button.bind(on_press=self.show_load_popup)
        load_section.add_widget(load_button)
        
        # Add sections to main content
        main_content.add_widget(create_section)
        main_content.add_widget(separator)
        main_content.add_widget(load_section)
        
        # Content area (will be filled dynamically)
        self.screen_content_area = BoxLayout(orientation='vertical')
        main_content.add_widget(self.screen_content_area)
        
        # Add main content to the content area from BaseScreen
        self.content_area.add_widget(main_content)

    def _update_bg(self, *args):
        self.bg_rect.size = self.size
        self.bg_rect.pos = self.pos

    def on_num_questions_entered(self, instance):
        """Handles validation when pressing enter after entering the number of questions."""
        try:
            num_questions = int(self.num_questions_input.text)
            if 10 <= num_questions <= 60:
                self.create_answer_fields(None)
            else:
                self.num_questions_input.text = ""  
                self.logger.warning("Please enter a number between 10 and 60.")
        except ValueError:
            self.num_questions_input.text = ""  
            self.logger.warning("Please enter a valid number.")

    def create_answer_fields(self, instance=None):
        """Create answer input fields dynamically based on the number of questions."""
        try:
            num_questions = int(self.num_questions_input.text)
            if not (10 <= num_questions <= 60):
                raise ValueError("Number of questions must be between 10 and 60.")

            self.answer_key = AnswerKey(num_questions)
            
            # Clear the content area
            self.screen_content_area.clear_widgets()

            # Create a header with key name input
            header = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
            name_label = Label(text="Answer Key Name:", size_hint_x=0.3)
            self.key_name_input = TextInput(hint_text="Enter a name for this answer key", multiline=False, size_hint_x=0.7)
            header.add_widget(name_label)
            header.add_widget(self.key_name_input)
            self.screen_content_area.add_widget(header)

            # Create a ScrollView to hold the dynamic question and answer widgets
            scroll_view = ScrollView(size_hint=(1, 0.8))
            content_layout = GridLayout(cols=2, spacing=10, size_hint_y=None, padding=10)
            content_layout.bind(minimum_height=content_layout.setter('height')) 

            self.inputs = []
            # Create dropdown (Spinner) for each question
            for i in range(1, num_questions + 1):
                question_label = Label(text=f"Question {i}:", size_hint_y=None, height=44)

                # Create a Spinner for multiple-choice answers
                spinner = Spinner(
                    text='Select Answer',
                    values=('A', 'B', 'C', 'D'),  
                    size_hint_y=None,
                    height=44
                )
                self.inputs.append((i, spinner))
                content_layout.add_widget(question_label)
                content_layout.add_widget(spinner)

            # Set the height of the grid layout based on the number of questions
            content_layout.height = num_questions * 50 
            
            # Add the content layout inside the scrollable area
            scroll_view.add_widget(content_layout)
            self.screen_content_area.add_widget(scroll_view)

            # Add buttons for saving and canceling
            buttons_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
            
            save_button = Button(text="Save Answer Key")
            save_button.bind(on_press=self.save_answer_key)
            
            cancel_button = Button(text="Cancel")
            cancel_button.bind(on_press=self.cancel)
            
            buttons_layout.add_widget(save_button)
            buttons_layout.add_widget(cancel_button)
            
            self.screen_content_area.add_widget(buttons_layout)
            
        except ValueError as e:
            self.logger.error(f"Error creating answer fields: {str(e)}")
            self.num_questions_input.text = ""

    def save_answer_key(self, instance):
        """Save the answers entered for each question."""
        if not self.answer_key:
            self.logger.error("No answer key to save")
            return
            
        # Get the name for the answer key
        key_name = self.key_name_input.text.strip()
        if not key_name:
            # Show error popup if no name is provided
            self.show_error_popup("Please enter a name for the answer key.")
            return
        
        # Collect answers from spinners
        for question_num, spinner in self.inputs:
            answer = spinner.text.strip().upper()  
            if answer != "SELECT ANSWER":  
                self.answer_key.add_answer(question_num, answer)
        
        # Save to database
        if self.answer_key.save_to_db(key_name):
            self.logger.info(f"Answer key '{key_name}' saved successfully")
            # Show success popup
            self.show_info_popup(f"Answer key '{key_name}' saved successfully.")
            # Go back to home screen
            self.manager.current = 'home'
        else:
            self.logger.error(f"Failed to save answer key '{key_name}'")
            self.show_error_popup(f"Failed to save answer key '{key_name}'.")
    
    def cancel(self, instance):
        """Cancel creating/editing the answer key and return to home screen."""
        self.manager.current = 'home'
    
    def show_load_popup(self, instance):
        """Show a popup with a list of existing answer keys to load."""
        # Get all answer keys from the database
        keys = AnswerKey.get_all_keys()
        
        if not keys:
            self.show_info_popup("No answer keys found in the database.")
            return
        
        # Create popup content
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Add a label
        content.add_widget(Label(text="Select an Answer Key to Load", size_hint_y=None, height=30))
        
        # Create a scrollable list of answer keys
        scroll_view = ScrollView(size_hint=(1, 0.8))
        keys_layout = GridLayout(cols=1, spacing=5, size_hint_y=None)
        keys_layout.bind(minimum_height=keys_layout.setter('height'))
        
        for key in keys:
            # Create a button for each answer key
            key_button = Button(
                text=f"{key['name']} ({key['num_questions']} questions)",
                size_hint_y=None,
                height=50
            )
            key_button.key_id = key['id']  # Store the key ID in the button
            key_button.bind(on_press=self.load_answer_key)
            keys_layout.add_widget(key_button)
        
        # Set the height of the keys layout
        keys_layout.height = len(keys) * 55  
        
        scroll_view.add_widget(keys_layout)
        content.add_widget(scroll_view)
        
        # Add a cancel button
        cancel_button = Button(text="Cancel", size_hint_y=None, height=50)
        content.add_widget(cancel_button)
        
        # Create and open the popup
        popup = Popup(title="Load Answer Key", content=content, size_hint=(0.8, 0.8))
        cancel_button.bind(on_press=popup.dismiss)
        popup.open()
    
    def load_answer_key(self, instance):
        """Load the selected answer key from the database."""
        key_id = instance.key_id
        
        # Load the answer key
        self.answer_key = AnswerKey(0)  
        if self.answer_key.load_from_db(key_id=key_id):
            self.logger.info(f"Answer key '{self.answer_key.name}' loaded successfully")
            
            # Clear the content area
            self.screen_content_area.clear_widgets()
            
            # Create a header with key name
            header = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
            name_label = Label(text="Answer Key Name:", size_hint_x=0.3)
            self.key_name_input = TextInput(text=self.answer_key.name, multiline=False, size_hint_x=0.7)
            header.add_widget(name_label)
            header.add_widget(self.key_name_input)
            self.screen_content_area.add_widget(header)
            
            # Create a ScrollView to hold the dynamic question and answer widgets
            scroll_view = ScrollView(size_hint=(1, 0.8))
            content_layout = GridLayout(cols=2, spacing=10, size_hint_y=None, padding=10)
            content_layout.bind(minimum_height=content_layout.setter('height'))
            
            self.inputs = []
            # Create dropdown (Spinner) for each question
            for i in range(1, self.answer_key.num_questions + 1):
                question_label = Label(text=f"Question {i}:", size_hint_y=None, height=44)
                
                # Create a Spinner for multiple-choice answers
                spinner = Spinner(
                    text=self.answer_key.get_answer(i) or 'Select Answer',
                    values=('A', 'B', 'C', 'D'),
                    size_hint_y=None,
                    height=44
                )
                self.inputs.append((i, spinner))
                content_layout.add_widget(question_label)
                content_layout.add_widget(spinner)
            
            # Set the height of the grid layout based on the number of questions
            content_layout.height = self.answer_key.num_questions * 50      
            
            # Add the content layout inside the scrollable area
            scroll_view.add_widget(content_layout)
            self.screen_content_area.add_widget(scroll_view)
            
            # Add buttons for saving, deleting, and canceling
            buttons_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
            
            save_button = Button(text="Save Changes")
            save_button.bind(on_press=self.save_answer_key)
            
            delete_button = Button(text="Delete Key")
            delete_button.bind(on_press=self.confirm_delete_key)
            
            cancel_button = Button(text="Cancel")
            cancel_button.bind(on_press=self.cancel)
            
            buttons_layout.add_widget(save_button)
            buttons_layout.add_widget(delete_button)
            buttons_layout.add_widget(cancel_button)
            
            self.screen_content_area.add_widget(buttons_layout)
            
            # Close the popup
            for widget in self.parent.children:
                if isinstance(widget, Popup):
                    widget.dismiss()
        else:
            self.logger.error(f"Failed to load answer key with ID {key_id}")
            self.show_error_popup(f"Failed to load answer key.")
    
    def confirm_delete_key(self, instance):
        """Show a confirmation popup before deleting an answer key."""
        if not self.answer_key or not self.answer_key.key_id:
            return
            
        # Create popup content
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Add a warning message
        content.add_widget(Label(
            text=f"Are you sure you want to delete the answer key '{self.answer_key.name}'?",
            halign='center'
        ))
        
        # Add buttons
        buttons = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        
        delete_button = Button(text="Delete", background_color=(1, 0, 0, 1))
        cancel_button = Button(text="Cancel")
        
        buttons.add_widget(delete_button)
        buttons.add_widget(cancel_button)
        
        content.add_widget(buttons)
        
        # Create and open the popup
        popup = Popup(title="Confirm Delete", content=content, size_hint=(0.8, 0.4))
        
        # Bind buttons
        delete_button.bind(on_press=lambda x: self.delete_answer_key(popup))
        cancel_button.bind(on_press=popup.dismiss)
        
        popup.open()
    
    def delete_answer_key(self, popup):
        """Delete the current answer key from the database."""
        if not self.answer_key or not self.answer_key.key_id:
            return
            
        key_id = self.answer_key.key_id
        key_name = self.answer_key.name
        
        if AnswerKey.delete_key(key_id=key_id):
            self.logger.info(f"Answer key '{key_name}' deleted successfully")
            popup.dismiss()
            self.show_info_popup(f"Answer key '{key_name}' deleted successfully.")
            self.manager.current = 'home'
        else:
            self.logger.error(f"Failed to delete answer key '{key_name}'")
            popup.dismiss()
            self.show_error_popup(f"Failed to delete answer key '{key_name}'.")
    
    def show_error_popup(self, message):
        """Show an error popup with the given message."""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=message, color=(1, 0, 0, 1)))
        
        button = Button(text="OK", size_hint_y=None, height=50)
        content.add_widget(button)
        
        popup = Popup(title="Error", content=content, size_hint=(0.8, 0.4))
        button.bind(on_press=popup.dismiss)
        popup.open()
    
    def show_info_popup(self, message):
        """Show an information popup with the given message."""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=message))
        
        button = Button(text="OK", size_hint_y=None, height=50)
        content.add_widget(button)
        
        popup = Popup(title="Information", content=content, size_hint=(0.8, 0.4))
        button.bind(on_press=popup.dismiss)
        popup.open()
