from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.graphics.texture import Texture
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
import numpy as np
import cv2
import logging
import time
import os
from ..processing.answer_detection import detect_bubbles
from ..processing.ocr_processing import extract_text, extract_text_blocks, process_document_with_ocr

class ProcessedImageScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logger = logging.getLogger("chexam.ui.processed_image_screen")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('[%(levelname)s] %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            
        # Main layout
        self.layout = BoxLayout(orientation='vertical', spacing=5, padding=5)
        
        # Top section with image and results
        self.top_section = BoxLayout(orientation='horizontal', size_hint_y=0.85)
        
        # Image widget on the left
        self.image_widget = Image(size_hint_x=0.7, allow_stretch=True, keep_ratio=True)
        
        # Results panel on the right
        self.results_panel = BoxLayout(orientation='vertical', size_hint_x=0.3, padding=5)
        self.results_label = Label(text='Detected Answers', size_hint_y=0.1, font_size=18, bold=True)
        
        # Scrollable results grid
        self.scroll_view = ScrollView(size_hint_y=0.9)
        self.results_grid = GridLayout(cols=2, spacing=10, size_hint_y=None)
        self.results_grid.bind(minimum_height=self.results_grid.setter('height'))
        self.scroll_view.add_widget(self.results_grid)
        
        self.results_panel.add_widget(self.results_label)
        self.results_panel.add_widget(self.scroll_view)
        
        self.top_section.add_widget(self.image_widget)
        self.top_section.add_widget(self.results_panel)
        
        # Controls for rotate/save/analyze
        self.controls = BoxLayout(orientation='horizontal', size_hint_y=0.1, spacing=10)
        self.rotate_left_btn = Button(text='⟲ Rotate Left')
        self.rotate_right_btn = Button(text='⟳ Rotate Right')
        self.save_btn = Button(text='💾 Save')
        self.analyze_btn = Button(text='🔍 Analyze Answers')
        self.extract_content_btn = Button(text='📝 Extract Content')
        
        self.rotate_left_btn.bind(on_press=self.rotate_left)
        self.rotate_right_btn.bind(on_press=self.rotate_right)
        self.save_btn.bind(on_press=self.save_image)
        self.analyze_btn.bind(on_press=self.analyze_answers)
        self.extract_content_btn.bind(on_press=self.extract_document_content)
        
        self.controls.add_widget(self.rotate_left_btn)
        self.controls.add_widget(self.rotate_right_btn)
        self.controls.add_widget(self.save_btn)
        self.controls.add_widget(self.analyze_btn)
        self.controls.add_widget(self.extract_content_btn)
        
        # Back button
        self.back_btn = Button(text='Back to Scanner', size_hint_y=0.05)
        self.back_btn.bind(on_press=self.on_back)
        
        # Add all sections to main layout
        self.layout.add_widget(self.top_section)
        self.layout.add_widget(self.controls)
        self.layout.add_widget(self.back_btn)
        
        self.add_widget(self.layout)
        
        # State variables
        self.on_back_callback = None
        self.current_image = None
        self.current_color_image = None  # Store color version for analysis
        self.current_binary_image = None  # Store binary version for analysis
        self.rotation = 0  # 0, 1, 2, 3 (number of 90 deg rotations)
        self.detected_answers = {}

    def set_image(self, binary_img, color_img=None):
        # binary_img: numpy array, shape (H, W), dtype=uint8 - binary/thresholded image optimized for bubble detection
        if binary_img is None:
            return
            
        # Store both binary and color versions for analysis
        self.current_binary_image = binary_img.copy()
        
        # Store color image if provided, otherwise convert grayscale to color
        if color_img is not None:
            self.current_color_image = color_img.copy()
        else:
            # Convert binary to BGR for display
            self.current_color_image = cv2.cvtColor(binary_img, cv2.COLOR_GRAY2BGR)
            
        # Always use the binary image for display since we're focusing on bubble detection
        self.current_image = self.current_binary_image
        self.rotation = 0
        
        # Update the image display
        self._show_image()
        
        # Clear previous results
        self.results_grid.clear_widgets()
        self.detected_answers = {}

    def _show_image(self):
        if self.current_image is None:
            return
            
        # Apply rotation if needed
        img_np = np.rot90(self.current_image, self.rotation)
        
        # Convert to texture
        if len(img_np.shape) == 2:  # Grayscale
            # For grayscale images, apply a colormap to better visualize bubble shading
            img_np = cv2.applyColorMap(img_np, cv2.COLORMAP_BONE)
            img_np = img_np[..., ::-1]
        elif len(img_np.shape) == 3 and img_np.shape[2] == 3: 
            img_np = img_np[..., ::-1]
            
        height, width = img_np.shape[:2]
        buf = img_np.tobytes()
        texture = Texture.create(size=(width, height), colorfmt='rgb')
        texture.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')
        
        # Update image widget
        self.image_widget.texture = texture

    def rotate_left(self, *args):
        if self.current_image is not None:
            self.rotation = (self.rotation + 1) % 4
            self._show_image()

    def rotate_right(self, *args):
        if self.current_image is not None:
            self.rotation = (self.rotation - 1) % 4
            self._show_image()
            
    # Toggle view method removed as we're focusing only on bubble detection

    def extract_document_content(self, *args):
        """
        Extract document content using Tesseract OCR with multiple preprocessing methods
        and display the results in a popup.
        """
        if self.current_image is None:
            self.logger.error("No image to extract content from")
            return
            
        # Apply current rotation to the image
        rotated_img = np.rot90(self.current_image, self.rotation)
        
        color_img = None
        if self.current_color_image is not None:
            color_img = np.rot90(self.current_color_image, self.rotation)
        
        self.logger.info("Extracting document content with OCR...")
        try:
            # Try multiple preprocessing methods for OCR
            methods = ['adaptive', 'high_contrast', 'default', 'otsu']
            results = []
            
            # Create a popup to show progress
            content = BoxLayout(orientation='vertical')
            progress_label = Label(text="Extracting content... Please wait.", size_hint=(1, 0.1))
            content.add_widget(progress_label)
            
            popup = Popup(title='Document Content Extraction', content=content, size_hint=(0.8, 0.8))
            popup.open()
            
            # Try each method and collect results
            for method in methods:
                progress_label.text = f"Trying {method} method..."
                text = extract_text(rotated_img, preprocess_method=method)
                results.append((text, method, len(text)))
                self.logger.debug(f"Method {method} extracted {len(text)} characters")
            
            # If we have a color image, try that too
            if color_img is not None:
                for method in methods:
                    progress_label.text = f"Trying {method} method on color image..."
                    text = extract_text(color_img, preprocess_method=method)
                    results.append((text, f"color_{method}", len(text)))
                    self.logger.debug(f"Color method {method} extracted {len(text)} characters")
            
            # Sort by text length (longer is usually better)
            results.sort(key=lambda x: x[2], reverse=True)
            
            # Update popup with results
            content.clear_widgets()
            
            # Create a scrollable text view
            scroll_view = ScrollView(size_hint=(1, 0.8))
            text_input = TextInput(text=results[0][0], multiline=True, readonly=True, size_hint=(1, None))
            text_input.bind(minimum_height=text_input.setter('height'))
            text_input.height = max(len(results[0][0].split('\n')) * 20, 400)  # Estimate height based on line count
            scroll_view.add_widget(text_input)
            
            # Add method selection dropdown
            method_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.1))
            method_label = Label(text="Method used:", size_hint=(0.3, 1))
            
            # Create buttons for each method
            methods_box = BoxLayout(orientation='horizontal', size_hint=(0.7, 1))
            for i, (text, method, length) in enumerate(results[:min(5, len(results))]):
                btn = Button(text=method, size_hint=(1/min(5, len(results)), 1))
                btn.method_index = i  
                btn.bind(on_press=lambda btn: text_input.setter('text')(text_input, results[btn.method_index][0]))
                methods_box.add_widget(btn)
            
            method_layout.add_widget(method_label)
            method_layout.add_widget(methods_box)
            
            # Add close button
            close_button = Button(text='Close', size_hint=(1, 0.1))
            close_button.bind(on_press=popup.dismiss)
            
            # Add all widgets to content
            content.add_widget(scroll_view)
            content.add_widget(method_layout)
            content.add_widget(close_button)
            
            self.logger.info(f"Content extracted successfully using {results[0][1]} method")
        except Exception as e:
            self.logger.error(f"Error extracting content: {str(e)}")
            # Update popup with error
            content.clear_widgets()
            error_label = Label(text=f"Error extracting content: {str(e)}")
            content.add_widget(error_label)
            close_button = Button(text='Close', size_hint=(1, 0.2))
            close_button.bind(on_press=popup.dismiss)
            content.add_widget(close_button)
    
    def save_image(self, *args):
        import cv2
        import time
        img_np = self.current_image
        if img_np is not None:
            img_to_save = np.rot90(img_np, self.rotation)
            fname = f"processed_{int(time.time())}.png"
            if len(img_to_save.shape) == 3 and img_to_save.shape[2] == 3:
                img_to_save = img_to_save[..., ::-1]
            cv2.imwrite(fname, img_to_save)
            self.logger.info(f"Image saved as {fname}")

    def set_on_back(self, callback):
        self.on_back_callback = callback

    def on_back(self, *args):
        if self.on_back_callback:
            self.on_back_callback()
            
    def extract_text(self, *args):
        """Extract text from the document using Tesseract OCR"""
        if self.current_color_image is None and self.current_binary_image is None:
            self.logger.error("No image to extract text from")
            return
            
        # Use the binary image for OCR as it's usually better for text recognition
        source_img = self.current_binary_image if self.current_binary_image is not None else self.current_color_image
        
        # Apply current rotation to the image
        rotated_img = np.rot90(source_img, self.rotation)
        
        self.logger.info("Extracting text with OCR...")
        try:
            # Try multiple preprocessing methods for OCR
            methods = ['adaptive', 'high_contrast', 'default', 'otsu']
            best_text = ""
            best_method = ""
            best_length = 0
            
            for method in methods:
                text = extract_text(rotated_img, preprocess_method=method)
                if len(text) > best_length:
                    best_text = text
                    best_method = method
                    best_length = len(text)
                    
            # Create a popup to display the extracted text
            content = BoxLayout(orientation='vertical')
            text_input = TextInput(text=best_text, multiline=True, readonly=True, size_hint=(1, 0.9))
            method_label = Label(text=f"Method used: {best_method}", size_hint=(1, 0.1))
            content.add_widget(text_input)
            content.add_widget(method_label)
            
            popup = Popup(title='Extracted Text', content=content, size_hint=(0.8, 0.8))
            close_button = Button(text='Close', size_hint=(1, 0.1))
            close_button.bind(on_press=popup.dismiss)
            content.add_widget(close_button)
            popup.open()
            
            self.logger.info(f"Text extracted successfully using {best_method} method")
        except Exception as e:
            self.logger.error(f"Error extracting text: {str(e)}")
            
    def analyze_answers(self, *args):
        if self.current_color_image is None:
            self.logger.error("No image to analyze")
            return
        
        # Get the current image for analysis - use binary image if available, otherwise color
        source_img = self.current_binary_image if self.current_binary_image is not None else self.current_color_image
        

        rotated_img = np.rot90(source_img, k=(-self.rotation) % 4)
        
        # Also rotate color image for visualization
        rotated_color = np.rot90(self.current_color_image, k=(-self.rotation) % 4)
        
        # Detect bubbles in the processed image
        self.logger.info("Analyzing answers...")
        try:
            # Save debug image
            import time
            debug_path = f"bubble_analysis_{int(time.time())}"
            
            # Save the rotated binary image for debugging
            cv2.imwrite(f"{debug_path}_binary.png", rotated_img)
            
            # Detect bubbles
            self.detected_answers = detect_bubbles(rotated_img, debug=True, debug_save_path=debug_path)
            
            # Clear previous results
            self.results_grid.clear_widgets()
            
            if self.detected_answers:
                # Display results
                for question_num, answer in sorted(self.detected_answers.items()):
                    # Question label
                    q_label = Label(text=f"Q{question_num}:", size_hint_y=None, height=40, bold=True)
                    # Answer label
                    a_label = Label(text=f"{answer}", size_hint_y=None, height=40, font_size=18, bold=True)
                    
                    self.results_grid.add_widget(q_label)
                    self.results_grid.add_widget(a_label)
                    
                self.logger.info(f"Detected {len(self.detected_answers)} answers")
                self.results_label.text = f"Detected Answers: {len(self.detected_answers)}"
            else:
                self.results_grid.add_widget(Label(text="No answers detected", size_hint_y=None, height=40))
                self.results_grid.add_widget(Label(text="", size_hint_y=None, height=40))
                self.results_label.text = "No Answers Detected"
                self.logger.warning("No answers detected in the image")
                
        except Exception as e:
            self.logger.error(f"Error analyzing answers: {e}")
            self.results_grid.clear_widgets()
            self.results_grid.add_widget(Label(text="Error analyzing", size_hint_y=None, height=40))
            self.results_grid.add_widget(Label(text="", size_hint_y=None, height=40))
