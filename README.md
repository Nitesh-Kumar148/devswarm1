# DevSwarm

A small autonomous AI engineering team for a hackathon.

## Flow

User Requirement -> Planner -> Coder -> Tester -> Debugger -> Retest

The system runs up to three test/fix cycles.

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:
   `.\venv\Scripts\python.exe -m pip install -r requirements.txt`
3. Copy `.env.example` to `.env`.
4. Put your OpenAI API key in `.env`.
5. Start:
   `.\venv\Scripts\python.exe -m streamlit run app.py`

## Demo

Use:

> Build a simple To-Do web application with add, delete and complete-task functionality.

After the build succeeds, open `workspace/index.html` in Chrome.

Never commit `.env` or expose your API key.
