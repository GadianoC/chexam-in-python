import logging
from ..db.answer_key_db import save_answer_key, get_answer_key, get_all_answer_keys, delete_answer_key

class AnswerKey:
    def __init__(self, num_questions, name=None, key_id=None):
        self.num_questions = num_questions
        self.key = {}  # Stores question number as the key and answer as the value
        self.name = name
        self.key_id = key_id
        self.logger = logging.getLogger("chexam.ui.answer_key")
        
        # If key_id or name is provided, load the answer key from the database
        if key_id is not None or name is not None:
            self.load_from_db(key_id, name)
        
    def add_answer(self, question_num, answer):
        if 1 <= question_num <= self.num_questions:
            self.key[question_num] = answer
        else:
            raise ValueError("Invalid question number")
    
    def get_answer(self, question_num):
        return self.key.get(question_num)
    
    def get_all_answers(self):
        return self.key
    
    def save_to_db(self, name):
        """Save the answer key to the database with the given name."""
        if not name:
            self.logger.error("Cannot save answer key: No name provided")
            return False
            
        self.name = name
        # Convert question numbers from int to str for JSON serialization
        answers_dict = {str(k): v for k, v in self.key.items()}
        key_id = save_answer_key(name, self.num_questions, answers_dict)
        
        if key_id:
            self.key_id = key_id
            return True
        return False
    
    def load_from_db(self, key_id=None, name=None):
        """Load an answer key from the database by ID or name."""
        answer_key = get_answer_key(key_id, name)
        
        if answer_key:
            self.key_id = answer_key['id']
            self.name = answer_key['name']
            self.num_questions = answer_key['num_questions']
            
            # Convert question numbers from str to int
            self.key = {int(k): v for k, v in answer_key['answers'].items()}
            return True
        return False
    
    @staticmethod
    def get_all_keys():
        """Get all answer keys from the database."""
        return get_all_answer_keys()
    
    @staticmethod
    def delete_key(key_id=None, name=None):
        """Delete an answer key from the database."""
        return delete_answer_key(key_id, name)
    
    def display_key(self):
        """Display the answer key for debugging."""
        print(f"Answer Key: {self.name} (ID: {self.key_id})")
        print(f"Number of Questions: {self.num_questions}")
        for question_num, answer in sorted(self.key.items()):
            print(f"Question {question_num}: Answer {answer}")
