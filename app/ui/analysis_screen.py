from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup

# Dummy functions to simulate analysis
def init_db():
    print("Database initialized.")

def load_txt_answers(folder_path, correct_answers):
    print(f"Loaded answers from {folder_path} with correct answers: {correct_answers}")

def analyze_all_students():
    print("Analysis complete.")

CORRECT_ANSWERS = ['A', 'B', 'C', 'D', 'A', 'B', 'C']

class AnalysisScreen(Screen):
    def __init__(self, switch_to_home, **kwargs):
        super().__init__(**kwargs)

        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)

        title = Label(text='[b]Student Analysis[/b]', markup=True, font_size=24)
        layout.add_widget(title)

        init_btn = Button(text='Initialize Database')
        init_btn.bind(on_press=self.handle_init_db)
        layout.add_widget(init_btn)

        load_btn = Button(text='Load Student Answers')
        load_btn.bind(on_press=self.handle_load_answers)
        layout.add_widget(load_btn)

        analyze_btn = Button(text='Run Analysis')
        analyze_btn.bind(on_press=self.handle_analyze)
        layout.add_widget(analyze_btn)

        back_btn = Button(text='Back to Home')
        back_btn.bind(on_press=lambda instance: switch_to_home())
        layout.add_widget(back_btn)

        self.add_widget(layout)

    def show_popup(self, message):
        popup = Popup(title='Info',
                      content=Label(text=message),
                      size_hint=(None, None), size=(300, 200))
        popup.open()

    def handle_init_db(self, instance):
        init_db()
        self.show_popup("Database initialized.")

    def handle_load_answers(self, instance):
        load_txt_answers("student_txts", CORRECT_ANSWERS)
        self.show_popup("Answers loaded.")

    def handle_analyze(self, instance):
        analyze_all_students()
        self.show_popup("Analysis complete.")

