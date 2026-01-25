# mechanics.py
import random

class QTEManager:
    def __init__(self):
        self.active = False
        self.value = 0
        self.speed = 0
        self.target_move = None

    def start(self, move_data):
        self.active = True
        self.value = 0
        self.speed = move_data['speed']
        self.target_move = move_data

    def update(self):
        if not self.active: return
        self.value += self.speed
        if self.value > 100: self.value = 0
    
    def resolve(self):
        self.active = False
        return self.value

class SubmissionManager:
    def __init__(self):
        self.target = 5
        self.banned = []
        self.attempts = 0

    def start(self, is_defense):
        self.target = random.randint(2, 9)
        self.banned = [self.target]
        self.attempts = 0

    def generate_next(self):
        new_val = random.randint(1, 10)
        while new_val in self.banned:
            new_val = random.randint(1, 10)
        
        self.banned.append(new_val)
        if len(self.banned) > 3: self.banned.pop(0)
        return new_val

    def check_guess(self, guess, next_val):
        if guess == "HIGHER" and next_val > self.target: return True
        if guess == "LOWER" and next_val < self.target: return True
        return False
