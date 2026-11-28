#!/usr/bin/env python3
"""Report curriculum runtime capabilities without reading or copying credentials."""
import argparse
import importlib.util
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time


def command_result(command):
    started = time.monotonic()
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=20)
        return {"available": result.returncode == 0, "seconds": round(time.monotonic() - started, 2)}
    except (OSError, subprocess.TimeoutExpired):
        return {"available": False, "seconds": round(time.monotonic() - started, 2)}


def inspect_environment():
    cli = shutil.which("codex")
    bundled = Path("/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex")
    if not cli and bundled.is_file():
        cli = str(bundled)
    auth = command_result([cli, "login", "status"]) if cli else {"available": False}
    return {
        "system": platform.system(),
        "python": sys.version.split()[0],
        "codex_cli": bool(cli),
        "codex_login_available": auth,
        "imports": {name: importlib.util.find_spec(name) is not None
                    for name in ("numpy", "pandas", "matplotlib", "seaborn")},
        "tools": {name: bool(shutil.which(name)) for name in ("mmdc", "node", "mysql", "gh")},
        "model_policy": json.loads((Path(__file__).resolve().parents[1] /
                                    "automation/model-policy.json").read_text()),
        "live_model_timing": "unmeasured",
        "required_benchmark": "Same batch, models, effort, dependencies and verification in each environment",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print(json.dumps(inspect_environment(), indent=2))
