from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.graphics import Rectangle, Color

from app.db.answer_key_db import get_all_answer_keys, get_answer_key
from api.analyze_all import analyze_class
from .base_screen import BaseScreen

class AnalysisScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(title="Class Analysis", **kwargs)
        
        # Set yellow pad background
        with self.canvas.before:
            self.bg_rect = Rectangle(source='yellow pad.jpg', size=self.size, pos=self.pos)
        self.bind(size=self._update_bg, pos=self._update_bg)
        
        # Set back destination and update title color
        self.set_back_destination('home')
        self.title_label.color = (0.2, 0.6, 1, 1)  # Blue color to match buttons
        
        self.selected_answer_key_id = None
        self.class_analysis_result = None
        
        # Create main content layout
        main_content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(15), size_hint=(1, 1))
        
        # Create a ScrollView to make the entire screen scrollable for mobile
        main_scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        
        # Content area
        content = BoxLayout(orientation='vertical', spacing=dp(10))
        
        # Style function for buttons
        def style_button(btn, primary=True):
            btn.background_normal = ''
            if primary:
                btn.background_color = (0.2, 0.6, 1, 1)
            else:
                btn.background_color = (0.6, 0.6, 0.6, 1)
            btn.color = (1, 1, 1, 1)
            btn.size_hint_y = None
            btn.height = dp(60)
            btn.font_size = dp(18)
            return btn
        
        # Answer key selection header
        key_header = Label(
            text='Answer Key Selection', 
            font_size=dp(20), 
            size_hint_y=None, 
            height=dp(40),
            color=(0.2, 0.6, 1, 1),
            bold=True
        )
        
        # Answer key selection and analyze button
        controls = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(150), spacing=dp(10))
        
        # Answer key selection
        key_section = BoxLayout(orientation='vertical', size_hint_x=0.7)
        key_label = Label(
            text='Select Answer Key:', 
            size_hint_y=None,
            height=dp(30),
            font_size=dp(16)
        )
        
        # Grid for answer key buttons with multiple columns
        self.key_buttons = GridLayout(cols=3, spacing=dp(10), size_hint_y=None, height=dp(100))
        self.key_buttons.bind(minimum_height=self.key_buttons.setter('height'))
        
        key_section.add_widget(key_label)
        key_section.add_widget(self.key_buttons)
        
        # Analyze button
        analyze_btn = style_button(Button(text='Analyze All Students'))
        analyze_btn.size_hint_x = 0.3
        analyze_btn.bind(on_press=self.analyze_class)
        
        # Add both sections to controls
        controls.add_widget(key_section)
        controls.add_widget(analyze_btn)
        
        # Analysis results header
        results_label = Label(
            text='Class Analysis Results', 
            font_size=dp(20), 
            size_hint_y=None, 
            height=dp(40),
            color=(0.2, 0.6, 1, 1),
            bold=True
        )
        
        # Scrollable results view
        results_scroll = ScrollView(size_hint_y=0.8)
        self.results_layout = GridLayout(cols=1, spacing=dp(10), size_hint_y=None, size_hint_x=1, padding=dp(10))
        self.results_layout.bind(minimum_height=self.results_layout.setter('height'))
        results_scroll.add_widget(self.results_layout)
        
        # Add all sections to content
        content.add_widget(controls)
        content.add_widget(results_label)
        content.add_widget(results_scroll)
        
        # Add content to main content layout
        main_content.add_widget(content)
        
        # Add main content to the scroll view
        main_scroll.add_widget(main_content)
        
        # Add scroll view to the content area from BaseScreen
        self.content_area.add_widget(main_scroll)
    
    def on_pre_enter(self):
        """Called before the screen is displayed."""
        self.load_answer_keys()
        self.clear_results()
    
    def go_back(self, instance):
        """Navigate back to home screen."""
        self.manager.current = 'home'
    
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
    
    def select_answer_key(self, instance):
        """Handle answer key selection."""
        # Deselect all buttons
        for child in self.key_buttons.children:
            if isinstance(child, Button):
                child.background_color = (1, 1, 1, 1)
        
        # Select the clicked button
        instance.background_color = (0.5, 0.8, 1, 1)
        self.selected_answer_key_id = instance.answer_key_id
    
    def analyze_class(self, instance):
        """Analyze all students for the selected answer key."""
        if not self.selected_answer_key_id:
            self.show_popup('Error', 'Please select an answer key.')
            return
        
        # Show loading popup
        loading_popup = Popup(
            title='Analyzing',
            content=Label(text='Analyzing all students...\nThis may take a moment.'),
            size_hint=(0.6, 0.3)
        )
        loading_popup.open()
        
        # Analyze class
        result = analyze_class(self.selected_answer_key_id)
        
        # Close loading popup
        loading_popup.dismiss()
        
        if result:
            self.class_analysis_result = result
            self.display_class_analysis()
            self.show_popup('Success', 'Class analysis complete!')
        else:
            self.show_popup('Error', 'Failed to analyze class. Make sure students have been added and analyzed.')
    
    def display_class_analysis(self):
        """Display class analysis results."""
        self.clear_results()
        
        if not self.class_analysis_result:
            self.results_layout.add_widget(Label(
                text='No analysis results found. Click "Analyze All Students" to analyze.',
                size_hint_y=None, height=dp(40)
            ))
            return
        
        # Get answer key name
        answer_key = get_answer_key(key_id=self.selected_answer_key_id)
        answer_key_name = answer_key['name'] if answer_key else 'Unknown Answer Key'
        
        # Add title
        self.results_layout.add_widget(Label(
            text=f'[b]Analysis for {answer_key_name}[/b]',
            markup=True,
            size_hint_y=None, 
            height=dp(40),
            color=(0, 0, 0, 1)  # Black color for the title
        ))
        
        # Display overall statistics
        stats_grid = GridLayout(cols=2, spacing=10, size_hint_y=None, height=dp(160))
        
        # Class average
        stats_grid.add_widget(Label(
            text='[b]Class Average:[/b]',
            markup=True,
            halign='right',
            color=(0, 0, 0, 1)  # Black color
        ))
        stats_grid.add_widget(Label(
            text=f"{self.class_analysis_result.get('class_average', 0)}%",
            halign='left',
            color=(0, 0, 0, 1)  # Black color
        ))
        
        # Passing rate
        stats_grid.add_widget(Label(
            text='[b]Passing Rate (≥60%):[/b]',
            markup=True,
            halign='right',
            color=(0, 0, 0, 1)  # Black color
        ))
        stats_grid.add_widget(Label(
            text=f"{self.class_analysis_result.get('passing_rate', 0)}%",
            halign='left',
            color=(0, 0, 0, 1)  # Black color
        ))
        
        # Highest score
        stats_grid.add_widget(Label(
            text='[b]Highest Score:[/b]',
            markup=True,
            halign='right',
            color=(0, 0, 0, 1)  # Black color
        ))
        stats_grid.add_widget(Label(
            text=f"{self.class_analysis_result.get('highest_score', 0)}%",
            halign='left',
            color=(0, 0, 0, 1)  # Black color
        ))
        
        # Lowest score
        stats_grid.add_widget(Label(
            text='[b]Lowest Score:[/b]',
            markup=True,
            halign='right',
            color=(0, 0, 0, 1)  # Black color
        ))
        stats_grid.add_widget(Label(
            text=f"{self.class_analysis_result.get('lowest_score', 0)}%",
            halign='left',
            color=(0, 0, 0, 1)  # Black color
        ))
        
        self.results_layout.add_widget(stats_grid)
        
        # Get correct answers for displaying choices
        from app.db.answer_key_db import get_answer_key_answers
        correct_answers = get_answer_key_answers(self.selected_answer_key_id)
        
        # Make sure we have a valid dictionary
        if correct_answers is None:
            correct_answers = {}
        
        # Most missed questions with answer choices - simplified format
        missed_questions = self.class_analysis_result.get('most_missed_questions', [])
        missed_items = []
        for q in missed_questions:
            if str(q) in correct_answers:
                correct_choice = correct_answers.get(str(q), '?')
                missed_items.append(f"{q}({correct_choice})")
            else:
                missed_items.append(str(q))
        missed_str = ', '.join(missed_items) if missed_items else 'None'
        missed_height = max(dp(60), min(dp(120), dp(40 + len(missed_str) // 30 * 20)))
        self.add_result_item('Most Missed Questions', missed_str, missed_height)
        
        # Best understood questions with answer choices - simplified format
        best_questions = self.class_analysis_result.get('best_understood_questions', [])
        best_items = []
        for q in best_questions:
            if str(q) in correct_answers:
                correct_choice = correct_answers.get(str(q), '?')
                best_items.append(f"{q}({correct_choice})")
            else:
                best_items.append(str(q))
        best_str = ', '.join(best_items) if best_items else 'None'
        best_height = max(dp(60), min(dp(120), dp(40 + len(best_str) // 30 * 20)))
        self.add_result_item('Best Understood Questions', best_str, best_height)
        
        # Class strengths, weaknesses, and teaching suggestions
        self.add_result_item('Class Strengths', 
                           self.class_analysis_result.get('class_strengths', 'No data'), 
                           dp(80))
        self.add_result_item('Class Weaknesses', 
                           self.class_analysis_result.get('class_weaknesses', 'No data'), 
                           dp(80))
        self.add_result_item('Teaching Suggestions', 
                           self.class_analysis_result.get('teaching_suggestions', 'No data'), 
                           dp(80))
    
    def add_result_item(self, title, content, height):
        """Add an item to the results layout."""
        item = BoxLayout(orientation='vertical', size_hint_y=None, height=height, size_hint_x=1)
        
        # Title label
        title_label = Label(
            text=f'[b]{title}:[/b]',
            markup=True,
            halign='left',
            valign='middle',
            size_hint_y=0.3,
            size_hint_x=1,
            color=(0, 0, 0, 1)  # Black color
        )
        title_label.bind(size=title_label.setter('text_size'))
        item.add_widget(title_label)
        
        # Content label with proper text wrapping
        content_label = Label(
            text=str(content),
            halign='left',
            valign='top',
            size_hint_y=0.7,
            size_hint_x=1,
            color=(0, 0, 0, 1)  # Black color
        )
        content_label.bind(width=lambda *x: content_label.setter('text_size')(content_label, (content_label.width, None)))
        item.add_widget(content_label)
        
        self.results_layout.add_widget(item)
    
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