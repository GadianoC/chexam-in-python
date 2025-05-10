from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from app.ui.home_screen import HomeScreen
from app.ui.scanner_screen import ScannerScreen
from app.ui.processed_image_screen import ProcessedImageScreen
from app.ui.answer_key_screen import AnswerKeyScreen
from app.ui.student_screen import StudentScreen
from app.ui.analysis_screen import AnalysisScreen
from app.ui.settings_screen import SettingsScreen

class BubbleScannerApp(App):
    def build(self):
        sm = ScreenManager()

        # Create navigation functions
        def go_to_scanner():
            sm.current = 'scanner'

        def go_to_answer_key():
            sm.current = 'answer_key'
            
        def go_to_students():
            sm.current = 'students'
            
        def go_to_analysis():
            sm.current = 'analysis'
            
        def go_to_settings():
            sm.current = 'settings'

        # Add all screens to the screen manager
        sm.add_widget(HomeScreen(
            name='home', 
            switch_to_scanner=go_to_scanner, 
            go_to_answer_key=go_to_answer_key,
            go_to_students=go_to_students,
            go_to_analysis=go_to_analysis,
            go_to_settings=go_to_settings
        ))
        
        # Add other screens with proper back functionality
        scanner_screen = ScannerScreen(name='scanner')
        processed_image_screen = ProcessedImageScreen(name='processed_image')
        answer_key_screen = AnswerKeyScreen(name='answer_key')
        student_screen = StudentScreen(name='students')
        analysis_screen = AnalysisScreen(name='analysis')
        settings_screen = SettingsScreen(name='settings')
        
        # Set back destinations for all screens
        scanner_screen.set_back_destination('home')
        processed_image_screen.set_back_destination('scanner')
        answer_key_screen.set_back_destination('home')
        student_screen.set_back_destination('home')
        analysis_screen.set_back_destination('home')
        settings_screen.set_back_destination('home')
        
        # Add all screens to screen manager
        sm.add_widget(scanner_screen)
        sm.add_widget(processed_image_screen)
        sm.add_widget(answer_key_screen)
        sm.add_widget(student_screen)
        sm.add_widget(analysis_screen)
        sm.add_widget(settings_screen)

        sm.current = 'home'  # Start at HomeScreen
        return sm

if __name__ == '__main__':
    BubbleScannerApp().run()
