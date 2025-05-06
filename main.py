from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from app.ui.home_screen import HomeScreen
from app.ui.scanner_screen import ScannerScreen
from app.ui.processed_image_screen import ProcessedImageScreen
from app.ui.answer_key_screen import AnswerKeyScreen  # Import the AnswerKeyScreen

class BubbleScannerApp(App):
    def build(self):
        sm = ScreenManager()

        # Create navigation functions
        def go_to_scanner():
            sm.current = 'scanner'

        def go_to_answer_key():
            sm.current = 'answer_key'

        sm.add_widget(HomeScreen(name='home', switch_to_scanner=go_to_scanner, go_to_answer_key=go_to_answer_key))
        sm.add_widget(ScannerScreen(name='scanner'))
        sm.add_widget(ProcessedImageScreen(name='processed_image'))
        sm.add_widget(AnswerKeyScreen(name='answer_key'))  # Add AnswerKeyScreen

        sm.current = 'home'  # Start at HomeScreen
        return sm

if __name__ == '__main__':
    BubbleScannerApp().run()
