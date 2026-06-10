#!/usr/bin/env python3
"""
ai_test_selector.py
Sends the 3 inputs to the LLM (Groq API) and returns
the prioritized list of tests to execute.
"""

import os
import sys
import json
import re
import requests

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT         = os.path.dirname(os.path.abspath(__file__))
AI_INPUTS    = os.path.join(ROOT, "ai_inputs")
DEPS_PATH    = os.path.join(ROOT, "ai_inputs", "dependencies.json")

# ── LLM Config ───────────────────────────────────────────────────────────────
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_URL     = "https://api.groq.com/openai/v1/chat/completions"
MODEL        = "llama-3.3-70b-versatile"
TIMEOUT      = 60

# ── Priority order for categories ────────────────────────────────────────────
CATEGORY_PRIORITY = {
    "safety_limits": 1,
    "functional":    2,
    "integration":   3,
    "boundary":      4,
    "performance":   5,
    "reliability":   6,
    "stress":        7,
}

# ── System Prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert test selection and prioritization engine for a Webots cyber-physical simulation system.

The system controls a UR robotic arm that grasps and deposits cans using two controllers:
- ure_can_grasper.c  : state machine (WAITING → GRASPING → ROTATING → RELEASING → ROTATING_BACK)
- ure_supervisor.py  : monitors heights and positions, writes simulation_results.json

Your task: given one or more code changes, select and prioritize only the relevant tests from the full test suite.

=== SELECTION RULES ===
Select a test if AT LEAST ONE of these conditions is true for ANY of the changed elements:

S1 - DIRECT LINK: the test directly checks the constant or function that changed.
S2 - DEPENDENCY LINK: the test checks a behavior listed in the impacts of the changed element in the dependencies file.
S3 - HISTORY LINK: the test has previously FAILED when this same element was changed (FAILED_WHEN column).

Do NOT select a test if none of S1, S2, S3 applies to any changed element.

=== PRIORITIZATION RULES ===
Order selected tests by:

P1 - CATEGORY PRIORITY (highest to lowest):
     safety_limits > functional > integration > boundary > performance > reliability > stress

P2 - FAILURE HISTORY: within the same category, tests with FAILED_WHEN matching any current change come first.

P3 - FAIL RATE: within the same category and same FAILED_WHEN status, higher FAIL/RUNS ratio comes first.

=== OUTPUT FORMAT ===
Respond ONLY with a valid JSON object. No text before or after. No markdown. No explanation.
Exact format:
{
  "selected_tests": [
    {
      "test_id": "test_name_here",
      "category": "category_here",
      "priority": 1,
      "reason": "brief reason in English (max 10 words)"
    }
  ],
  "total_selected": <number>,
  "changed_elements": ["element1", "element2"],
  "reasoning_summary": "one sentence explaining the selection logic"
}
"""


def load_input(filename):
    path = os.path.join(AI_INPUTS, filename)
    if not os.path.exists(path):
        print(f"ERROR: {path} not found. Run prepare_inputs.py first.")
        sys.exit(1)
    with open(path) as f:
        return f.read()


def extract_changed_elements(git_diff_text):
    """Extract ALL changed element names from git_diff.txt — supports multiple changes.

    Handles both simple names (speed, HAUTEUR_SAISIE) and
    array-indexed names (target_positions[2], gripper_position).
    """
    elements = []
    for line in git_diff_text.splitlines():
        # Matches lines like:
        #   "  - speed                    : 1.0 → 0.0"
        #   "  - target_positions[2]      : -2.38 → -1.80"
        #   "  - gripper_position         : 0.85 → 0.70"
        m = re.match(r"\s*-\s+([\w\[\]]+)\s*:", line)
        if m:
            name = m.group(1)
            # Normalise: strip index for dep-map lookup (target_positions[2] -> target_positions)
            base = re.sub(r'\[\d+\]', '', name)
            if base not in elements:
                elements.append(base)
            # Also keep the indexed form so the LLM sees the exact slot
            if name != base and name not in elements:
                elements.append(name)
    return elements if elements else []


def filter_deps(deps, changed_elements):
    """Return only the impacts relevant to ALL changed elements."""
    if not changed_elements:
        return deps

    filtered = {}
    for file_deps in deps.values():
        for element in changed_elements:
            if element in file_deps:
                filtered[element] = file_deps[element]

    return filtered if filtered else deps


def build_user_prompt():
    git_diff     = load_input("git_diff.txt")
    test_history = load_input("test_history.txt")

    if not os.path.exists(DEPS_PATH):
        print(f"ERROR: {DEPS_PATH} not found.")
        sys.exit(1)
    with open(DEPS_PATH) as f:
        deps = json.load(f)

    # Extract ALL changed elements and filter dependencies for all of them
    changed_elements = extract_changed_elements(git_diff)
    filtered_deps    = filter_deps(deps, changed_elements)

    print(f"  Changed elements : {changed_elements}")
    print(f"  Deps sent        : {list(filtered_deps.keys())}")

    return f"""=== INPUT 1: GIT DIFF (what changed) ===
{git_diff}

