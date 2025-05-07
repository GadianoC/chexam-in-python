from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from app.ui.home_screen import HomeScreen
from app.ui.scanner_screen import ScannerScreen
from app.ui.processed_image_screen import ProcessedImageScreen
from app.ui.answer_key_screen import AnswerKeyScreen
from app.ui.analysis_screen import AnalysisScreen  # Make sure to import

class BubbleScannerApp(App):
    def build(self):
        sm = ScreenManager()

        # Navigation functions
        def go_to_scanner():
            sm.current = 'scanner'

        def go_to_answer_key():
            sm.current = 'answer_key'

        def go_to_home():
            sm.current = 'home'

        def go_to_analysis():
            sm.current = 'analysis'

        # Add screens
        sm.add_widget(ScannerScreen(name='scanner', switch_to_home=go_to_home))
        sm.add_widget(HomeScreen(name='home',
                                 switch_to_scanner=go_to_scanner,
                                 switch_to_answer_key=go_to_answer_key,
                                 switch_to_analysis=go_to_analysis))
        sm.add_widget(ProcessedImageScreen(name='processed_image'))
        sm.add_widget(AnswerKeyScreen(name='answer_key'))
        sm.add_widget(AnalysisScreen(name='analysis', switch_to_home=go_to_home))  # Add this

        sm.current = 'home'
        return sm

if __name__ == '__main__':
    BubbleScannerApp().run()
