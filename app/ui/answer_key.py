class AnswerKey:
    def __init__(self, num_questions):
        self.num_questions = num_questions
        self.key = {}  # Stores question number as the key and answer as the value
        
    def add_answer(self, question_num, answer):
        if 1 <= question_num <= self.num_questions:
            self.key[question_num] = answer
        else:
            raise ValueError("Invalid question number")
    
    def get_answer(self, question_num):
        return self.key.get(question_num)
    
    def display_key(self):
        for question_num, answer in self.key.items():
            print(f"Question {question_num}: Answer {answer}")
