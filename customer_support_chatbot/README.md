# Customer Support Chatbot

A beginner-friendly full-stack rule-based chatbot using Python, Flask, HTML, CSS, JavaScript, and a JSON FAQ dataset.

## Project structure

- `app.py` — Flask web server and `/chat` API endpoint
- `chatbot.py` — input normalization, regex intent matching, multiple FAQ responses, fallback, and exit handling
- `sample_faq.json` — the supplied sample greetings and FAQ answers
- `templates/index.html` — chat interface
- `static/style.css` — responsive styling
- `static/script.js` — sends messages to Flask and displays responses

## Run locally

1. Install Python 3.
2. Open a terminal in this project folder.
3. Install Flask:

   ```bash
   python -m pip install -r requirements.txt
   ```

4. Start the application:

   ```bash
   python app.py
   ```

5. Open `http://127.0.0.1:5000` in your browser.

## Try these questions

- `Hi`
- `What are your hours of operation?`
- `How do I submit my internship project?`
- `When will I receive my certificate?`
- `Tell me the hours and certificate details`
- `What is the weather today?` (tests fallback)
- `bye` (ends the chat interaction)

## Customize the FAQ

Edit `sample_faq.json` to change greetings and answers. If you add a completely new FAQ topic, add its regex patterns and corresponding FAQ index to `FAQ_PATTERNS` in `chatbot.py`.

This is a rule-based bot, not an AI/LLM chatbot. The sample business-hour and FAQ answers are demo data from the provided sample FAQ dataset.
