"""
Flask API with Alloy commands

Run:
  python examples/60-integration/02_flask_endpoint.py

Requirements:
  - flask (see examples/requirements.txt)

Notes:
  - Alloy disappears into normal web apps
  - Offline: export ALLOY_BACKEND=fake

Example:
  curl -X POST http://127.0.0.1:5000/api/draft-email \
    -H 'Content-Type: application/json' \
    -d '{"purpose":"follow up","context":"Customer asked about invoice #123"}'
"""

from dataclasses import dataclass, asdict

try:
    from flask import Flask, request, jsonify
except ImportError:
    import sys

    print("This example needs Flask: pip install -r examples/requirements.txt")
    sys.exit(1)
from alloy import command, configure
from dotenv import load_dotenv

load_dotenv()
configure(temperature=0.2)

app = Flask(__name__)


@dataclass
class EmailDraft:
    subject: str
    body: str
    tone: str


@command(output=EmailDraft)
def draft_email(purpose: str, context: str) -> str:
    return f"""
    Draft a professional email for this purpose: {purpose}
    Context: {context}

    Return JSON with subject, body, and tone fields.
    """


@app.route("/api/draft-email", methods=["POST"])
def api_draft_email():
    data = request.get_json(force=True, silent=True) or {}
    try:
        draft = draft_email(
            purpose=str(data.get("purpose", "")),
            context=str(data.get("context", "")),
        )
        return jsonify(asdict(draft))
    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    app.run(debug=True)
