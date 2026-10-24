from flask import Flask, render_template, request, jsonify, session
import random
import secrets
import re
from pathlib import Path

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# --------------------------------------------------
# LOAD WORDS FROM words.txt
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
WORD_FILE = BASE_DIR / "words.txt"


def load_words():
    """Load valid Hangman words from words.txt."""

    if not WORD_FILE.exists():
        raise FileNotFoundError(
            f"words.txt not found! Please create it here: {WORD_FILE}"
        )

    with open(WORD_FILE, "r", encoding="utf-8") as file:
        words = [
            line.strip().upper()
            for line in file
            if line.strip().isalpha()
            and 4 <= len(line.strip()) <= 10
        ]

    # Remove duplicate words
    words = list(set(words))

    if not words:
        raise ValueError(
            "No valid words found in words.txt. "
            "Add alphabetic words containing 4 to 10 letters."
        )

    return words


WORDS = load_words()


# --------------------------------------------------
# HANGMAN DRAWING STAGES
# --------------------------------------------------

STAGES = [
r"""  +---+
  |   |
      |
      |
      |
      |
=========""",

r"""  +---+
  |   |
  O   |
      |
      |
      |
=========""",

r"""  +---+
  |   |
  O   |
  |   |
      |
      |
=========""",

r"""  +---+
  |   |
  O   |
 /|   |
      |
      |
=========""",

r"""  +---+
  |   |
  O   |
 /|\  |
      |
      |
=========""",

r"""  +---+
  |   |
  O   |
 /|\  |
 /    |
      |
=========""",

r"""  +---+
  |   |
  O   |
 /|\  |
 / \  |
      |
========="""
]


# --------------------------------------------------
# START A NEW GAME
# --------------------------------------------------

def start_game():
    session["word"] = random.choice(WORDS)
    session["guessed"] = []
    session["wrong"] = []
    session["status"] = "playing"


# --------------------------------------------------
# GET CURRENT GAME STATE
# --------------------------------------------------

def state():
    word = session["word"]
    guessed = set(session["guessed"])
    wrong = session["wrong"]

    mistakes = len(wrong)

    won = all(letter in guessed for letter in word)

    if won:
        status = "won"
    elif mistakes >= 6:
        status = "lost"
    else:
        status = "playing"

    session["status"] = status

    return {
        "word_display": " ".join(
            letter if letter in guessed else "_"
            for letter in word
        ),
        "guessed": sorted(guessed),
        "wrong": wrong,
        "mistakes": mistakes,
        "remaining": max(0, 6 - mistakes),
        "stage": STAGES[min(mistakes, 6)],
        "status": status,
        "secret_word": word if status != "playing" else None
    }


# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------

@app.route("/")
def index():
    if "word" not in session:
        start_game()

    return render_template("index.html", state=state())


# --------------------------------------------------
# GUESS A LETTER
# --------------------------------------------------

@app.route("/guess", methods=["POST"])
def guess():
    if "word" not in session:
        start_game()

    data = request.get_json(silent=True) or {}

    letter = str(data.get("letter", "")).strip().upper()

    # Prevent guessing after the round ends
    if session.get("status") in ("won", "lost"):
        return jsonify({
            "error": "Round over. Start a new game."
        }), 400

    # Accept exactly one English alphabet letter
    if not re.fullmatch(r"[A-Z]", letter):
        return jsonify({
            "error": "Please choose one letter from A to Z."
        }), 400

    # Prevent duplicate guesses
    if letter in session["guessed"]:
        return jsonify({
            "error": f"You already guessed {letter}. No attempt deducted.",
            "state": state()
        })

    # Save the guessed letter
    session["guessed"].append(letter)

    # Save incorrect guesses
    if letter not in session["word"]:
        session["wrong"].append(letter)

    session.modified = True

    return jsonify({
        "state": state()
    })


# --------------------------------------------------
# START A NEW GAME
# --------------------------------------------------

@app.route("/new-game", methods=["POST"])
def new_game():
    start_game()

    return jsonify({
        "state": state()
    })


# --------------------------------------------------
# RUN THE FLASK APPLICATION
# --------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
