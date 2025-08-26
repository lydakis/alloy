"""
Multi-modal OCR from an image → summarize table

Run:
  python examples/90-advanced/03_multi_modal.py /path/to/table_image.png

Requirements:
  - pillow, pytesseract (see examples/requirements.txt)
  - Tesseract OCR system binary installed (e.g., `brew install tesseract` on macOS)

Notes:
  - Uses local OCR via pytesseract, then summarizes with Alloy
  - OpenAI is multi-modal, but Alloy currently passes text content; native image parts may be added later
  - Offline: export ALLOY_BACKEND=fake
"""

from __future__ import annotations

import sys
from pathlib import Path
from alloy import command, tool, configure
from dotenv import load_dotenv


@tool
def ocr_image(path: str) -> str:
    """Extract text from an image using pytesseract (install pillow, pytesseract)."""
    try:
        from PIL import Image
        import pytesseract
    except Exception:
        return "ERROR: install pillow and pytesseract to enable OCR"
    p = Path(path)
    if not p.exists():
        return f"ERROR: image not found: {p}"
    try:
        img = Image.open(p)
        return pytesseract.image_to_string(img)
    except Exception as e:
        return f"ERROR: OCR failed: {e}"


@command
def describe_table(ocr_text: str) -> str:
    return f"Infer the schema and 3 insights from this table OCR text:\n{ocr_text}"


def main():
    load_dotenv()
    configure(temperature=0.2)
    img_path = sys.argv[1] if len(sys.argv) > 1 else ""
    if not img_path:
        print("Usage: python examples/90-advanced/03_multi_modal.py /path/to/image.png")
        print("Tip: returns a helpful error if OCR deps are missing.")
    text = ocr_image(img_path) if img_path else ""
    if text.startswith("ERROR:") or not text.strip():
        # Fallback sample if OCR is unavailable
        text = (
            "Item, Price, Qty\n"
            "Widget A, 19.99, 3\n"
            "Widget B, 9.50, 5\n"
            "Total, 69.47, -\n"
        )
    print(describe_table(text))


if __name__ == "__main__":
    main()
