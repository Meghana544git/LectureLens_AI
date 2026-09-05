# LectureLens AI

An AI-powered web application that turns lecture recordings or transcripts into:

- Structured study notes
- Headings and subheadings
- Key definitions
- Important/exam-relevant highlights
- Auto-generated Mermaid flowcharts for process-based lectures
- "Quiz Me on This Lecture" mode
- Instant quiz feedback
- Browser print / Save as PDF

This project follows the hackathon brief: audio/transcript input, speech-to-text,
LLM-based structured notes, definitions, highlights, quiz mode, and the optional
diagram feature.

## Tech stack

- Frontend: HTML, CSS, JavaScript
- Backend: Python + Flask
- Speech-to-text: Gemini Whisper API
- LLM: Gemini API
- Diagrams: Mermaid.js
- Storage: none for the MVP, so setup is simple

## 1. Install Python

Python 3.10+ is recommended.

Check:

```powershell
python --version
```

## 2. Open the project in VS Code

Open the `lecture_study_notes_ai` folder.

## 3. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

## 4. Install dependencies

```powershell
pip install -r requirements.txt
```

## 5. Create your .env file

Copy `.env.example` and rename the copy to:

```text
.env
```

Put your API key in it:

```text
GEMINI_API_KEY=your_real_key_here
```

Do NOT upload `.env` to GitHub. It is already included in `.gitignore`.

## 6. Start the app

```powershell
python app.py
```

You should see Flask running on:

```text
http://127.0.0.1:5000
```

Open that address in your browser.

## 7. Test it

### Fastest test

Paste a transcript such as:

"Today we will learn the software development life cycle. The first stage is
planning, where requirements are identified. Next is analysis, followed by
design. During implementation developers write the code. Testing checks the
software for errors. Finally deployment makes the system available to users,
and maintenance handles future changes."

Click:

**Generate Study Notes**

The app should create:

- Overview
- Important points
- Structured sections
- Definitions
- A lifecycle flowchart
- Quiz mode

### Audio test

Upload a short MP3/WAV/M4A lecture.

For a hackathon demo, use a 5-10 minute recording so processing is fast.

## Project structure

```text
lecture_study_notes_ai/
│
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
│
├── templates/
│   └── index.html
│
└── static/
```

## How the application works

```text
Audio / Transcript
        ↓
Speech-to-Text (if audio)
        ↓
Lecture Transcript
        ↓
Gemini LLM
        ↓
Structured JSON
   ↙    ↓     ↘
Notes Definitions Highlights
        ↓
 Mermaid Diagram (if process exists)
        ↓
 Quiz Generator
        ↓
 Interactive Feedback
```

## Important security rule

Never hard-code an API key inside `app.py` or JavaScript.

Never commit `.env` to GitHub.

If an API key is accidentally exposed, revoke/rotate it immediately.

## Common errors

### "GEMINI_API_KEY is missing"

Make sure:

1. The file is named `.env`, not `.env.txt`.
2. It is in the same folder as `app.py`.
3. It contains `GEMINI_API_KEY=...`.
4. Restart `python app.py`.

### ModuleNotFoundError

Activate the virtual environment and run:

```powershell
pip install -r requirements.txt
```

### Port already in use

Change the last line of `app.py` from:

```python
app.run(debug=True, host="127.0.0.1", port=5000)
```

to another port such as:

```python
app.run(debug=True, host="127.0.0.1", port=5001)
```

Then open:

```text
http://127.0.0.1:5001
```

## Hackathon demo flow

1. Open the app.
2. Paste or upload a short lecture.
3. Click Generate Study Notes.
4. Show the clean headings and important points.
5. Scroll to Key Definitions.
6. Show the automatically generated process diagram.
7. Click Quiz Me on This Lecture.
8. Answer questions.
9. Click Check My Answers.
10. Show instant feedback.
11. Use Print / Save as PDF if judges ask about export.

## Features mapped to the brief

Must-have:
- Audio/transcript upload: yes
- Speech-to-text: yes
- AI structured notes: yes
- Definitions: yes
- Highlights: yes
- Quiz mode: yes
- Clean UI: yes

Stretch:
- Mermaid diagrams: yes
- PDF export: browser Print / Save as PDF
- Difficulty levels: yes
- Timestamp linking: not included in this MVP
- Database: intentionally omitted to keep the hackathon MVP simple

## Future upgrades

- Store lectures and notes in SQLite/Firebase
- User login
- Timestamped transcript segments
- Click a note to jump to audio timestamp
- Flashcards
- Spaced repetition
- Multiple languages
- Lecture history
- Teacher/student dashboards
- Chunk very long lectures and summarize each chunk
- Use an open-source local Whisper model to reduce API costs
