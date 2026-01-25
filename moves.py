# moves.py

# --- STRIKES (New Registry for variety) ---
STRIKES = {
    "Chop": {
        "dmg": 5, "penalty": 0,
        "hit": "A KNIFE-EDGE CHOP echoes through the arena!",
        "blocked": "They absorbed the chop and stared you down!"
    },
    "Kick": {
        "dmg": 6, "penalty": 0,
        "hit": "Stiff kick to the midsection connects!",
        "blocked": "They caught your leg and shoved you back!"
    },
    "Elbow": {
        "dmg": 5, "penalty": 0,
        "hit": "Reviewing the tape... yes, an elbow right to the jaw!",
        "blocked": "Blocked! They saw it coming a mile away."
    }
}

# --- GRAPPLES (The QTE Moves) ---
GRAPPLE_MOVES = {
    "Suplex": {
        "dmg": 15, "speed": 5, 
        "desc": "Vertical Suplex",
        "hit": "You hoist them up... and SLAM them to the mat!",
        "crit": "HELD IN THE AIR FOR 10 SECONDS! BRAINBUSTER!",
        "botch": "You couldn't get the lift! You fell backward!"
    },
    "Powerbomb": {
        "dmg": 25, "speed": 8, 
        "desc": "High Impact Bomb",
        "hit": "Sit-out Powerbomb! The ring shook!",
        "crit": "BATISTA BOMB! THEY MIGHT BE BROKEN IN HALF!",
        "botch": "Back body drop! You got countered mid-move!"
    },
    "Piledriver": {
        "dmg": 35, "speed": 12, 
        "desc": "Neck Drop",
        "hit": "He spiked him! Piledriver connects!",
        "crit": "TOMBSTONE! CROSS THEIR ARMS! IT'S OVER!",
        "botch": "They reversed it! You took the impact!"
    },
    "DDT": {
        "dmg": 18, "speed": 6, 
        "desc": "Face Plant",
        "hit": "Caught the head... DDT!",
        "crit": "TORNADO DDT FROM THE CORNER! SPECTACULAR!",
        "botch": "They pushed you off and you hit the turnbuckle."
    }
}

# --- GROUND ATTACKS ---
GROUND_MOVES = {
    "Stomp": {
        "dmg": 5, "risk": 0.0,
        "hit": "Boot to the face! Disrespectful!",
        "miss": "Whiffed! They rolled away."
    },
    "Elbow Drop": {
        "dmg": 12, "risk": 0.4,
        "hit": "DROPPING THE ELBOW! Right to the heart!",
        "miss": "Nobody home! You hit the canvas hard!"
    },
    "Knee Drop": {
        "dmg": 8, "risk": 0.2,
        "hit": "Knee drop across the forehead!",
        "miss": "They moved! You busted your knee!"
    }
}

# --- RUNNING ATTACKS ---
RUNNING_MOVES = {
    "Clothesline": {
        "dmg": 12, "risk": 0.5,
        "hit": "CLOTHESLINE FROM HELL! TURNED THEM INSIDE OUT!",
        "miss": "They ducked! You went over the top rope!"
    },
    "Spear": {
        "dmg": 18, "risk": 0.6,
        "hit": "GORE! GORE! GORE! BROKEN IN HALF!",
        "miss": "You hit the ring post! Shoulder first!"
    }
}
