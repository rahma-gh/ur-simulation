#!/usr/bin/env python3
"""
prepare_inputs.py
Generates 2 dynamic inputs for the LLM:
  - ai_inputs/git_diff.txt       : what changed in the last commit
  - ai_inputs/test_history.txt   : all tests with their history and sensitivity
"""

import os
import json
import subprocess
import re

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT         = os.path.dirname(os.path.abspath(__file__))
STORE_PATH   = os.path.join(ROOT, "ai_inputs", "test_history_store.json")
OUTPUT_DIR   = os.path.join(ROOT, "ai_inputs")
TESTS_DIR    = os.path.join(ROOT, "tests")
CONTROLLERS  = [
    os.path.join(ROOT, "controllers", "ure_can_grasper", "ure_can_grasper.c"),
    os.path.join(ROOT, "controllers", "ure_supervisor",  "ure_supervisor.py"),
]

CATEGORIES = ["boundary", "functional", "integration", "performance",
              "reliability", "safety_limits", "stress"]

# ── Keywords for SENSITIVE_TO detection ─────────────────────────────────────
SENSITIVITY_KEYWORDS = {
    "speed":              [r"speed", r"vitesse_bras", r"wb_motor_set_velocity"],
    "TIME_STEP":          [r"TIME_STEP", r"timestep"],
    "target_positions":   [r"target_position", r"positions_cibles"],
    "distance_threshold": [r"distance_sensor", r"< 500", r"seuil.*capteur", r"capteur.*seuil"],
    "gripper_position":   [r"0\.85", r"finger.*joint", r"hand_motor", r"gripper_pos"],
    "wrist_threshold":    [r"wrist", r"\-2\.3", r"\-0\.1", r"position_sensor"],
    "HAUTEUR_SAISIE":     [r"HAUTEUR_SAISIE", r"hauteur.*saisie", r"grasped", r"grasp_event"],
    "DEPLACEMENT_DEPOT":  [r"DEPLACEMENT_DEPOT", r"deplacement.*depot", r"deposited", r"release_event"],
    "STEPS_STABLE":       [r"STEPS_STABLE", r"steps_stable"],
}

# ── Helpers ──────────────────────────────────────────────────────────────────

def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    return result.stdout.strip()


def get_git_diff():
    """Return structured info about the last commit."""
    commit_msg   = run(["git", "log", "-1", "--pretty=%s"])
    changed_files = run(["git", "diff", "HEAD~1", "HEAD", "--name-only"]).splitlines()
    diff_lines   = run(["git", "diff", "HEAD~1", "HEAD", "--", *CONTROLLERS])

    # Extract changed element and value from diff
    changed_element = "unknown"
    old_value, new_value = "?", "?"

    for line in diff_lines.splitlines():
        # Look for lines like: -    double speed = 1.0;  /  +    double speed = 0.0;
        m_old = re.search(r'^-.*?(\w+)\s*=\s*([0-9.\-]+)', line)
        m_new = re.search(r'^\+.*?(\w+)\s*=\s*([0-9.\-]+)', line)
        if m_old and not line.startswith("---"):
            changed_element = m_old.group(1)
            old_value = m_old.group(2)
        if m_new and not line.startswith("+++"):
            new_value = m_new.group(2)

    lines = []
    lines.append("=== GIT DIFF — LAST COMMIT ===")
    lines.append(f"COMMIT MESSAGE   : {commit_msg}")
    lines.append(f"MODIFIED FILES   : {', '.join(changed_files) if changed_files else 'none'}")
    lines.append(f"CHANGED ELEMENT  : {changed_element}")
    lines.append(f"OLD VALUE        : {old_value}")
    lines.append(f"NEW VALUE        : {new_value}")
    lines.append("")
    lines.append("--- RAW DIFF (only +/- lines) ---")
    for line in diff_lines.splitlines():
        if line.startswith(("+", "-")) and not line.startswith(("+++", "---")):
            lines.append(line)

    return "\n".join(lines)


def detect_sensitive(test_path):
    """Detect which constants/elements a test is sensitive to."""
    try:
        content = open(test_path).read()
    except Exception:
        return ["—"]

    found = []
    for element, patterns in SENSITIVITY_KEYWORDS.items():
        for pat in patterns:
            if re.search(pat, content, re.IGNORECASE):
                found.append(element)
                break

    return found if found else ["—"]


def get_test_history(test_id, store):
    """Extract FAIL, RUNS, FAILED_WHEN from the store for a given test."""
    entry = store.get(test_id, {})
    history = entry.get("history", [])
    runs = len(history)
    fails = sum(1 for h in history if h.get("result") == "FAILED")
    failed_when = list({
        f"{h['changed_element']}={h['value_at_change']}"
        for h in history if h.get("result") == "FAILED"
    })
    return runs, fails, failed_when


def generate_test_history(store):
    """Generate the formatted test_history.txt table."""
    lines = []
    header = f"{'TEST_ID':<55} | {'CATEGORY':<15} | {'FAIL':>4} | {'RUNS':>4} | {'SENSITIVE_TO':<45} | FAILED_WHEN"
    lines.append(header)
    lines.append("-" * len(header))

    for cat in CATEGORIES:
        cat_dir = os.path.join(TESTS_DIR, cat)
        if not os.path.isdir(cat_dir):
            continue
        for fname in sorted(os.listdir(cat_dir)):
            if not fname.startswith("test_") or not fname.endswith(".py"):
                continue
            test_id   = fname[:-3]
            test_path = os.path.join(cat_dir, fname)
            sensitive = detect_sensitive(test_path)
            runs, fails, failed_when = get_test_history(test_id, store)
            sensitive_str   = ", ".join(sensitive)
            failed_when_str = ", ".join(failed_when) if failed_when else "—"
            lines.append(
                f"{test_id:<55} | {cat:<15} | {fails:>4} | {runs:>4} | {sensitive_str:<45} | {failed_when_str}"
            )

    return "\n".join(lines)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Load store
    store = {}
    if os.path.exists(STORE_PATH):
        with open(STORE_PATH) as f:
            store = json.load(f)

    # Input 1 — git_diff.txt
    git_diff = get_git_diff()
    with open(os.path.join(OUTPUT_DIR, "git_diff.txt"), "w") as f:
        f.write(git_diff)
    print("✓ git_diff.txt generated")

    # Input 3 — test_history.txt
    test_history = generate_test_history(store)
    with open(os.path.join(OUTPUT_DIR, "test_history.txt"), "w") as f:
        f.write(test_history)
    print("✓ test_history.txt generated")

    print("\n=== PREVIEW git_diff.txt ===")
    print(git_diff[:500])
    print("\n=== PREVIEW test_history.txt (first 10 lines) ===")
    print("\n".join(test_history.splitlines()[:12]))


if __name__ == "__main__":
    main()