import json
import os
import re
from pathlib import Path
from typing import Callable

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.5")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

LogFn = Callable[[str], None]


def ask_ai(instructions: str, prompt: str) -> str:
    response = client.responses.create(
        model=MODEL,
        instructions=instructions,
        input=prompt,
    )
    return response.output_text


def planner(requirement: str, log: LogFn | None = None) -> str:
    if log:
        log("🧠 Planner Agent — analyzing requirements...")
    return ask_ai(
        """You are the Planner Agent in an autonomous software engineering team.
Turn the user's software requirement into a concise implementation plan.
Include: features, files, user flow, testing strategy, and acceptance criteria.
Do not write the actual source code.""",
        requirement,
    )


def _extract_files(text: str) -> dict[str, str]:
    """
    Expected format:
    ===FILE: index.html===
    file contents
    ===END_FILE===
    """
    pattern = re.compile(
        r"===FILE:\s*(.+?)===\s*\n(.*?)\n===END_FILE===",
        re.DOTALL | re.IGNORECASE,
    )
    files = {}
    for match in pattern.finditer(text):
        path = match.group(1).strip().replace("\\", "/")
        content = match.group(2)
        if path and not path.startswith("/") and ".." not in Path(path).parts:
            files[path] = content
    return files


def coder(requirement: str, plan: str, workspace: Path, log: LogFn | None = None) -> dict[str, str]:
    if log:
        log("💻 Coder Agent — generating application files...")

    prompt = f"""
USER REQUIREMENT:
{requirement}

PLAN:
{plan}

Create a small, complete web application for this requirement.

Return ONLY files using exactly this format for every file:

===FILE: relative/path/to/file===
file contents
===END_FILE===

Rules:
- Keep the project small enough to run locally.
- Prefer a self-contained HTML/CSS/JavaScript application when suitable.
- Include an index.html for the main application when suitable.
- Include tests/test_app.py containing real Python tests that verify important generated functionality.
- Tests must use only Python's standard library unless absolutely necessary.
- Do not use markdown fences.
- Do not include explanations outside the file blocks.
"""
    raw = ask_ai(
        """You are the Coder Agent. You write production-quality but minimal code.
Your output is consumed by an automated file writer, so follow the requested file format exactly.""",
        prompt,
    )
    files = _extract_files(raw)

    if not files:
        raise RuntimeError("Coder returned no parseable files.")

    for relative, content in files.items():
        destination = workspace / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")

    return files


def tester(workspace: Path, log: LogFn | None = None) -> tuple[bool, str]:
    import subprocess
    import sys

    if log:
        log("🧪 Tester Agent — running automated tests...")

    test_file = workspace / "tests" / "test_app.py"
    if not test_file.exists():
        return False, "No tests/test_app.py was generated."

    completed = subprocess.run(
        [sys.executable, str(test_file)],
        cwd=str(workspace),
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = (completed.stdout + "\n" + completed.stderr).strip()

    if completed.returncode == 0:
        if log:
            log("🧪 Tester Agent — ✅ all tests passed.")
        return True, output
    else:
        if log:
            log("🧪 Tester Agent — ❌ tests failed.")
        return False, output


def debugger(
    requirement: str,
    workspace: Path,
    test_output: str,
    log: LogFn | None = None,
) -> dict[str, str]:
    if log:
        log("🐛 Debugger Agent — analyzing failure and applying fixes...")

    current_files = []
    for path in workspace.rglob("*"):
        if path.is_file() and ".git" not in path.parts:
            rel = path.relative_to(workspace).as_posix()
            if path.stat().st_size < 200_000:
                current_files.append(
                    f"\n===FILE: {rel}===\n{path.read_text(encoding='utf-8', errors='replace')}\n===END_FILE==="
                )

    prompt = f"""
USER REQUIREMENT:
{requirement}

TEST FAILURE:
{test_output}

CURRENT PROJECT:
{''.join(current_files)}

Find the root cause and fix the project.

Return ONLY files that need to be changed using:
===FILE: relative/path===
new file contents
===END_FILE===

Do not return unchanged files.
Do not use markdown fences.
"""
    raw = ask_ai(
        """You are the Debugger Agent. Diagnose failing tests, make the smallest reliable fix,
and return only the files that must change. Never hide the failure.""",
        prompt,
    )
    fixes = _extract_files(raw)

    if not fixes:
        raise RuntimeError("Debugger returned no parseable fixes.")

    for relative, content in fixes.items():
        destination = workspace / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")

    return fixes
