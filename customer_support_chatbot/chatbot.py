import json
import re
from pathlib import Path

FAQ_PATH = Path(__file__).with_name("sample_faq.json")

with FAQ_PATH.open("r", encoding="utf-8") as file:
    FAQ_DATA = json.load(file)

GREETINGS = FAQ_DATA.get("greetings", [])
FAQS = FAQ_DATA.get("faqs", [])

# Patterns are based on the questions in sample_faq.json.
FAQ_PATTERNS = [
    {
        "faq_index": 0,
        "patterns": [
            r"\bhours?\b",
            r"\bopening hours\b",
            r"\bhours? of operation\b",
            r"\bwhen do you open\b",
            r"\bwhen do you close\b",
            r"\bbusiness hours\b"
        ]
    },
    {
        "faq_index": 1,
        "patterns": [
            r"\binternship project\b",
            r"\bsubmit\b.*\bproject\b",
            r"\bproject submission\b",
            r"\bgithub\b",
            r"\bstudent workspace\b"
        ]
    },
    {
        "faq_index": 2,
        "patterns": [
            r"\bcertificate(s)?\b",
            r"\bwhen will i receive\b",
            r"\bissue(d|ance)?\b.*\bcertificate(s)?\b"
        ]
    }
]

def normalize_input(message: str) -> str:
    """Lowercase the message and collapse repeated whitespace."""
    return re.sub(r"\s+", " ", message.lower()).strip()

def find_matching_faqs(message: str):
    """Return all FAQ entries that match the user's message."""
    matches = []
    for rule in FAQ_PATTERNS:
        if any(re.search(pattern, message) for pattern in rule["patterns"]):
            index = rule["faq_index"]
            if index < len(FAQS):
                matches.append(FAQS[index])
    return matches

def get_response(user_input: str):
    """Return a greeting, one or more FAQ answers, or a fallback."""
    message = normalize_input(user_input)

    if not message:
        return {
            "messages": ["Please type a question so I can help you."],
            "exit": False
        }

    if re.fullmatch(r"(bye|goodbye|exit|quit)", message):
        return {
            "messages": ["Thank you for chatting with us. Goodbye!"],
            "exit": True
        }

    responses = []

    # Match greetings as whole phrases/words.
    greeting_pattern = r"\b(" + "|".join(
        re.escape(greeting) for greeting in sorted(GREETINGS, key=len, reverse=True)
    ) + r")\b"
    if re.search(greeting_pattern, message):
        responses.append("Hello! Welcome to Customer Support. How can I help you?")

    matched_faqs = find_matching_faqs(message)
    for faq in matched_faqs:
        if faq["answer"] not in responses:
            responses.append(faq["answer"])

    if not responses:
        responses.append(
            "Sorry, I couldn't understand that question. You can ask me about "
            "business hours, internship project submission, or certificates."
        )

    return {"messages": responses, "exit": False}
