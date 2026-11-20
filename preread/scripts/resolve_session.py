#!/usr/bin/env python3
"""Resolve an existing curriculum lecture without creating or changing files."""
import argparse
import json
from pathlib import Path


def repo_root():
    for path in Path(__file__).resolve().parents:
        if (path / "curriculum-index.json").is_file():
            return path
    raise ValueError("Run from a curriculum checkout containing curriculum-index.json")


def resolve(root, batch_id, session_id, module_id=None):
    data = json.loads((root / "curriculum-index.json").read_text())
    batches = [b for b in data["batches"] if b["batch"] == batch_id]
    if not batches:
        raise ValueError("Unknown batch: " + batch_id)
    matches = []
    for module in batches[0]["modules"]:
        if module_id is not None and module["module_id"].lower() != module_id.lower():
            continue
        for session in module["sessions"]:
            if str(session["source_session"]) != session_id:
                continue
            directory = (root / session["path"]).resolve()
            if not directory.is_relative_to(root.resolve()):
                raise ValueError("Indexed output path escapes the repository")
            matches.append({"batch_id": batch_id, "module_id": module["module_id"],
                            "module_name": module["title"], "session_id": session_id,
                            "session_name": session["title"], "output_directory": str(directory),
                            "output_path": str(directory / "pre-read.md"),
                            "status": session.get("status", "unknown")})
    if not matches:
        raise ValueError("Session not found in confirmed curriculum; do not infer a new session")
    if len(matches) != 1:
        choices = ", ".join(m["module_id"] + ": " + m["session_name"] for m in matches)
        raise ValueError("Ambiguous session; supply --module. Matches: " + choices)
    return matches[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", required=True)
    parser.add_argument("--session", required=True)
    parser.add_argument("--module")
    args = parser.parse_args()
    try:
        result = resolve(repo_root(), args.batch, args.session, args.module)
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as error:
        print(json.dumps({"ok": False, "error": str(error)}))
        return 1
    print(json.dumps({"ok": True, **result}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
