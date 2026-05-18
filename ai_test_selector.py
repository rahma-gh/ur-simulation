#!/usr/bin/env python3

import os
import sys
import json
import argparse
import subprocess
import textwrap
import urllib.request
import urllib.error
import re
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.resolve()
AI_INPUTS    = PROJECT_ROOT / "ai_inputs"

HF_MODEL = "qwen3:4b"
HF_URL   = os.environ.get("OLLAMA_NGROK_URL", "http://localhost:11434").rstrip("/") + "/api/chat"

# ── LLM retry settings ───────────────────────────────────────
MAX_RETRIES     = 3   # number of times to retry on bad JSON or HTTP 503
RETRY_WAIT_SEC  = 5   # seconds between retries on bad JSON response

# ── Input size limits (see prepare_inputs.py for rationale) ──
MAX_DIFF_CHARS    = 20_000
MAX_HISTORY_CHARS = 40_000


def read_input(filename: str, max_chars: int) -> str:
    path = AI_INPUTS / filename
    if not path.exists():
        print(f"  [!] Missing file: {path}")
        print(f"      → Run first: python prepare_inputs.py")
        sys.exit(1)
    content = path.read_text(encoding="utf-8")
    if len(content) > max_chars:
        print(f"  [WARNING] {filename} truncated: {len(content):,} → {max_chars:,} chars")
        content = content[:max_chars] + f"\n\n... [TRUNCATED at {max_chars} chars]"
    return content


def load_all_inputs() -> dict:
    print("  [1/4] Reading ai_inputs/ files...")
    data = {
        "git_diff":      read_input("git_diff.txt",     MAX_DIFF_CHARS),
        "tests_history": read_input("tests_history.txt", MAX_HISTORY_CHARS),
    }
    for k, v in data.items():
        print(f"        ✓ {k:16s}  ({len(v):,} chars)")
    return data