=== INPUT 2: DEPENDENCY MAP (what the changes impact) ===
{json.dumps(filtered_deps, indent=2)}

=== INPUT 3: TEST HISTORY (all tests + sensitivity + past failures) ===
{test_history}

Now apply the selection and prioritization rules. Return ONLY the JSON object.
"""


def call_llm(user_prompt):
    if not GROQ_API_KEY:
        print("ERROR: GROQ_API_KEY environment variable is not set.")
        sys.exit(1)

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_prompt},
        ],
        "temperature": 0.1,
        "max_tokens":  2000,
    }

    headers = {
        "Content-Type":  "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}",
    }

    print(f"Calling Groq API (model: {MODEL}) ...")
    try:
        response = requests.post(GROQ_URL, json=payload, headers=headers, timeout=TIMEOUT)
        print(f"Status: {response.status_code}")
        response.raise_for_status()
    except requests.exceptions.Timeout:
        print("ERROR: Groq request timed out.")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Groq request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text[:500]}")
        sys.exit(1)

    data = response.json()
    return data["choices"][0]["message"]["content"]


def parse_and_validate(raw):
    """Extract and validate JSON from LLM response."""
    raw = raw.strip()
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    if raw.startswith("```"):
        raw = "\n".join(raw.split("\n")[1:])
    if raw.endswith("```"):
        raw = "\n".join(raw.split("\n")[:-1])
    raw = raw.strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"ERROR: LLM returned invalid JSON: {e}")
        print("Raw response:", raw[:500])
        sys.exit(1)

    if "selected_tests" not in result:
        print("ERROR: Missing 'selected_tests' key in LLM response.")
        sys.exit(1)

    tests = result["selected_tests"]
    for i, t in enumerate(tests):
        if "priority" not in t:
            t["priority"] = i + 1

    tests.sort(key=lambda t: (
        CATEGORY_PRIORITY.get(t.get("category", "stress"), 99),
        t.get("priority", 99)
    ))

    for i, t in enumerate(tests):
        t["priority"] = i + 1

    result["selected_tests"] = tests
    result["total_selected"]  = len(tests)

    return result


def save_output(result):
    out_json = os.path.join(AI_INPUTS, "selected_tests.json")
    out_list = os.path.join(AI_INPUTS, "selected_tests.txt")

    with open(out_json, "w") as f:
        json.dump(result, f, indent=2)

    with open(out_list, "w") as f:
        for t in result["selected_tests"]:
            f.write(t["test_id"] + "\n")

    print(f"\n✓ Results saved to {out_json}")
    print(f"✓ Test list saved to {out_list}")


def main():
    print("=" * 60)
    print("AI TEST SELECTOR — Phase 2 Pipeline")
    print("=" * 60)

    user_prompt = build_user_prompt()

    print(f"\n[Input sizes]")
    print(f"  User prompt : {len(user_prompt)} chars (~{len(user_prompt)//4} tokens)")

    raw    = call_llm(user_prompt)
    result = parse_and_validate(raw)

    print(f"\n=== LLM SELECTION RESULT ===")
    print(f"Changed elements : {result.get('changed_elements', '?')}")
    print(f"Reasoning        : {result.get('reasoning_summary', '?')}")
    print(f"Total selected   : {result['total_selected']} tests\n")

    print(f"{'#':<4} {'TEST_ID':<55} {'CATEGORY':<15} REASON")
    print("-" * 100)
    for t in result["selected_tests"]:
        print(f"{t['priority']:<4} {t['test_id']:<55} {t['category']:<15} {t.get('reason', '')}")

    save_output(result)

    test_ids = [t["test_id"] for t in result["selected_tests"]]
    print("\n=== PYTEST COMMAND ===")
    print("pytest " + " ".join(f"tests/*/{tid}.py" for tid in test_ids))


if __name__ == "__main__":
    main()