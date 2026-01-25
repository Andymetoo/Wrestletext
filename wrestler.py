# wrestler.py
MAX_HEALTH = 100
MAX_STAMINA = 100

class Wrestler:
    def __init__(self, name, is_player):
        self.name = name
        self.hp = MAX_HEALTH
        self.stamina = MAX_STAMINA
        self.heat_bonus = 0
        self.state = "NEUTRAL"
        self.move_history = [] 

    def record_move(self, move_name):
        self.move_history.append(move_name)
        if len(self.move_history) > 5:
            self.move_history.pop(0)

    def get_stale_penalty(self, move_name):
        count = self.move_history.count(move_name)
        if count == 0: return 0.0
        if count == 1: return 0.1
        if count == 2: return 0.4
        return 0.8
