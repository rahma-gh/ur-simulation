#!/usr/bin/env python3
"""
update_store.py
---------------
Alimente le store (ai_inputs/test_history_store.json) avec les résultats
du dernier run de tests, en y injectant le contexte du commit courant.

Entrées attendues :
  - reports/test_results.json   : généré par conftest.py (passed/failed lists)
  - ai_inputs/git_diff.txt      : généré par prepare_inputs.py (optionnel)
  - git log                     : interrogé directement pour commit_message et fichiers changés

Sortie :
  - ai_inputs/test_history_store.json mis à jour (commit en tête de chaque historique)
"""

import os
import json
import subprocess
import sys

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT         = os.path.dirname(os.path.abspath(__file__))
STORE_PATH   = os.path.join(ROOT, "ai_inputs", "test_history_store.json")
RESULTS_PATH = os.path.join(ROOT, "reports", "test_results.json")
DIFF_PATH    = os.path.join(ROOT, "ai_inputs", "git_diff.txt")

CONTROLLERS = [
    "controllers/ure_can_grasper/ure_can_grasper.c",
    "controllers/ure_supervisor/ure_supervisor.py",
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    return result.stdout.strip()


def get_commit_context():
    """Retrieve commit message, changed files, and changed elements from git."""
    commit_message    = run(["git", "log", "-1", "--pretty=%s"])
    commit_sha        = run(["git", "log", "-1", "--pretty=%H"])[:12]
    changed_files     = run(["git", "diff", "HEAD~1", "HEAD", "--name-only"]).splitlines()

    # Detect changed elements (variable = value pairs) in controller diffs
    diff_lines = run(["git", "diff", "HEAD~1", "HEAD", "--"] + CONTROLLERS)

    import re
    old_vals, new_vals = {}, {}
    for line in diff_lines.splitlines():
        if line.startswith(("---", "+++")):
            continue
        m = re.search(r'(\w+)\s*=\s*([0-9.\-]+)', line)
        if not m:
            continue
        if line.startswith("-"):
            old_vals[m.group(1)] = m.group(2)
        elif line.startswith("+"):
            new_vals[m.group(1)] = m.group(2)

    changes = []
    for elem in old_vals:
        if elem in new_vals and old_vals[elem] != new_vals[elem]:
            changes.append({"element": elem, "old": old_vals[elem], "new": new_vals[elem]})

    # Fallback: list all touched elements if no clean pair found
    if not changes:
        for elem in set(list(old_vals) + list(new_vals)):
            changes.append({
                "element": elem,
                "old": old_vals.get(elem, "?"),
                "new": new_vals.get(elem, "?"),
            })

    return commit_message, commit_sha, changed_files, changes


def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path) as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"⚠  JSON decode error in {path}: {e}", file=sys.stderr)
    return default


def build_history_entry(test_name, result, commit_message, commit_sha,
                        changed_files, changes):
    """Build one history entry for a given test."""
    # Pick the most relevant changed_element for this test
    # (first change if multiple; empty string if no controller change detected)
    changed_element = changes[0]["element"] if changes else ""
    value_at_change = changes[0]["new"]     if changes else ""

    return {
        "commit_sha":            commit_sha,
        "commit_message":        commit_message,
        "source_files_changed":  changed_files,
        "changed_element":       changed_element,
        "value_at_change":       value_at_change,
        "all_changes":           changes,   # full list for traceability
        "result":                result,    # "PASSED" | "FAILED"
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # 1. Load existing store
    store = load_json(STORE_PATH, {})

    # 2. Load test results produced by conftest.py
    results = load_json(RESULTS_PATH, None)
    if results is None:
        print(f"✗ {RESULTS_PATH} not found — nothing to update.", file=sys.stderr)
        sys.exit(1)

    passed_tests = results.get("passed_tests", [])
    failed_tests = results.get("failed_tests", [])

    total_results = len(passed_tests) + len(failed_tests)
    if total_results == 0:
        print("⚠  test_results.json contains no test names — store unchanged.")
        sys.exit(0)

    # 3. Get git context (commit message, changed files, changed elements)
    commit_message, commit_sha, changed_files, changes = get_commit_context()

    print(f"📌 Commit  : {commit_sha}  — {commit_message}")
    print(f"📂 Files   : {', '.join(changed_files) if changed_files else 'none'}")
    print(f"🔧 Changes : {len(changes)} element(s) modified")
    for c in changes:
        print(f"     {c['element']}: {c['old']} → {c['new']}")
    print(f"🧪 Results : {len(passed_tests)} passed, {len(failed_tests)} failed")
    print()

    # 4. Update store: prepend new entry to each test's history
    updated = 0

    def upsert(test_name, result):
        nonlocal updated
        if test_name not in store:
            store[test_name] = {"test_id": test_name, "history": []}
        entry = build_history_entry(
            test_name, result,
            commit_message, commit_sha,
            changed_files, changes
        )
        store[test_name]["history"].insert(0, entry)
        updated += 1

    for name in passed_tests:
        upsert(name, "PASSED")

    for name in failed_tests:
        upsert(name, "FAILED")

    # 5. Persist store
    os.makedirs(os.path.dirname(STORE_PATH), exist_ok=True)
    with open(STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(store, f, indent=2, ensure_ascii=False)

    print(f"✅ Store updated : {updated} test(s) — {STORE_PATH}")
    print(f"   Total tests tracked in store: {len(store)}")


if __name__ == "__main__":
    main()