# ══════════════════════════════════════════════════════════════
# SYSTEM PROMPT — written in English for best model compliance
# ══════════════════════════════════════════════════════════════
SYSTEM_PROMPT = textwrap.dedent("""\
    ## ROLE
    You are a test selection engine for an industrial cyber-physical system.
    The project is "ur-simulation": a Webots simulation of UR robotic arms
    that grasp cans from a conveyor belt.

    Your sole role: analyze what changed in the source code and decide
    which tests must be run on this push — as few as possible, but every
    test genuinely affected by the change.

    ## SOURCE FILES
    There are exactly 2 source files that control behavior:

      controllers/ure_can_grasper/ure_can_grasper.c
        C state machine with these independent elements:
          - speed            : arm speed (double speed = X.X)
          - TIME_STEP        : simulation interval (#define TIME_STEP 32)
          - structure        : states (WAITING/GRASPING/ROTATING/RELEASING/ROTATING_BACK)
                               and joint positions {-1.88, -2.14, -2.38, -1.51}
          - distance_threshold : distance sensor threshold (< 500)
          - wrist_threshold  : wrist position thresholds (-2.3, -0.1)
          - gripper_position : gripper close position (0.85)

      controllers/ure_supervisor/ure_supervisor.py
        Contains these independent constants:
          - HAUTEUR_SAISIE    : grasp detection height (0.80 m)
          - DEPLACEMENT_DEPOT : deposit detection distance (0.30 m)

      Tests read either the constants directly or the simulation_results.json
      file produced by the supervisor after simulation.

    ## WHAT YOU RECEIVE

    [GIT_DIFF]
      - Which source files changed (controllers/*.c or controllers/*.py)
      - The exact constant modified and its new value
      - The complete diff (+ and - lines)
      - Full source code of both controllers (for semantic context)

    [TESTS_HISTORY]
      A table with for each test:
      - TEST_ID      : exact identifier
      - CATEGORY     : functional | non_functional
      - SUBCATEGORY  : communication | safety | performance | stress | boundary | realtime
      - FAIL / RUNS  : number of failures over total runs
      - SENSITIVE_TO : exact constant this test checks
                       Format → file::constant
                       Example → ure_can_grasper::speed
                       Special value "ure_can_grasper::behavior | ure_supervisor::behavior"
                       → this test reads the JSON results and is affected by
                         ANY change in either source file
                       Value "—" → purely algorithmic test, never affected
      - FAILED_WHEN  : source file modified when this test failed in the past
                       "—" = has never failed

    ## SELECTION STEPS (follow in strict order)

    STEP 1 — Identify the changed element from GIT_DIFF
      Read "CHANGED ELEMENT" in the diff.
      Identify the source file AND the modified constant.
      Example: "speed changed 1.0 → 0.0" → element = ure_can_grasper::speed

    STEP 2 — Select tests (rules in priority order)

      RULE A — SENSITIVE_TO match (absolute priority)
        If SENSITIVE_TO contains the element identified in step 1
        → SELECT this test, even if FAIL=0 and FAILED_WHEN=—
        Match examples:
          - element = ure_can_grasper::speed
            match if SENSITIVE_TO contains "ure_can_grasper::speed"
          - element = speed (in ure_can_grasper.c)
            match if SENSITIVE_TO contains "ure_can_grasper::behavior" (global behavior)

      RULE B — SENSITIVE_TO = behavior (behavioral safety net)
        If SENSITIVE_TO = "ure_can_grasper::behavior | ure_supervisor::behavior"
        AND the modified source file is ure_can_grasper.c OR ure_supervisor.py
        → SELECT (these tests verify global behavior, affected by any change)

      RULE C — Historical safety net
        If FAILED_WHEN contains the modified source file
        AND the test is not already selected by A or B
        → SELECT (catches dependencies not detected statically)

      RULE D — Absolute exclusion
        If SENSITIVE_TO = "—" AND FAILED_WHEN = "—"
        → IGNORE unconditionally
        These tests are purely algorithmic (math, stress tests on fixed values).
        They cannot fail due to a source code change.

    STEP 3 — Prioritize selected tests
      Group 1 (run first) : SUBCATEGORY = safety
      Group 2             : SUBCATEGORY = communication | functional tests without subcategory
      Group 3             : SUBCATEGORY = performance | boundary | realtime
      Group 4 (run last)  : SUBCATEGORY = stress

      Within each group, sort by FAIL/RUNS ratio descending
      (highest failure rate = highest priority within group).
      Assign unique integers starting from 1.

    ## VERIFICATION BEFORE RESPONDING
      [ ] Every test with a SENSITIVE_TO matching the changed element is selected
      [ ] Every test with SENSITIVE_TO = "—" AND FAILED_WHEN = "—" is ignored
      [ ] No invented test_id — all come exactly from TESTS_HISTORY
      [ ] Priorities are unique integers starting from 1
      [ ] skipped_count = total tests in TESTS_HISTORY - number selected

    ## OUTPUT FORMAT
    Return ONLY a valid JSON object.
    No text before. No text after. No markdown fences. Raw JSON only.

    {
      "selected_tests": [
        {
          "test_id":     "<exact identifier from TESTS_HISTORY>",
          "priority":    <integer, 1 = run first>,
          "category":    "<functional | non_functional>",
          "subcategory": "<communication | safety | performance | stress | boundary | realtime>",
          "reason":      "<one sentence: which constant changed + what this test verifies>",
          "rule":        "<RULE A | RULE B | RULE C>"
        }
      ],
      "skipped_count":        <integer>,
      "diff_summary":         "<one sentence: file changed + nature of change>",
      "selection_rationale":  "<2 sentences: how many selected per rule A vs B vs C, and why>"
    }

    ## EXAMPLE
    GIT_DIFF shows: speed changed from 1.0 to 0.0 in ure_can_grasper.c

    TESTS_HISTORY contains:
      test_vitesse_bras_securisee   SENSITIVE_TO: ure_can_grasper::speed          FAILED_WHEN: —
      test_arm_rotates              SENSITIVE_TO: ure_can_grasper::behavior | ... FAILED_WHEN: ure_can_grasper
      test_boundary_joint_zero      SENSITIVE_TO: —                               FAILED_WHEN: —
      test_timestep_conforme        SENSITIVE_TO: ure_can_grasper::TIME_STEP      FAILED_WHEN: —

    Correct selection:
      SELECT test_vitesse_bras_securisee → RULE A (SENSITIVE_TO::speed matches)
      SELECT test_arm_rotates            → RULE B (behavior + modified source file)
      IGNORE test_boundary_joint_zero    → RULE D (— and —)
      IGNORE test_timestep_conforme      → RULE A does not apply (TIME_STEP ≠ speed)

    ## WHAT YOU MUST NEVER DO
    - Invent a test_id that does not exist in TESTS_HISTORY
    - Select ALL tests — being selective is correct and expected
    - Select a test whose SENSITIVE_TO does not match the changed element
      and whose FAILED_WHEN is "—"
    - Assign the same priority number to two different tests
    - Add any text outside the JSON object
    - Return invalid JSON or JSON missing the "selected_tests" key
""")


