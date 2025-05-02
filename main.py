from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from app.ui.home_screen import HomeScreen
from app.ui.scanner_screen import ScannerScreen
from app.ui.processed_image_screen import ProcessedImageScreen

class BubbleScannerApp(App):
    def build(self):
        sm = ScreenManager()
        # Navigation function
        def go_to_scanner():
            sm.current = 'scanner'
        sm.add_widget(HomeScreen(name='home', switch_to_scanner=go_to_scanner))
        sm.add_widget(ScannerScreen(name='scanner'))
        sm.add_widget(ProcessedImageScreen(name='processed_image'))
        sm.current = 'home'
        return sm

if __name__ == '__main__':
    BubbleScannerApp().run()
