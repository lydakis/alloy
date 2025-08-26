"""
Multi-stage translator network

Run:
  python examples/50-composition/04_translator_network.py

Notes:
  - Detect language → translate to English → translate to target
  - Offline: export ALLOY_BACKEND=fake
"""

from alloy import command, configure
from dotenv import load_dotenv


@command
def detect_language(text: str) -> str:
    return f"Detect the language of this text and return only the language name: {text}"


@command
def translate(text: str, target_lang: str) -> str:
    return f"Translate to {target_lang}. Keep meaning and tone. Text: {text}"


def translate_pipeline(text: str, target_lang: str) -> str:
    src = detect_language(text).strip()
    en = text if src.lower() == "english" else translate(text, "English")
    out = en if target_lang.lower() == "english" else translate(en, target_lang)
    return f"Source language: {src}\n\n{out}"


def main():
    load_dotenv()
    configure(temperature=0.2)
    sample = "Bonjour, je m'appelle Marie."
    print(translate_pipeline(sample, "Spanish"))


if __name__ == "__main__":
    main()
