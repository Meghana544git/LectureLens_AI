import json
import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
import google.generativeai as genai
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB
app.config["UPLOAD_FOLDER"] = tempfile.gettempdir()

ALLOWED_AUDIO = {".mp3", ".wav", ".m4a", ".webm", ".mp4", ".mpeg", ".mpga"}
TEXT_EXTENSIONS = {".txt"}

client = genai.GenerativeModel(api_key=os.getenv("GEMINI_API_KEY"))

NOTES_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
TRANSCRIPTION_MODEL = os.getenv("GEMINI_TRANSCRIPTION_MODEL", "gemini-3.5-transcribe")


def clean_json(text):
    """Extract JSON even if a model accidentally wraps it in markdown fences."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        lines = lines[1:] if lines and lines[0].startswith("```") else lines
        lines = lines[:-1] if lines and lines[-1].strip() == "```" else lines
        text = "\n".join(lines).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        text = text[start:end + 1]

    return json.loads(text)


def generate_notes(transcript):
    prompt = f"""
You are an expert college study-note creator.

Turn the lecture transcript below into accurate, exam-friendly study notes.

IMPORTANT RULES:
- Use ONLY information supported by the transcript.
- Do not invent facts.
- Preserve important terminology from the lecture.
- Make the notes useful for revision, not just a short summary.
- Identify 5-7 genuinely important/exam-relevant points when possible.
- Extract definitions explicitly mentioned or clearly defined in the lecture.
- Create a Mermaid flowchart ONLY when the lecture clearly describes a process,
  sequence, pipeline, algorithm, lifecycle, or cause/effect chain.
- If no useful process exists, set diagram.enabled to false.
- Mermaid must be valid flowchart syntax and should avoid special characters that
  commonly break Mermaid.
- Return ONLY valid JSON. No markdown and no extra commentary.

Required JSON schema:
{{
  "title": "lecture title",
  "overview": "2-4 sentence overview",
  "sections": [
    {{
      "heading": "section heading",
      "summary": "short section explanation",
      "points": ["important point 1", "important point 2"]
    }}
  ],
  "definitions": [
    {{
      "term": "term",
      "definition": "definition based on lecture"
    }}
  ],
  "highlights": [
    "critical point 1",
    "critical point 2"
  ],
  "diagram": {{
    "enabled": true,
    "title": "process title",
    "mermaid": "flowchart TD; A[Start] --> B[Next]"
  }}
}}

LECTURE TRANSCRIPT:
{transcript}
"""

    response = client.chat.completions.create(
        model=NOTES_MODEL,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": "You produce precise structured JSON study notes."
            },
            {"role": "user", "content": prompt},
        ],
    )

    return clean_json(response.choices[0].message.content)


def generate_quiz(notes, difficulty="mixed", count=7):
    notes_json = json.dumps(notes, ensure_ascii=False)

    prompt = f"""
Create a quiz from the study notes below.

Difficulty: {difficulty}
Number of questions: {count}

Rules:
- Every question must be answerable from the supplied notes.
- Do not introduce outside facts.
- Mix multiple-choice and short-answer questions.
- For MCQ, provide exactly 4 options.
- For short-answer, options must be an empty array.
- Give the correct answer and a short explanation.
- Return ONLY valid JSON.

Schema:
{{
  "questions": [
    {{
      "type": "mcq",
      "question": "question",
      "options": ["A", "B", "C", "D"],
      "answer": "exact correct option text",
      "explanation": "why it is correct"
    }},
    {{
      "type": "short_answer",
      "question": "question",
      "options": [],
      "answer": "expected answer",
      "explanation": "what the learner should remember"
    }}
  ]
}}

STUDY NOTES:
{notes_json}
"""

    response = client.chat.completions.create(
        model=NOTES_MODEL,
        temperature=0.4,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": "You create accurate educational quizzes from supplied notes."
            },
            {"role": "user", "content": prompt},
        ],
    )

    return clean_json(response.choices[0].message.content)


def transcribe_audio(file_storage):
    suffix = Path(secure_filename(file_storage.filename)).suffix.lower()
    if suffix not in ALLOWED_AUDIO:
        raise ValueError(
            "Unsupported audio format. Use MP3, WAV, M4A, WEBM, MP4, MPEG, or MPGA."
        )

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
            file_storage.save(temp.name)
            temp_path = temp.name

        with open(temp_path, "rb") as audio_file:
            result = client.audio.transcriptions.create(
                model=TRANSCRIPTION_MODEL,
                file=audio_file,
            )

        return result.text
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/health")
def health():
    return jsonify({"ok": bool(os.getenv("GEMINI_API_KEY"))})


@app.route("/api/generate", methods=["POST"])
def generate():
    try:
        if not os.getenv("GEMINI_API_KEY"):
            return jsonify({
                "error": "GEMINI_API_KEY is missing. Add it to your .env file."
            }), 500

        transcript = request.form.get("transcript", "").strip()
        audio = request.files.get("audio")

        if audio and audio.filename:
            transcript = transcribe_audio(audio)

        if not transcript:
            return jsonify({
                "error": "Upload an audio file or paste a lecture transcript."
            }), 400

        if len(transcript) < 30:
            return jsonify({
                "error": "The transcript is too short. Please provide a little more lecture content."
            }), 400

        # Avoid accidentally sending extremely large pasted text to the model.
        # This keeps the MVP predictable for a hackathon demo.
        transcript = transcript[:120000]

        notes = generate_notes(transcript)

        return jsonify({
            "success": True,
            "transcript": transcript,
            "notes": notes,
        })

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/quiz", methods=["POST"])
def quiz():
    try:
        data = request.get_json(silent=True) or {}
        notes = data.get("notes")
        difficulty = data.get("difficulty", "mixed")
        count = int(data.get("count", 7))

        if not notes:
            return jsonify({"error": "No notes were supplied."}), 400

        count = max(3, min(count, 12))
        result = generate_quiz(notes, difficulty, count)

        return jsonify({"success": True, **result})

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.errorhandler(413)
def too_large(_):
    return jsonify({"error": "File is too large. Maximum size is 50 MB."}), 413


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
