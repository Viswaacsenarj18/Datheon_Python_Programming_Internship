# Hangman — Full-Stack Word Game

A browser-based Hangman game built with Python, Flask, HTML, CSS, and JavaScript.

## Features
- Random word selection from a built-in list
- Six incorrect guesses and ASCII gallows stages
- Clickable on-screen keyboard and physical keyboard input
- Duplicate guesses do not deduct attempts
- Correct/wrong letter highlighting
- Win/loss messages reveal the secret word
- New Game button
- Flask session keeps each round's state

## Run
1. Open this folder in VS Code.
2. In terminal run: `python -m pip install -r requirements.txt`
3. Run: `python app.py`
4. Open `http://127.0.0.1:5000` in your browser.

The built-in word list means you do not need to download a separate text file.
