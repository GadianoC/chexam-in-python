from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.graphics import Rectangle, Color

from app.db.student_db import (
    get_all_students, add_student, delete_student,
    get_analysis_result, generate_answers_for_existing_students
)
from app.db.answer_key_db import get_all_answer_keys
from api.analyze_all import analyze_student
from .base_screen import BaseScreen

class StudentScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(title="Student Management", **kwargs)
        
        # Set background
        with self.canvas.before:
            self.bg_rect = Rectangle(source='yp.png', size=self.size, pos=self.pos)
        self.bind(size=self._update_bg, pos=self._update_bg)
        
        # Set back destination and update title color
        self.set_back_destination('home')
        self.title_label.color = (0.2, 0.6, 1, 1)  # Blue color to match buttons
        
        self.selected_student_id = None
        self.selected_answer_key_id = None
        
        # Create a simple layout structure
        layout = BoxLayout(orientation='vertical')
        
        # Create a ScrollView that will contain all our content
        scroll = ScrollView()
        
        # Create a layout that will contain all the scrollable content
        # Using a GridLayout with one column works better for scrolling
        self.container = GridLayout(cols=1, spacing=10, padding=10, size_hint_y=None)
        
        # Important: bind the height to the container's minimum height
        # This makes scrolling work properly
        self.container.bind(minimum_height=self.container.setter('height'))
        
        # We'll add widgets directly to the container instead of using a separate content layout
        
        # Style function for buttons
        def style_button(btn, primary=True):
            btn.background_normal = ''
            if primary:
                btn.background_color = (0.2, 0.6, 1, 1)
            else:
                btn.background_color = (0.6, 0.6, 0.6, 1)
            btn.color = (1, 1, 1, 1)
            btn.size_hint_y = None
            btn.height = dp(48)
            btn.font_size = dp(14)
            btn.radius = [dp(12)]  # Rounded corners for better aesthetics
            return btn
        
        # Add student section
        add_section = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(56), spacing=dp(8))
        self.student_input = TextInput(
            hint_text='Enter Student Name', 
            multiline=False, 
            size_hint_x=0.7,
            font_size=dp(14),
            padding=[dp(8), dp(8), dp(8), dp(8)]
        )
        add_btn = style_button(Button(text='Add'), primary=True)
        add_btn.size_hint_x = 0.3
        add_btn.bind(on_press=self.add_new_student)
        add_section.add_widget(self.student_input)
        add_section.add_widget(add_btn)
        
        # Student list with scroll view
        list_label = Label(
            text='Students', 
            font_size=dp(18), 
            size_hint_y=None, 
            height=dp(32),
            color=(0.2, 0.6, 1, 1),
            bold=True
        )
        
        # Student list with its own scroll view and reduced fixed height
        student_scroll = ScrollView(size_hint=(1, None), height=dp(150))
        self.student_list = GridLayout(cols=1, spacing=dp(6), size_hint_y=None, padding=dp(8))
        self.student_list.bind(minimum_height=self.student_list.setter('height'))
        student_scroll.add_widget(self.student_list)
        
        # Student management buttons
        student_buttons = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(48), spacing=dp(8))
        delete_btn = style_button(Button(text='Delete'), primary=False)
        delete_btn.size_hint_x = 0.33
        delete_btn.bind(on_press=self.delete_selected_student)
        init_btn = style_button(Button(text='Example Data'), primary=True)
        init_btn.size_hint_x = 0.33
        init_btn.bind(on_press=self.initialize_students)
        gen_answers_btn = style_button(Button(text='Gen Answers'), primary=True)
        gen_answers_btn.size_hint_x = 0.34
        gen_answers_btn.bind(on_press=self.generate_answers_for_all)
        student_buttons.add_widget(delete_btn)
        student_buttons.add_widget(init_btn)
        student_buttons.add_widget(gen_answers_btn)
        
        # Answer key section
        key_header = Label(
            text='Answer Key Selection', 
            font_size=dp(18), 
            size_hint_y=None, 
            height=dp(32),
            color=(0.2, 0.6, 1, 1),
            bold=True
        )
        key_section = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(80), spacing=dp(8))
        key_label = Label(
            text='Select Answer Key:', 
            size_hint_y=None,
            height=dp(24),
            font_size=dp(14),
            color=(0, 0, 0, 1)  # Black color for label
        )
        self.key_buttons = BoxLayout(orientation='horizontal', spacing=dp(6), size_hint_y=None, height=dp(40))
        key_section.add_widget(key_label)
        key_section.add_widget(self.key_buttons)
        
        # Analysis button
        analyze_btn = style_button(Button(text='Analyze'), primary=True)
        analyze_btn.bind(on_press=self.analyze_selected_student)
        
        # Analysis results section
        results_label = Label(
            text='Analysis Results', 
            font_size=dp(18), 
            size_hint_y=None, 
            height=dp(32),
            color=(0.2, 0.6, 1, 1),
            bold=True
        )
        
        # Results layout with its own scroll view and fixed height
        results_scroll = ScrollView(size_hint=(1, None), height=dp(300))
        self.results_layout = GridLayout(cols=1, spacing=dp(8), size_hint_y=None, size_hint_x=1, padding=dp(8))
        self.results_layout.bind(minimum_height=self.results_layout.setter('height'))
        results_scroll.add_widget(self.results_layout)
        
        # Add widgets directly to the container
        self.container.add_widget(add_section)
        self.container.add_widget(list_label)
        self.container.add_widget(student_scroll)
        self.container.add_widget(student_buttons)
        self.container.add_widget(key_header)
        self.container.add_widget(key_section)
        self.container.add_widget(analyze_btn)
        self.container.add_widget(results_label)
        self.container.add_widget(results_scroll)
        
        # Add the container to the scroll view
        scroll.add_widget(self.container)
        
        # Add the scroll view to the layout
        layout.add_widget(scroll)
        
        # Add the layout to the content area from BaseScreen
        self.content_area.add_widget(layout)
    
    def on_pre_enter(self):
        """Called before the screen is displayed."""
        self.load_students()
        self.load_answer_keys()
        self.clear_results()
        
    def refresh_student_list(self):
        """Refresh the student list - alias for load_students for backward compatibility."""
        self.load_students()
    
    def go_back(self, instance):
        """Navigate back to home screen."""
        self.manager.current = 'home'
    
    def load_students(self):
        """Load all students into the student list."""
        self.student_list.clear_widgets()
        students = get_all_students()
        
        if not students:
            self.student_list.add_widget(Label(
                text='No students found. Add students or initialize example data.',
                size_hint_y=None, height=dp(40)
            ))
            return
        
        for student in students:
            # Create a styled button for each student
            btn = Button(
                text=student['name'],
                size_hint_y=None,
                height=dp(60),
                background_normal='',
                background_color=(0.9, 0.9, 0.9, 1),
                color=(0, 0, 0, 1),
                font_size=dp(18),
                halign='center'
            )
            btn.student_id = student['id']
            btn.bind(on_press=self.select_student)
            self.student_list.add_widget(btn)
    
    def load_answer_keys(self):
        """Load all answer keys into the key selection area."""
        self.key_buttons.clear_widgets()
        answer_keys = get_all_answer_keys()
        
        if not answer_keys:
            self.key_buttons.add_widget(Label(
                text='No answer keys found. Please create an answer key first.',
                size_hint_x=1
            ))
            return
        
        for key in answer_keys:
            btn = Button(text=key['name'])
            btn.answer_key_id = key['id']
            btn.bind(on_press=self.select_answer_key)
            self.key_buttons.add_widget(btn)
        
        # Select the first answer key by default
        self.selected_answer_key_id = answer_keys[0]['id']
    
    def select_student(self, instance):
        """Handle student selection."""
        # Deselect all buttons
        for child in self.student_list.children:
            if isinstance(child, Button):
                child.background_color = (1, 1, 1, 1)
        
        # Select the clicked button
        instance.background_color = (0.5, 0.8, 1, 1)
        self.selected_student_id = instance.student_id
        
        # Load analysis results if available
        if self.selected_student_id and self.selected_answer_key_id:
            self.load_analysis_results()
    
    def select_answer_key(self, instance):
        """Handle answer key selection."""
        # Deselect all buttons
        for child in self.key_buttons.children:
            if isinstance(child, Button):
                child.background_color = (1, 1, 1, 1)
        
        # Select the clicked button
        instance.background_color = (0.5, 0.8, 1, 1)
        self.selected_answer_key_id = instance.answer_key_id
        
        # Load analysis results if available
        if self.selected_student_id and self.selected_answer_key_id:
            self.load_analysis_results()
    
    def add_new_student(self, instance):
        """Add a new student to the database."""
        name = self.student_input.text.strip()
        if not name:
            self.show_popup('Error', 'Please enter a student name.')
            return
        
        student_id = add_student(name)
        if student_id:
            self.student_input.text = ''
            self.load_students()
            self.show_popup('Success', f'Student "{name}" added successfully.')
        else:
            self.show_popup('Error', f'Failed to add student "{name}". The name may already exist.')
    
    def delete_selected_student(self, instance):
        """Delete the selected student from the database."""
        if not self.selected_student_id:
            self.show_popup('Error', 'Please select a student to delete.')
            return
        
        # Find the student name
        student_name = None
        for child in self.student_list.children:
            if isinstance(child, Button) and hasattr(child, 'student_id') and child.student_id == self.selected_student_id:
                student_name = child.text
                break
        
        if delete_student(student_id=self.selected_student_id):
            self.selected_student_id = None
            self.load_students()
            self.clear_results()
            self.show_popup('Success', f'Student "{student_name}" deleted successfully.')
        else:
            self.show_popup('Error', 'Failed to delete student.')
    
    def initialize_students(self, instance):
        """Initialize example student data."""
        from api.init_students import initialize_students
        
        if initialize_students():
            self.load_students()
            self.show_popup('Success', '30 example students initialized successfully.')
        else:
            self.show_popup('Error', 'Failed to initialize example students. Make sure you have at least one answer key.')
    
    def generate_answers_for_all(self, instance):
        """Generate answers for all existing students for all answer keys."""
        # Show loading popup
        loading_popup = Popup(
            title='Generating Answers',
            content=Label(text='Generating answers for all students... This may take a moment.'),
            size_hint=(0.6, 0.3)
        )
        loading_popup.open()
        
        # Generate answers for all existing students
        success = generate_answers_for_existing_students()
        
        # Close loading popup
        loading_popup.dismiss()
        
        if success:
            self.show_popup('Success', 'Generated answers for all students for all answer keys.')
        else:
            self.show_popup('Error', 'Failed to generate answers. Make sure you have at least one answer key.')
    
    def analyze_selected_student(self, instance):
        """Analyze the selected student's answers."""
        if not self.selected_student_id:
            self.show_popup('Error', 'Please select a student to analyze.')
            return
        
        if not self.selected_answer_key_id:
            self.show_popup('Error', 'Please select an answer key.')
            return
        
        # Show loading popup
        loading_popup = Popup(
            title='Analyzing',
            content=Label(text='Analyzing student answers...\nThis may take a moment.'),
            size_hint=(0.6, 0.3)
        )
        loading_popup.open()
        
        # Analyze student
        result = analyze_student(self.selected_student_id, self.selected_answer_key_id)
        
        # Close loading popup
        loading_popup.dismiss()
        
        if result:
            self.load_analysis_results()
            self.show_popup('Success', 'Analysis complete!')
        else:
            self.show_popup('Error', 'Failed to analyze student answers.')
    
    def load_analysis_results(self):
        """Load analysis results for the selected student and answer key."""
        self.clear_results()
        
        if not self.selected_student_id or not self.selected_answer_key_id:
            return
        
        # Get analysis results
        result = get_analysis_result(self.selected_student_id, self.selected_answer_key_id)
        if not result:
            self.results_layout.add_widget(Label(
                text='No analysis results found. Click "Analyze Selected Student" to analyze.',
                size_hint_y=None, height=dp(40)
            ))
            return
        
        # Get student answers and correct answers for displaying choices
        from app.db.student_db import get_student_answers
        from app.db.answer_key_db import get_answer_key_answers
        
        # Both functions now return dictionaries directly
        student_answers = get_student_answers(self.selected_student_id, self.selected_answer_key_id)
        correct_answers = get_answer_key_answers(self.selected_answer_key_id)
        
        # Make sure we have valid dictionaries
        if student_answers is None:
            student_answers = {}
        if correct_answers is None:
            correct_answers = {}
        
        # Display results with larger, more visible text for score and percentage
        # Create special score display with more height and better formatting
        score_container = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(100), padding=[0, 10, 0, 10])
        score_label = Label(
            text=f"[b]Score:[/b] [color=00BFFF][size=32]{result['score']}[/size][/color]",
            markup=True,
            halign='center',
            valign='middle',
            size_hint=(1, 1),
            color=(1, 1, 1, 1)
        )
        score_container.add_widget(score_label)
        self.results_layout.add_widget(score_container)
        
        # Create special percentage display with more height and better formatting
        percentage_container = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(100), padding=[0, 10, 0, 10])
        percentage_label = Label(
            text=f"[b]Percentage:[/b] [color=00BFFF][size=32]{result['percentage']}%[/size][/color]",
            markup=True,
            halign='center',
            valign='middle',
            size_hint=(1, 1),
            color=(1, 1, 1, 1)
        )
        percentage_container.add_widget(percentage_label)
        self.results_layout.add_widget(percentage_container)
        
        # Add a larger spacer after the score and percentage
        spacer = BoxLayout(size_hint_y=None, height=dp(20))
        self.results_layout.add_widget(spacer)
        
        # Format correct questions with answer choices - simplified format
        correct_items = []
        for q in result.get('correct_indices', []):
            if student_answers and str(q) in student_answers:
                answer_choice = student_answers.get(str(q))
                correct_items.append(f"{q}({answer_choice})")
            else:
                correct_items.append(str(q))
        correct_str = ', '.join(correct_items)
        
        # Format wrong questions with answer choices - simplified format
        wrong_items = []
        for q in result.get('wrong_indices', []):
            if student_answers and str(q) in student_answers:
                student_choice = student_answers.get(str(q), '?')
                wrong_items.append(f"{q}({student_choice})")
            else:
                wrong_items.append(str(q))
        wrong_str = ', '.join(wrong_items)
        
        # Calculate appropriate heights based on content length with better minimums and more space
        correct_height = max(dp(150), min(dp(250), dp(100 + len(correct_str) // 15 * 15)))
        wrong_height = max(dp(150), min(dp(250), dp(100 + len(wrong_str) // 15 * 15)))
        
        # Text sections need more height for better readability
        strengths_height = max(dp(180), min(dp(300), dp(120 + len(result['strengths']) // 40 * 20)))
        weaknesses_height = max(dp(180), min(dp(300), dp(120 + len(result['weaknesses']) // 40 * 20)))
        suggestions_height = max(dp(180), min(dp(300), dp(120 + len(result['suggestions']) // 40 * 20)))
        
        # Add items with calculated heights
        self.add_result_item('Correct Questions', correct_str, correct_height)
        self.add_result_item('Wrong Questions', wrong_str, wrong_height)
        
        # Strengths, weaknesses, and suggestions with more space
        self.add_result_item('Strengths', result['strengths'], strengths_height)
        self.add_result_item('Weaknesses', result['weaknesses'], weaknesses_height)
        self.add_result_item('Suggestions', result['suggestions'], suggestions_height)
    def add_result_item(self, title, content, height):
        """Add an item to the results layout with proper containment."""
        # Create a container with border and background for better separation
        container = BoxLayout(orientation='vertical', 
                             size_hint_y=None, 
                             height=height, 
                             size_hint_x=1,
                             padding=[dp(10), dp(10), dp(10), dp(10)])
        
        # Bind the position and size for proper background drawing
        def update_rect(instance, value):
            instance.rect.pos = instance.pos
            instance.rect.size = instance.size
            
        # Add a background that updates with the container
        with container.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(0.15, 0.15, 0.15, 0.1)  # Slightly visible background for better readability
            container.rect = Rectangle(pos=container.pos, size=container.size)
            
        container.bind(pos=update_rect, size=update_rect)
            
        # Inner layout for content
        item = BoxLayout(orientation='vertical', size_hint=(1, 1))
        
        # Title label with accent color
        title_label = Label(
            text=f'[b]{title}:[/b]',
            markup=True,
            halign='left',
            valign='middle',
            size_hint_y=None,
            height=dp(30),
            color=(0.2, 0.6, 1, 1)  # Blue accent color
        )
        title_label.bind(size=title_label.setter('text_size'))
        item.add_widget(title_label)
        
        # Content in a scroll view to prevent overflow
        scroll_view = ScrollView(size_hint=(1, 1))
        
        # Content layout with proper background
        content_layout = BoxLayout(orientation='vertical', size_hint_y=None)
        content_layout.bind(minimum_height=content_layout.setter('height'))
        
        # Content label with proper text wrapping and black color
        content_label = Label(
            text=str(content),
            halign='left',
            valign='top',
            size_hint_y=None,
            text_size=(None, None),
            color=(1, 1, 1, 1)  # White color for better visibility
        )
        
        # Make sure text wraps properly with better padding
        content_label.bind(width=lambda *x: content_label.setter('text_size')(content_label, (content_label.width - dp(20), None)))
        content_label.bind(texture_size=content_label.setter('size'))
        content_label.padding = [dp(10), dp(10)]
        content_label.font_size = dp(16)  # Larger font for better readability
        
        # Add content label to content layout
        content_layout.add_widget(content_label)
        scroll_view.add_widget(content_layout)
        item.add_widget(scroll_view)
        
        # Add item to container and container to results layout
        container.add_widget(item)
        self.results_layout.add_widget(container)
        
        # Add a larger spacer after each item for better separation
        spacer = BoxLayout(size_hint_y=None, height=dp(15))
        self.results_layout.add_widget(spacer)
    
    def clear_results(self):
        """Clear analysis results."""
        self.results_layout.clear_widgets()
    
    def show_popup(self, title, message):
        """Show a popup with the given title and message."""
        popup = Popup(
            title=title,
            content=Label(text=message),
            size_hint=(0.6, 0.3)
        )
        popup.open()

    def _update_bg(self, *args):
        """Update the background rectangle size and position."""
        self.bg_rect.size = self.size
        self.bg_rect.pos = self.pos
