from pathlib import Path
import shutil
from typing import Callable

from agents import planner, coder, tester, debugger

WORKSPACE = Path(__file__).resolve().parent / "workspace"
MAX_ATTEMPTS = 3


def run_pipeline(requirement: str, log: Callable[[str], None]) -> dict:
    # Start with a clean workspace for each build.
    if WORKSPACE.exists():
        shutil.rmtree(WORKSPACE)
    WORKSPACE.mkdir(parents=True, exist_ok=True)

    log("🚀 DevSwarm started.")
    plan = planner(requirement, log)

    log("🏗️ Plan created.")
    coder(requirement, plan, WORKSPACE, log)

    last_output = ""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        log(f"🔁 Test cycle {attempt}/{MAX_ATTEMPTS}")
        passed, output = tester(WORKSPACE, log)
        last_output = output

        if passed:
            log("🔐 Quality gate — tests passed.")
            log("🚀 Build complete.")
            return {
                "success": True,
                "attempts": attempt,
                "workspace": str(WORKSPACE),
                "test_output": output,
            }

        if attempt < MAX_ATTEMPTS:
            debugger(requirement, WORKSPACE, output, log)
        else:
            log("🛑 Maximum debugging attempts reached.")

    return {
        "success": False,
        "attempts": MAX_ATTEMPTS,
        "workspace": str(WORKSPACE),
        "test_output": last_output,
        "error": "Tests did not pass within the maximum number of attempts.",
    }