def build_user_prompt(inputs: dict) -> str:
    return textwrap.dedent(f"""\
        Here are the context files for the current push.
        Analyze them and produce the test selection JSON.

        ═══════════════════════════════════════════════════════════
        [GIT_DIFF]
        ═══════════════════════════════════════════════════════════
        {inputs['git_diff']}

        ═══════════════════════════════════════════════════════════
        [TESTS_HISTORY]
        ═══════════════════════════════════════════════════════════
        {inputs['tests_history']}

        ═══════════════════════════════════════════════════════════
        CRITICAL: Return ONLY a valid JSON object.
        The root key MUST be "selected_tests".
        No text before. No text after. No markdown fences.
        Every selected test MUST include a "rule" field (RULE A, RULE B, or RULE C).
        ═══════════════════════════════════════════════════════════
    """)


def call_llm_once(system: str, user: str) -> str:
    """Single LLM call. Returns raw response string."""
    ngrok_url = os.environ.get("OLLAMA_NGROK_URL", "").strip()
    if not ngrok_url:
        print("\n  [!] OLLAMA_NGROK_URL not set.")
        print("      Run ngrok on your PC: ngrok http 11434")
        print("      Then add the URL to GitHub Secrets: OLLAMA_NGROK_URL=https://abc123.ngrok-free.app")
        sys.exit(1)

    payload = json.dumps({
        "model": HF_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        "stream": False,
        "options": {"temperature": 0.0},   # deterministic output for reproducibility
    }).encode("utf-8")

    req = urllib.request.Request(
        HF_URL,
        data=payload,
        headers={
            "Content-Type":               "application/json",
            "User-Agent":                 "ur-simulation-ci/2.0",
            "ngrok-skip-browser-warning": "true",
        },
        method="POST",
    )

    HTTP_RETRIES = 5
    for attempt in range(1, HTTP_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            if e.code == 503 and attempt < HTTP_RETRIES:
                wait = attempt * 10
                print(f"  [!] Server overloaded (503) — retry {attempt}/{HTTP_RETRIES-1} in {wait}s...")
                time.sleep(wait)
                continue
            print(f"\n  [!] HTTP error {e.code}")
            print(f"      Body: {err_body[:1000]}")
            sys.exit(1)
        except urllib.error.URLError as e:
            print(f"\n  [!] Network error: {e.reason}")
            sys.exit(1)

    raw = body["message"]["content"].strip()
    print(f"        ✓ model used     — {body.get('model', HF_MODEL)}")
    print(f"        ✓ tokens used    — prompt: {body.get('prompt_eval_count','?')}  "
          f"completion: {body.get('eval_count','?')}")
    return raw


def call_llm(system: str, user: str, verbose: bool) -> str:
    """
    Calls the LLM up to MAX_RETRIES times, retrying on bad JSON.
    This ensures the pipeline never silently accepts a weak/incomplete AI response.
    """
    print(f"  [2/4] Sending to LLM: {HF_MODEL} ...")

    for attempt in range(1, MAX_RETRIES + 1):
        raw = call_llm_once(system, user)

        if verbose:
            print(f"\n  ── Raw LLM response (attempt {attempt}) ──")
            print(raw[:3000])
            print("  ─────────────────────────────────────────\n")

        # Quick pre-check: does the response look like JSON?
        cleaned = _clean_raw(raw)
        if cleaned.startswith("{"):
            return raw  # looks valid, let parse_llm_response handle the rest

        if attempt < MAX_RETRIES:
            print(f"  [!] Response does not look like JSON (attempt {attempt}/{MAX_RETRIES}) — retrying in {RETRY_WAIT_SEC}s...")
            print(f"      First 200 chars: {raw[:200]}")
            time.sleep(RETRY_WAIT_SEC)
        else:
            print(f"\n  [!] LLM did not return valid JSON after {MAX_RETRIES} attempts.")
            print(f"      Last response (500 chars): {raw[:500]}")
            sys.exit(1)

    return raw   # unreachable but keeps linters happy


def _clean_raw(raw: str) -> str:
    """Strip <thinking> blocks and markdown fences from raw LLM output."""
    cleaned = re.sub(r"<thinking>[\s\S]*?</thinking>", "", raw).strip()
    if "```" in cleaned:
        m = re.search(r"```(?:json)?\s*([\s\S]+?)```", cleaned)
        if m:
            cleaned = m.group(1).strip()
    m = re.search(r"\{[\s\S]+\}", cleaned)
    if m:
        cleaned = m.group(0)
    return cleaned


# ══════════════════════════════════════════════════════════════
# STRICT JSON VALIDATION
# The old code silently accepted weak/fallback formats and
# repaired truncated JSON. This version:
#   1. Rejects invalid JSON and retries the LLM call
#   2. Validates the schema strictly
#   3. Never silently accepts missing fields
# ══════════════════════════════════════════════════════════════
REQUIRED_ROOT_KEYS    = {"selected_tests", "skipped_count", "diff_summary", "selection_rationale"}
REQUIRED_TEST_KEYS    = {"test_id", "priority", "category", "subcategory", "reason", "rule"}
VALID_RULES           = {"RULE A", "RULE B", "RULE C"}
VALID_CATEGORIES      = {"functional", "non_functional"}
VALID_SUBCATEGORIES   = {"communication", "safety", "performance", "stress", "boundary", "realtime", "—", ""}


def validate_schema(data: dict) -> list[str]:
    """
    Returns a list of validation errors.
    Empty list = schema is valid.
    """
    errors = []

    missing_root = REQUIRED_ROOT_KEYS - set(data.keys())
    if missing_root:
        errors.append(f"Missing root keys: {missing_root}")

    if "selected_tests" not in data:
        return errors  # can't validate further

    if not isinstance(data["selected_tests"], list):
        errors.append("'selected_tests' must be a list")
        return errors

    priorities_seen = set()
    for i, t in enumerate(data["selected_tests"]):
        prefix = f"selected_tests[{i}]"
        if not isinstance(t, dict):
            errors.append(f"{prefix}: must be a dict, got {type(t).__name__}")
            continue

        missing = REQUIRED_TEST_KEYS - set(t.keys())
        if missing:
            errors.append(f"{prefix}: missing keys {missing}")

        if "priority" in t:
            p = t["priority"]
            if not isinstance(p, int):
                errors.append(f"{prefix}: 'priority' must be int, got {type(p).__name__}")
            elif p in priorities_seen:
                errors.append(f"{prefix}: duplicate priority {p}")
            else:
                priorities_seen.add(p)

        if "rule" in t and t["rule"] not in VALID_RULES:
            errors.append(f"{prefix}: invalid rule '{t['rule']}', expected one of {VALID_RULES}")

        if "category" in t and t["category"] not in VALID_CATEGORIES:
            errors.append(f"{prefix}: invalid category '{t['category']}'")

        if "subcategory" in t and t["subcategory"] not in VALID_SUBCATEGORIES:
            # subcategory is a soft warning, not a hard error
            pass  # accept any value — the model may use variant names

    if not isinstance(data.get("skipped_count", 0), int):
        errors.append("'skipped_count' must be an integer")

    return errors


def parse_llm_response(raw: str, system: str, user: str, verbose: bool) -> dict:
    """
    Parses and strictly validates the LLM response.
    Retries the LLM call if validation fails (up to MAX_RETRIES).
    """
    print("  [3/4] Parsing and validating LLM response...")

    for attempt in range(1, MAX_RETRIES + 1):
        cleaned = _clean_raw(raw)

        # 1. Parse JSON
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            print(f"  [!] Invalid JSON (attempt {attempt}/{MAX_RETRIES}): {e}")
            print(f"      First 300 chars: {cleaned[:300]}")
            if attempt < MAX_RETRIES:
                print(f"      Retrying LLM call in {RETRY_WAIT_SEC}s...")
                time.sleep(RETRY_WAIT_SEC)
                raw = call_llm_once(system, user)
                if verbose:
                    print(f"\n  ── Retry {attempt} raw response ──")
                    print(raw[:2000])
                    print("  ─────────────────────────────────\n")
                continue
            else:
                print(f"\n  [!] LLM returned invalid JSON after {MAX_RETRIES} attempts. Aborting.")
                sys.exit(1)

        # 2. Validate schema
        errors = validate_schema(data)
        if errors:
            print(f"  [!] Schema validation failed (attempt {attempt}/{MAX_RETRIES}):")
            for err in errors:
                print(f"      - {err}")
            if attempt < MAX_RETRIES:
                print(f"      Retrying LLM call in {RETRY_WAIT_SEC}s...")
                time.sleep(RETRY_WAIT_SEC)
                raw = call_llm_once(system, user)
                if verbose:
                    print(f"\n  ── Retry {attempt} raw response ──")
                    print(raw[:2000])
                    print("  ─────────────────────────────────\n")
                continue
            else:
                print(f"\n  [!] LLM response failed schema validation after {MAX_RETRIES} attempts.")
                print(f"      Validation errors: {errors}")
                sys.exit(1)

        # 3. All good — normalize and return
        data["selected_tests"].sort(key=lambda t: t.get("priority", 999))
        print(f"        ✓ JSON valid and schema OK ({len(data['selected_tests'])} tests selected)")
        return data

    # Should not reach here
    sys.exit(1)


# ══════════════════════════════════════════════════════════════
# DETERMINISTIC SELECTION REPORT
# Shows exactly why each test was selected, which rule applied,
# and what changed — making results explainable and debuggable.
# ══════════════════════════════════════════════════════════════
def display_plan(data: dict) -> None:
    selected  = data["selected_tests"]
    skipped   = data.get("skipped_count", "?")
    diff_sum  = data.get("diff_summary", "")
    rationale = data.get("selection_rationale", "")

    # Count per rule
    rule_counts = {}
    for t in selected:
        rule = t.get("rule", "?")
        rule_counts[rule] = rule_counts.get(rule, 0) + 1

    print()
    print("  " + "=" * 80)
    print(f"  AI TEST SELECTION REPORT — {HF_MODEL}")
    print("  " + "=" * 80)
    if diff_sum:
        print(f"\n  Change    : {diff_sum}")
    if rationale:
        print(f"  Analysis  : {rationale}")

    print(f"\n  Selected  : {len(selected)} tests   |   Skipped: {skipped}")
    if rule_counts:
        rule_summary = "  |  ".join(f"{rule}: {count}" for rule, count in sorted(rule_counts.items()))
        print(f"  By rule   : {rule_summary}")

    print()
    print(f"  {'PRIO':<5}  {'RULE':<8}  {'CATEGORY':<16}  {'SUBCATEGORY':<14}  {'TEST_ID'}")
    print(f"  {'':5}  {'':8}  {'':16}  {'':14}  {'REASON'}")
    print("  " + "─" * 100)

    for t in selected:
        test_id  = t['test_id']
        priority = t['priority']
        rule     = t.get('rule', '?')
        cat      = t.get('category', '')
        sub      = t.get('subcategory', '')
        reason   = t.get('reason', '')

        print(f"  {priority:<5}  {rule:<8}  {cat:<16}  {sub:<14}  {test_id}")
        print(f"  {'':5}  {'':8}  {'':16}  {'':14}  → {reason}")
        print()

    print("  " + "─" * 100)
    print()


def build_pytest_args(selected_tests: list) -> list:
    test_dir  = PROJECT_ROOT / "tests"
    args      = []
    not_found = []

    for entry in selected_tests:
        tid     = entry["test_id"]
        matches = list(test_dir.rglob(f"{tid}.py"))
        if matches:
            args.append(str(matches[0].relative_to(PROJECT_ROOT)))
        else:
            not_found.append(tid)

    if not_found:
        print(f"  [!] Tests not found on disk (skipped): {not_found}")

    return args


def run_tests(pytest_args: list, dry_run: bool, verbose: bool) -> int:
    print("  [4/4] Running selected tests...")
    print()

    cmd = [sys.executable, "-m", "pytest"] + pytest_args + [
        "-v",
        "--tb=short",
        "--html=reports/ai_selected_report.html",
        "--self-contained-html",
    ]
    if verbose:
        cmd.append("-s")

    print("  Command:", " ".join(cmd))
    print()

    if dry_run:
        print("  [dry-run] No tests launched (--dry-run active).")
        return 0

    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    return result.returncode


def save_selection_log(data: dict) -> None:
    log_path = AI_INPUTS / "last_selection.json"
    log = {
        "model":               HF_MODEL,
        "selected":            data["selected_tests"],
        "skipped":             data.get("skipped_count"),
        "diff_summary":        data.get("diff_summary"),
        "selection_rationale": data.get("selection_rationale"),
    }
    log_path.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  ✓ Selection saved: ai_inputs/last_selection.json")


def main():
    parser = argparse.ArgumentParser(
        description="Intelligent test selection and prioritization via LLM."
    )
    parser.add_argument("--dry-run",      action="store_true",
                        help="Display the plan without launching pytest.")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show raw LLM response.")
    parser.add_argument("--skip-prepare", action="store_true",
                        help="Skip prepare_inputs.py.")
    args = parser.parse_args()

    print()
    print("=" * 70)
    print("  AI TEST SELECTOR — ur-simulation")
    print(f"  Model : {HF_MODEL} (Ollama local via ngrok)")
    print("=" * 70)
    print()

    # 0. Regenerate inputs
    if not args.skip_prepare:
        print("  [0/4] Regenerating inputs (prepare_inputs.py)...")
        r = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "prepare_inputs.py")],
            cwd=PROJECT_ROOT,
        )
        if r.returncode != 0:
            print("  [!] prepare_inputs.py failed.")
            sys.exit(1)
        print()

    # 1. Load inputs
    inputs = load_all_inputs()
    print()

    # 2. Build prompts
    system = SYSTEM_PROMPT
    user   = build_user_prompt(inputs)

    # 3. Call LLM (with retry on bad JSON)
    raw_response = call_llm(system, user, args.verbose)
    print()

    # 4. Parse + validate (strict, with retry)
    selection = parse_llm_response(raw_response, system, user, args.verbose)
    print()

    # 5. Display deterministic selection report
    display_plan(selection)

    # 6. Save
    save_selection_log(selection)
    print()

    # 7. Build pytest args
    pytest_args = build_pytest_args(selection["selected_tests"])
    if not pytest_args:
        print("  No tests to run (all skipped or not found on disk).")
        return 0

    # 8. Run
    exit_code = run_tests(pytest_args, args.dry_run, args.verbose)

    print()
    if exit_code == 0:
        print("  ✓ All selected tests passed.")
    else:
        print(f"  ✗ Some tests failed (exit code {exit_code}).")
    print()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())