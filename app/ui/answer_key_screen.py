from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput  # Ensure to import TextInput
from kivy.uix.scrollview import ScrollView  # Import ScrollView
from app.ui.answer_key import AnswerKey  # Import AnswerKey class

class AnswerKeyScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.answer_key = None  # Will initialize after the number of questions is set

        layout = BoxLayout(orientation='vertical', padding=40, spacing=20)

        # Label and input for the number of questions
        num_questions_label = Label(text="Enter number of exam questions (between 10 and 100):")
        self.num_questions_input = TextInput(hint_text="Enter number", multiline=False)
        self.num_questions_input.bind(on_text_validate=self.on_num_questions_entered)

        layout.add_widget(num_questions_label)
        layout.add_widget(self.num_questions_input)

        # Button to proceed with the specified number of questions
        proceed_button = Button(text="Proceed")
        proceed_button.bind(on_press=self.create_answer_fields)
        layout.add_widget(proceed_button)

        self.add_widget(layout)

    def on_num_questions_entered(self, instance):
        """Handles validation when pressing enter after entering the number of questions."""
        try:
            num_questions = int(self.num_questions_input.text)
            if 10 <= num_questions <= 100:
                self.create_answer_fields(num_questions)
            else:
                self.num_questions_input.text = ""  # Clear input if it's out of range
                print("Please enter a number between 10 and 100.")
        except ValueError:
            self.num_questions_input.text = ""  # Clear input if invalid value is entered

    def create_answer_fields(self, instance=None):
        """Create answer input fields dynamically based on the number of questions."""
        try:
            num_questions = int(self.num_questions_input.text)
            if not (10 <= num_questions <= 100):
                raise ValueError("Number of questions must be between 10 and 100.")

            self.answer_key = AnswerKey(num_questions)
            self.clear_widgets()  # Clear previous widgets

            # Create a ScrollView to hold the dynamic question and answer widgets
            scroll_view = ScrollView(size_hint=(1, None), height=600)  # Increase height for better scrolling
            content_layout = BoxLayout(orientation='vertical', size_hint_y=None, padding=10, spacing=10)
            content_layout.bind(minimum_height=content_layout.setter('height'))  # Ensures the layout height adjusts

            self.inputs = []
            # Create dropdown (Spinner) for each question
            for i in range(1, num_questions + 1):
                question_label = Label(text=f"Select answer for Question {i}:")

                # Create a Spinner for multiple-choice answers
                spinner = Spinner(
                    text='Select Answer',
                    values=('A', 'B', 'C', 'D'),  # You can modify this list with your own options
                    size_hint=(None, None),
                    size=(200, 44),
                    pos_hint={'center_x': 0.5}
                )
                self.inputs.append((i, spinner))
                content_layout.add_widget(question_label)
                content_layout.add_widget(spinner)

            save_button = Button(text="Save Answer Key", size_hint_y=None, height=50)
            save_button.bind(on_press=self.save_answer_key)
            content_layout.add_widget(save_button)

            # Add the content layout inside the scrollable area
            scroll_view.add_widget(content_layout)

            # Add the ScrollView to the main layout
            self.add_widget(scroll_view)
        except ValueError:
            self.num_questions_input.text = ""

    def save_answer_key(self, instance):
        """Save the answers entered for each question."""
        if self.answer_key:
            for question_num, spinner in self.inputs:
                answer = spinner.text.strip().upper()  # Clean and standardize input
                if answer != "Select Answer":  # Avoid saving the default text
                    self.answer_key.add_answer(question_num, answer)

            print("Answer key saved.")
            self.manager.current = 'home'  # After saving, go back to the home screen
