from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.graphics.texture import Texture
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.metrics import dp
from .base_screen import BaseScreen
import numpy as np
import cv2
import logging
import time
import os
import json
# Import Gemini Vision processing instead of OCR
from ..processing.gemini_vision import process_document_with_gemini

class ProcessedImageScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(title="Processed Image", **kwargs)
        self.logger = logging.getLogger("chexam.ui.processed_image_screen")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('[%(levelname)s] %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        # Create main content layout
        content_layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        # Image widget - takes up top portion of screen
        self.image_widget = Image(
            size_hint_y=None, 
            height=dp(350), 
            allow_stretch=True, 
            keep_ratio=True
        )
        
        # Results label
        self.results_label = Label(
            text='Detected Answers', 
            size_hint_y=None, 
            height=dp(40), 
            font_size=dp(18), 
            bold=True,
            color=(0.2, 0.6, 1, 1)
        )
        
        # Scrollable results grid
        self.scroll_view = ScrollView(size_hint_y=None, height=dp(200))
        self.results_grid = GridLayout(cols=2, spacing=dp(10), size_hint_y=None)
        self.results_grid.bind(minimum_height=self.results_grid.setter('height'))
        self.scroll_view.add_widget(self.results_grid)
        
        # Style function for buttons
        def style_button(btn, icon_only=False):
            btn.background_normal = ''
            btn.background_color = (0.2, 0.6, 1, 1)
            btn.color = (1, 1, 1, 1)
            if icon_only:
                btn.size_hint = (None, None)
                btn.width = dp(60)
                btn.height = dp(60)
                btn.font_size = dp(24)
            else:
                btn.size_hint_x = 1
                btn.size_hint_y = None
                btn.height = dp(60)
                btn.font_size = dp(18)
            return btn
        
        # Image controls in a horizontal layout
        image_controls = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60), spacing=dp(10))
        self.rotate_left_btn = style_button(Button(text='⟲'), icon_only=True)
        self.rotate_right_btn = style_button(Button(text='⟳'), icon_only=True)
        self.flip_horizontal_btn = style_button(Button(text='↔'), icon_only=True)
        self.flip_vertical_btn = style_button(Button(text='↕'), icon_only=True)
        
        self.rotate_left_btn.bind(on_press=self.rotate_left)
        self.rotate_right_btn.bind(on_press=self.rotate_right)
        self.flip_horizontal_btn.bind(on_press=self.flip_horizontal)
        self.flip_vertical_btn.bind(on_press=self.flip_vertical)
        
        image_controls.add_widget(self.rotate_left_btn)
        image_controls.add_widget(self.rotate_right_btn)
        image_controls.add_widget(self.flip_horizontal_btn)
        image_controls.add_widget(self.flip_vertical_btn)
        
        # Action buttons
        action_buttons = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(130), spacing=dp(10))
        self.save_btn = style_button(Button(text='💾 Save Image'))
        self.extract_content_btn = style_button(Button(text='📝 Extract Answers'))
        
        self.save_btn.bind(on_press=self.save_image)
        self.extract_content_btn.bind(on_press=self.extract_document_content)
        
        action_buttons.add_widget(self.save_btn)
        action_buttons.add_widget(self.extract_content_btn)
        
        # Add all sections to content layout
        content_layout.add_widget(self.image_widget)
        content_layout.add_widget(image_controls)
        content_layout.add_widget(self.results_label)
        content_layout.add_widget(self.scroll_view)
        content_layout.add_widget(action_buttons)
        
        # Add content layout to the content area
        self.content_area.add_widget(content_layout)
        
        # State variables
        self.current_image = None
        self.current_color_image = None  
        self.current_binary_image = None  
        self.rotation = 0  
        self.flip_h = False 
        self.flip_v = False 
        self.detected_answers = {}

    def set_image(self, binary_img, color_img=None):
        """Set the image to display and process."""
        if binary_img is None:
            self.logger.error("No image data provided")
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
        
        # Set correct orientation for display
        self.rotation = 0
        self.flip_h = False
        self.flip_v = False  
        
        # Update the image display
        self._show_image()
        
        # Clear previous results
        self.results_grid.clear_widgets()
        self.detected_answers = {}

    def _show_image(self):
        if self.current_image is None:
            return
            
        # Start with the original image
        img_np = self.current_image.copy()
        
        # Apply rotation if needed
        img_np = np.rot90(img_np, self.rotation)
        
        # Apply flips if needed
        if self.flip_h:
            img_np = cv2.flip(img_np, 1)  
        
        if self.flip_v:
            img_np = cv2.flip(img_np, 0) 
        
        # Convert to texture
        if len(img_np.shape) == 2:  
            img_np = cv2.cvtColor(img_np, cv2.COLOR_GRAY2BGR)
            img_np = img_np[..., ::-1]  
        elif len(img_np.shape) == 3 and img_np.shape[2] == 3: 
            img_np = img_np[..., ::-1]  
            
        # Get image dimensions
        height, width = img_np.shape[:2]
        
        # Create texture with correct size and format
        buf = img_np.tobytes()
        texture = Texture.create(size=(width, height), colorfmt='rgb')
        texture.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')
        
        # Update image widget
        self.image_widget.texture = texture
        
        # Ensure image widget has proper size
        self.image_widget.size_hint_y = None
        self.image_widget.height = dp(350)

    def rotate_left(self, *args):
        if self.current_image is not None:
            self.rotation = (self.rotation + 1) % 4
            self._show_image()

    def rotate_right(self, *args):
        if self.current_image is not None:
            self.rotation = (self.rotation - 1) % 4
            self._show_image()
            
    def flip_horizontal(self, *args):
        if self.current_image is not None:
            self.flip_h = not self.flip_h 
            self._show_image()
            
    def flip_vertical(self, *args):
        if self.current_image is not None:
            self.flip_v = not self.flip_v 
            self._show_image()
            
    # Toggle view method removed as we're focusing only on bubble detection

    def extract_document_content(self, *args):
        """
        Extract document content using Gemini Vision API and display the results in a popup.
        """
        if self.current_image is None:
            self.logger.error("No image to extract content from")
            return
        
        # First, ask for the student name
        self.show_student_name_popup()
    
    def show_student_name_popup(self):
        """Show a popup to enter the student name before extracting content."""
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        # Add a label and text input for the student name
        name_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        name_label = Label(text="Student Name:", size_hint_x=0.3)
        self.student_name_input = TextInput(hint_text="Enter student name", multiline=False, size_hint_x=0.7)
        name_box.add_widget(name_label)
        name_box.add_widget(self.student_name_input)
        content.add_widget(name_box)
        
        # Add buttons
        buttons = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        proceed_button = Button(text="Proceed")
        cancel_button = Button(text="Cancel")
        buttons.add_widget(proceed_button)
        buttons.add_widget(cancel_button)
        content.add_widget(buttons)
        
        # Create and open the popup
        popup = Popup(title="Enter Student Information", content=content, size_hint=(0.8, 0.4))
        
        # Bind buttons
        proceed_button.bind(on_press=lambda x: self.process_with_gemini(popup))
        cancel_button.bind(on_press=popup.dismiss)
        
        popup.open()
    
    def process_with_gemini(self, popup):
        """Process the image with Gemini Vision API after getting the student name."""
        # Get the student name
        student_name = self.student_name_input.text.strip()
        if not student_name:
            student_name = "Unknown Student"
        
        # Close the student name popup
        popup.dismiss()
        
        # Check if we have a saved image file
        import glob
        import os
        import time
        
        # Look for the most recent processed_*.png file
        processed_files = glob.glob("processed_*.png")
        if processed_files:
            # Sort by modification time (newest first)
            processed_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            image_path = processed_files[0]
            self.logger.info(f"Using saved image file: {image_path}")
            
            # Read the image file
            processed_image = cv2.imread(image_path)
            if processed_image is None:
                self.logger.error(f"Failed to read image file: {image_path}")
                # Fall back to using the current image
                if self.current_color_image is not None:
                    processed_image = self.current_color_image.copy()
                else:
                    processed_image = cv2.cvtColor(self.current_image, cv2.COLOR_GRAY2BGR)
        else:
            # If no saved image file, save the current image first
            self.logger.info("No saved image file found, saving current image")
            timestamp = int(time.time())
            image_path = f"processed_{timestamp}.png"
            
            # Prepare the image with current transformations
            if self.current_color_image is not None:
                img_to_save = self.current_color_image.copy()
            else:
                img_to_save = cv2.cvtColor(self.current_image, cv2.COLOR_GRAY2BGR)
            
            # Apply rotation and flips
            img_to_save = np.rot90(img_to_save, self.rotation)
            if self.flip_h:
                img_to_save = cv2.flip(img_to_save, 1)
            if self.flip_v:
                img_to_save = cv2.flip(img_to_save, 0)
            
            # Save the image
            if len(img_to_save.shape) == 3 and img_to_save.shape[2] == 3:
                img_to_save = img_to_save[..., ::-1]  
            # cv2.imwrite(image_path, img_to_save)
            self.logger.info(f"Saved image as {image_path}")
            
            # Read the saved image to ensure we're using the same file that will be used for future analysis
            processed_image = cv2.imread(image_path)
        
        # Create a popup to show progress
        content = BoxLayout(orientation='vertical')
        progress_label = Label(
            text=f"Extracting content for {student_name}\nusing Gemini Vision API...\nThis may take a few seconds.", 
            halign='center', size_hint=(1, 0.1)
        )
        content.add_widget(progress_label)
        
        popup = Popup(title='Document Content Extraction', content=content, size_hint=(0.8, 0.8))
        popup.open()
        
        # Save a debug image with timestamp
        debug_path = None
        
        # Process the document with Gemini Vision
        progress_label.text = "Sending image to Gemini Vision API..."
        
        # Store the student name for later use
        self.student_name = student_name
        
        # Process using the saved image file
        results = process_document_with_gemini(processed_image, debug_save_path=debug_path, debug=False)
            
        # Extract the answers from the results
        gemini_data = results.get('gemini_results', {})
        
        # Handle both old and new response formats
        if isinstance(gemini_data, dict) and 'answers' in gemini_data:
            gemini_results = gemini_data.get('answers', {})
            score_info = {
                'score': gemini_data.get('score', 0),
                'percentage': gemini_data.get('percentage', 0),
                'summary': gemini_data.get('summary', 'No answer key available for comparison')
            }
        else:
            gemini_results = gemini_data
            score_info = None
        
        # Format the results for display
        formatted_text = f"Student: {self.student_name}\n\nGemini Vision API Results:\n\n"
        
        if gemini_results:
            # Format the answers in JSON format
            formatted_text += "Detected Answers:\n"
            formatted_text += "{"
            
            # Add each answer in JSON format
            answer_lines = []
            for question_num, answer in sorted(gemini_results.items(), key=lambda x: int(x[0])):
                answer_lines.append(f'  "{question_num}": "{answer}"')
            
            formatted_text += "\n" + ",\n".join(answer_lines) + "\n}"
            
            # Add score information if available from the new format
            if score_info:
                formatted_text += "\n\nScore Information:\n"
                formatted_text += "{"
                formatted_text += f"\n  'score': {score_info['score']},"
                formatted_text += f"\n  'percentage': {score_info['percentage']},"
                formatted_text += f"\n  'summary': '{score_info['summary']}'"
                formatted_text += "\n}"
            
            # Get teacher's answer key and compare results
            from ..processing.gemini_vision import compare_answers
            comparison_results = compare_answers(gemini_results)
            
            # Add comparison results if available
            if comparison_results and comparison_results['total'] > 0:
                formatted_text += "\n\nComparison with Answer Key:\n"
                formatted_text += f"Score: {comparison_results['score']}/{comparison_results['total']} "
                formatted_text += f"({comparison_results['percentage']}%)\n\n"
                
                # Add a summary section
                formatted_text += "Summary:\n"
                formatted_text += f"Student: {self.student_name}\n"
                formatted_text += f"Total Questions: {comparison_results['total']}\n"
                formatted_text += f"Correct Answers: {comparison_results['score']}\n"
                formatted_text += f"Score: {comparison_results['percentage']}%\n\n"
                
                formatted_text += "Details:\n"
                for q_num, detail in sorted(comparison_results['details'].items(), key=lambda x: int(x[0])):
                    student = detail['student_answer']
                    correct = detail['correct_answer']
                    result = "✓ Correct" if detail['is_correct'] else "✗ Incorrect"
                    formatted_text += f"Q{q_num}: Student: {student}, Correct: {correct}, {result}\n"
                
                # Save results to a JSON file
                import json
                import time
                
                result_data = {
                    'student_name': self.student_name,
                    'timestamp': int(time.time()),
                    'answers': gemini_results,
                    'score': comparison_results['score'],
                    'total': comparison_results['total'],
                    'percentage': comparison_results['percentage'],
                    'details': comparison_results['details']
                }
                
                # Create a filename with student name and timestamp
                safe_name = self.student_name.replace(' ', '_').lower()
                result_filename = f"{safe_name}_results_{int(time.time())}.json"
                
                try:
                    with open(result_filename, 'w') as f:
                        json.dump(result_data, f, indent=2)
                    self.logger.info(f"Saved results to {result_filename}")
                    formatted_text += f"\nResults saved to {result_filename}"
                except Exception as e:
                    self.logger.error(f"Error saving results: {str(e)}")
        else:
            formatted_text += "No answers detected in the document.\n"
        
        # Create a single result entry
        results = [(formatted_text, "gemini_vision", len(formatted_text))]
        
        # Update popup with results
        content.clear_widgets()
        
        # Create a scrollable text view
        scroll_view = ScrollView(size_hint=(1, 0.8))
        text_input = TextInput(text=results[0][0], multiline=True, readonly=True, size_hint=(1, None))
        text_input.bind(minimum_height=text_input.setter('height'))
        text_input.height = max(len(results[0][0].split('\n')) * 20, 400) 
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
        
        # Show the results popup
        popup.open()
    
    def _handle_extraction_error(self, popup, content, e):
        """Handle errors during content extraction."""
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
            # Apply all transformations to get the final image
            img_to_save = img_np.copy()
            
            # Apply rotation - use the same rotation as displayed to the user
            img_to_save = np.rot90(img_to_save, self.rotation)
            
            # Apply flips if needed - same as displayed to the user
            if self.flip_h:
                img_to_save = cv2.flip(img_to_save, 1) 
            
            if self.flip_v:
                img_to_save = cv2.flip(img_to_save, 0) 
            
            # Save both the processed image and a copy for Gemini Vision API
            timestamp = int(time.time())
            fname = f"processed_{timestamp}.png"
            
            # Convert BGR to RGB if needed
            if len(img_to_save.shape) == 3 and img_to_save.shape[2] == 3:
                img_to_save = img_to_save[..., ::-1]
                
            # cv2.imwrite(fname, img_to_save)
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
        
        processed_image = self.current_color_image.copy()
        
        processed_image = np.rot90(processed_image, self.rotation)
        
        # Apply flips if needed - same as displayed to the user
        if self.flip_h:
            processed_image = cv2.flip(processed_image, 1) 
        
        if self.flip_v:
            processed_image = cv2.flip(processed_image, 0) 
        
        # Process the image with Gemini Vision API
        self.logger.info("Analyzing answers with Gemini Vision API...")
        try:
            # Save a single debug image with a timestamp
            import time
            debug_path = None
            
            # Show a processing popup
            content = BoxLayout(orientation='vertical')
            processing_label = Label(text="Processing with Gemini Vision API...\nThis may take a few seconds.", halign='center')
            content.add_widget(processing_label)
            popup = Popup(title='Processing', content=content, size_hint=(0.6, 0.3), auto_dismiss=False)
            popup.open()
            
            # Process the document with Gemini Vision
            results = process_document_with_gemini(processed_image, debug_save_path=debug_path, debug=False)
            
            # Extract the answers from the results
            gemini_results = results.get('gemini_results', {})
            
            # Get teacher's answer key and compare results
            from ..processing.gemini_vision import compare_answers
            comparison_results = compare_answers(gemini_results)
            
            # Close the popup
            popup.dismiss()
            
            # Clear previous results
            self.results_grid.clear_widgets()
            self.detected_answers = {}
            
            if gemini_results:
                # Add a header for the results
                header_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
                header_box.add_widget(Label(text="Question", bold=True, size_hint_x=0.2))
                header_box.add_widget(Label(text="Student", bold=True, size_hint_x=0.2))
                header_box.add_widget(Label(text="Correct", bold=True, size_hint_x=0.2))
                header_box.add_widget(Label(text="Result", bold=True, size_hint_x=0.4))
                self.results_grid.add_widget(header_box)
                
                # Display comparison results
                details = comparison_results.get('details', {})
                for question_num in sorted(gemini_results.keys(), key=lambda x: int(x)):
                    if question_num in details:
                        detail = details[question_num]
                        student_answer = detail.get('student_answer', 'blank')
                        correct_answer = detail.get('correct_answer', '-')
                        is_correct = detail.get('is_correct', False)
                        
                        # Create a row for this question
                        row = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
                        
                        # Question number
                        q_label = Label(text=f"Q{question_num}", size_hint_x=0.2)
                        
                        # Student answer
                        s_label = Label(text=f"{student_answer}", size_hint_x=0.2, 
                                       color=(0.2, 0.6, 1, 1) if student_answer != 'blank' else (0.7, 0.7, 0.7, 1))
                        
                        # Correct answer
                        c_label = Label(text=f"{correct_answer}", size_hint_x=0.2)
                        
                        # Result indicator
                        if correct_answer == '-':
                            # No answer key for this question
                            r_label = Label(text="No key", size_hint_x=0.4, color=(0.7, 0.7, 0.7, 1))
                        elif student_answer == 'blank':
                            # Student didn't answer
                            r_label = Label(text="Not answered", size_hint_x=0.4, color=(0.7, 0.7, 0.7, 1))
                        elif is_correct:
                            # Correct answer
                            r_label = Label(text="✓ Correct", size_hint_x=0.4, color=(0, 0.8, 0, 1))
                        else:
                            # Incorrect answer
                            r_label = Label(text="✗ Incorrect", size_hint_x=0.4, color=(0.8, 0, 0, 1))
                        
                        row.add_widget(q_label)
                        row.add_widget(s_label)
                        row.add_widget(c_label)
                        row.add_widget(r_label)
                        
                        self.results_grid.add_widget(row)
                    else:
                        # Just show the student answer if no comparison data
                        row = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
                        q_label = Label(text=f"Q{question_num}", size_hint_x=0.2)
                        s_label = Label(text=f"{gemini_results[question_num]}", size_hint_x=0.2)
                        row.add_widget(q_label)
                        row.add_widget(s_label)
                        row.add_widget(Label(text="-", size_hint_x=0.2))
                        row.add_widget(Label(text="No key", size_hint_x=0.4, color=(0.7, 0.7, 0.7, 1)))
                        self.results_grid.add_widget(row)
                
                # Add score summary at the bottom
                score = comparison_results.get('score', 0)
                total = comparison_results.get('total', 0)
                percentage = comparison_results.get('percentage', 0)
                
                if total > 0:
                    summary_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=60)
                    summary_box.add_widget(Label(text="Score:", bold=True, size_hint_x=0.3))
                    summary_box.add_widget(Label(text=f"{score}/{total} ({percentage}%)", 
                                               bold=True, size_hint_x=0.7, 
                                               color=(0, 0.8, 0, 1) if percentage >= 60 else (0.8, 0, 0, 1)))
                    self.results_grid.add_widget(summary_box)
                
                # Update the summary label
                answered_count = sum(1 for ans in gemini_results.values() if ans.upper() in ['A', 'B', 'C', 'D'])
                blank_count = sum(1 for ans in gemini_results.values() if ans.lower() == 'blank')
                
                self.logger.info(f"Detected {answered_count} answers, {blank_count} blank/invalid")
                if total > 0:
                    self.results_label.text = f"Score: {score}/{total} ({percentage}%)"
                else:
                    self.results_label.text = f"Detected: {answered_count} answers"
            else:
                self.results_grid.add_widget(Label(text="No answers detected", size_hint_y=None, height=40))
                self.results_label.text = "No Answers Detected"
                self.logger.warning("No answers detected in the image")
                
        except Exception as e:
            self.logger.error(f"Error analyzing answers with Gemini Vision: {e}")
            self.results_grid.clear_widgets()
            self.results_grid.add_widget(Label(text=f"Error: {str(e)}", size_hint_y=None, height=40))
