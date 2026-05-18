#!/usr/bin/env python3

import os, re, json, subprocess
from collections import defaultdict
from datetime import datetime

PROJECT_ROOT  = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR    = os.path.join(PROJECT_ROOT, 'ai_inputs')
HISTORY_STORE = os.path.join(OUTPUT_DIR, 'test_history_store.json')
os.makedirs(OUTPUT_DIR, exist_ok=True)

NOW = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# ── Controller source paths ───────────────────────────────────
CONTROLLER_C  = os.path.join(PROJECT_ROOT, 'controllers', 'ure_can_grasper', 'ure_can_grasper.c')
CONTROLLER_PY = os.path.join(PROJECT_ROOT, 'controllers', 'ure_supervisor', 'ure_supervisor.py')

# ── Input size limits ─────────────────────────────────────────
# IMPORTANT — why these limits exist and when to change them:
#
#   These limits protect against silently overflowing the LLM's context window.
#   If the raw input exceeds the model's token budget, the model silently drops
#   the tail of the prompt — which is far worse than our explicit truncation here,
#   because then we don't even know what was lost.
#
#   Can you remove them entirely?
#   → NOT recommended. Even large-context models (32k tokens) can be overwhelmed
#     by an unbounded test history or a massive merge-commit diff. Always keep a
#     safety ceiling; just raise it when you upgrade the model.
#
#   Current values are tuned for qwen2.5-coder:14b (≈32k token context):
#     MAX_DIFF_CHARS    = 20 000   (raised from 8 000 — covers realistic diffs)
#     MAX_HISTORY_CHARS = 40 000   (raised from 12 000 — no test entry is dropped)
#
#   If you switch back to qwen3:4b (≈4k tokens), lower these back to 8 000 / 12 000.
#   If you switch to a 32B+ model, you can raise them further or remove the ceiling
#   for history (but keep one for diff to avoid sending huge merge commits).
#
#   For very large inputs, a better strategy than raising limits is to summarize
#   the history (e.g. keep only the last 5 runs per test) before sending to the LLM.

MAX_DIFF_CHARS    = 20_000   # raised from 8 000
MAX_HISTORY_CHARS = 40_000   # raised from 12 000


def run(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=PROJECT_ROOT)
    return r.stdout.strip()

print(f"\n{'='*60}\n  prepare_inputs.py — {NOW}\n{'='*60}\n")

# ══════════════════════════════════════════════════════════════
# SENSITIVITY DETECTION
# ══════════════════════════════════════════════════════════════
def detect_sensitivity(src):
    """
    Reads a test's source code and returns the list of source-code
    elements (constants / behaviors) this test is sensitive to.
    Returns ['—'] if the test is purely algorithmic.
    """
    sensitive = []

    # ── ure_can_grasper.c ───────────────────────────────────────
    if re.search(
        r'\bDEFAULT_SPEED\b'
        r'|\bspeed\b.*(?:rad|bras|vitesse|securis|limit|=\s*1\.0|=\s*0\.0|=\s*2\.0)'
        r'|(?:rad|bras|vitesse|securis).*\bspeed\b',
        src, re.IGNORECASE
    ):
        sensitive.append('ure_can_grasper::speed')

    if re.search(r'\bTIME_STEP\b|\bTIMESTEP\b', src):
        sensitive.append('ure_can_grasper::TIME_STEP')

    if re.search(
        r'-1\.88|-2\.14|-2\.38|-1\.51'
        r'|\btarget_positions\b'
        r'|\bETATS_MACHINE\b'
        r'|WAITING.*GRASPING|GRASPING.*ROTATING'
        r'|ure_can_grasper\.c',
        src
    ):
        sensitive.append('ure_can_grasper::structure')

    if re.search(
        r'\bTHRESHOLD\b.*\b500\b'
        r'|\b500\b.*\bTHRESHOLD\b'
        r'|\bTHRESHOLD\s*=\s*500'
        r'|\bSENSOR_THRESHOLD\b',
        src
    ):
        sensitive.append('ure_can_grasper::distance_threshold')

    if re.search(r'-2\.3\b|-0\.1\b|\bWRIST_THRESH\b', src):
        sensitive.append('ure_can_grasper::wrist_threshold')

    if re.search(r'\b0\.85\b|\bGRIPPER_GRASP_POSITION\b', src):
        sensitive.append('ure_can_grasper::gripper_position')

    # ── ure_supervisor.py ───────────────────────────────────────
    if re.search(r'\bHAUTEUR_SAISIE\b|\bHAUTEUR_MIN\b', src):
        sensitive.append('ure_supervisor::HAUTEUR_SAISIE')

    if re.search(
        r'\bDEPLACEMENT_DEPOT\b'
        r'|\bDEPLACEMENT_MIN\b'
        r'|\bDEPLACEMENT_MAX\b',
        src
    ):
        sensitive.append('ure_supervisor::DEPLACEMENT_DEPOT')

    if 'simulation_results.json' in src and not sensitive:
        sensitive.append('ure_can_grasper::behavior | ure_supervisor::behavior')

    return sensitive if sensitive else ['—']


# ── Parse tests ───────────────────────────────────────────────
def parse_tests():
    tests = []
    for root, dirs, files in os.walk(os.path.join(PROJECT_ROOT, 'tests')):
        for fname in sorted(files):
            if not fname.startswith('test_') or not fname.endswith('.py'):
                continue
            fpath = os.path.join(root, fname)
            rel   = os.path.relpath(fpath, PROJECT_ROOT).replace('\\', '/')
            with open(fpath, encoding='utf-8') as f:
                src = f.read()

            parts       = rel.split('/')
            category    = parts[1] if len(parts) >= 2 else 'root'
            subcategory = parts[2] if len(parts) >= 4 else ''
            sensitive   = detect_sensitivity(src)

            tests.append({
                'test_id':      fname.replace('.py', ''),
                'category':     category,
                'subcategory':  subcategory,
                'file_path':    rel,
                'sensitive_to': sensitive,
            })
    return tests


print("  [1/5] Parsing tests...")
tests_data = parse_tests()
n_func    = sum(1 for t in tests_data if t['category'] == 'functional')
n_nonfunc = sum(1 for t in tests_data if t['category'] == 'non_functional')
print(f"        {len(tests_data)} tests  |  functional: {n_func}  |  non_functional: {n_nonfunc}")


# ── Read git history ──────────────────────────────────────────
def extract_changed_element(diff_text):
    patterns = [
        (r'\+\s*double\s+(\w+)\s*=\s*([\d.]+)',  lambda m: (m.group(1), m.group(2))),
        (r'\+\s*#define\s+(\w+)\s+([\d.]+)',      lambda m: (m.group(1), m.group(2))),
        (r'\+\s*([A-Z_]{3,})\s*=\s*([\d.]+)',     lambda m: (m.group(1), m.group(2))),
        (r'\+\s*(target_positions)\s*\[\]',        lambda m: (m.group(1), 'modified')),
    ]
    for pattern, extractor in patterns:
        m = re.search(pattern, diff_text)
        if m:
            return extractor(m)
    return ('unknown', 'unknown')


def get_commits(n=10):
    log = run(f"git log --format='%H|%ai|%s' -n {n}")
    commits = []
    for line in log.split('\n'):
        if '|' not in line:
            continue
        p = line.split('|', 2)
        c = {
            'hash': p[0].strip(),
            'date': p[1].strip(),
            'msg':  p[2].strip()
        }
        changed = run(f"git show --name-only --format='' {c['hash']}")
        c['changed_files'] = [f for f in changed.split('\n') if f.strip()]
        diff = run(f"git show {c['hash']}")
        c['changed_element'], c['value_at_change'] = extract_changed_element(diff)
        commits.append(c)
    return commits


print("  [2/5] Reading git log...")
commits = get_commits(10)
HEAD = commits[0] if commits else {
    'hash': 'unknown', 'date': NOW, 'msg': 'unknown',
    'changed_files': [], 'changed_element': 'unknown', 'value_at_change': 'unknown'
}
PREV = commits[1] if len(commits) > 1 else HEAD
print(f"        {len(commits)} commits | HEAD={HEAD['hash'][:8]} "
      f"element={HEAD.get('changed_element')} value={HEAD.get('value_at_change')}")

print("  [3/5] Generating git_diff.txt (with full controller sources)...")

# ══════════════════════════════════════════════════════════════
# git_diff.txt — includes full controller source code so the AI
# can understand the exact semantic impact of every change.
# ══════════════════════════════════════════════════════════════
full_diff     = run(f"git diff {PREV['hash']} {HEAD['hash']}")
changed_files = [
    f for f in run(f"git diff {PREV['hash']} {HEAD['hash']} --name-only").split('\n')
    if f.strip()
]
source_files_changed = [
    f for f in changed_files
    if 'controllers/' in f and (f.endswith('.c') or f.endswith('.py'))
]

# Truncate diff explicitly (never silently)
diff_was_truncated = False
if len(full_diff) > MAX_DIFF_CHARS:
    print(f"  [WARNING] git diff truncated: {len(full_diff):,} → {MAX_DIFF_CHARS:,} chars")
    print(f"            Raise MAX_DIFF_CHARS if this diff contains important changes.")
    full_diff = (
        full_diff[:MAX_DIFF_CHARS]
        + f"\n\n... [TRUNCATED at {MAX_DIFF_CHARS} chars — raise MAX_DIFF_CHARS if needed]"
    )
    diff_was_truncated = True

# Read controller sources in full (no limit — they are small and critical)
def read_source(path):
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            return f.read()
    return f"(file not found: {path})"

controller_c_src  = read_source(CONTROLLER_C)
controller_py_src = read_source(CONTROLLER_PY)

lines = []
lines += [
    "=" * 80,
    "GIT DIFF — ur-simulation",
    f"Generated : {NOW}",
    f"HEAD      : {HEAD['hash'][:8]}  {HEAD['date'][:19]}  \"{HEAD['msg']}\"",
    "=" * 80, ""
]

lines += ["─" * 80, "SOURCE FILES CHANGED (controllers/ only)", "─" * 80]
if source_files_changed:
    for f in source_files_changed:
        lines.append(f"  {f}")
else:
    lines.append("  (no controllers/ source file changed)")

lines += ["", "─" * 80, "CHANGED ELEMENT", "─" * 80]
lines.append(f"  Constant  : {HEAD.get('changed_element', 'unknown')}")
lines.append(f"  New value : {HEAD.get('value_at_change', 'unknown')}")

lines += ["", "─" * 80, "FULL DIFF", "─" * 80]
if diff_was_truncated:
    lines.append("  WARNING: diff was truncated — see MAX_DIFF_CHARS in prepare_inputs.py")
lines.append(full_diff)

# ── Inject full controller source code ────────────────────────
lines += [
    "",
    "=" * 80,
    "CONTROLLER SOURCE — controllers/ure_can_grasper/ure_can_grasper.c (FULL)",
    "Included so the AI understands the exact semantic impact of any change.",
    "Key elements: speed, TIME_STEP, target_positions[], distance threshold (500),",
    "              wrist thresholds (-2.3 / -0.1), gripper position (0.85),",
    "              state machine: WAITING→GRASPING→ROTATING→RELEASING→ROTATING_BACK",
    "=" * 80,
    controller_c_src,
    "",
    "=" * 80,
    "CONTROLLER SOURCE — controllers/ure_supervisor/ure_supervisor.py (FULL)",
    "Included so the AI understands the exact semantic impact of any change.",
    "Key elements: HAUTEUR_SAISIE (0.80m), DEPLACEMENT_DEPOT (0.30m),",
    "              produces simulation_results.json read by integration/functional tests.",
    "=" * 80,
    controller_py_src,
]

out_diff = '\n'.join(lines)
with open(os.path.join(OUTPUT_DIR, 'git_diff.txt'), 'w', encoding='utf-8') as f:
    f.write(out_diff)
print(f"        ✓ ai_inputs/git_diff.txt  ({len(out_diff):,} chars, includes controller sources)")


# ══════════════════════════════════════════════════════════════
# Load history store (read-only)
# ══════════════════════════════════════════════════════════════
print("  [4/5] Loading history store...")
history_store = {}
if os.path.exists(HISTORY_STORE):
    with open(HISTORY_STORE) as f:
        history_store = json.load(f)
    print(f"        store loaded: {len(history_store)} entries")
else:
    print("        store absent — first push, no history available")

history_by_test = defaultdict(list)
for test_id, entry in history_store.items():
    if isinstance(entry, dict) and "history" in entry:
        for h in entry["history"]:
            history_by_test[test_id].append(h)
    else:
        history_by_test[entry.get('test_id', test_id)].append(entry)


# ══════════════════════════════════════════════════════════════
# tests_history.txt
# NEVER silently truncate test entries — warn loudly instead.
# ══════════════════════════════════════════════════════════════
print("  [5/5] Generating tests_history.txt...")

lines = []
lines += [
    "=" * 100,
    "TESTS HISTORY — ur-simulation",
    f"Generated  : {NOW}",
    f"HEAD       : {HEAD['hash'][:8]}  {HEAD['date'][:19]}  "
    f"element={HEAD.get('changed_element')}  value={HEAD.get('value_at_change')}  "
    f"\"{HEAD['msg']}\"",
    "",
    "COLUMNS:",
    "  TEST_ID      : exact test identifier",
    "  CATEGORY     : functional | non_functional",
    "  SUBCATEGORY  : communication | safety | performance | stress | boundary | realtime",
    "  FAIL / RUNS  : number of failures over total runs",
    "  SENSITIVE_TO : exact source-code constant this test verifies",
    "                 Format → file::constant",
    "                 '—' = purely algorithmic test, never affected by source code",
    "  FAILED_WHEN  : source file modified when this test failed in the past",
    "                 '—' = has never failed",
    "=" * 100, ""
]

col_id   = max((len(t['test_id']) for t in tests_data), default=20)
col_cat  = 14
col_sub  = 14
col_sens = 55

header = (
    f"  {'TEST_ID':<{col_id}}  {'CATEGORY':<{col_cat}}  {'SUBCATEGORY':<{col_sub}}  "
    f"{'FAIL':>4}  {'RUNS':>4}  {'SENSITIVE_TO':<{col_sens}}  FAILED_WHEN"
)
lines.append(header)
lines.append("  " + "─" * (len(header) - 2))

for t in tests_data:
    h     = history_by_test[t['test_id']]
    runs  = len(h)
    fails = sum(1 for r in h if r['result'] == 'FAILED')

    failed_when = []
    for r in h:
        if r['result'] == 'FAILED':
            cf = r.get('source_files_changed', r.get('changed_files', []))
            src_files = [
                f for f in cf
                if 'controllers/' in f and (f.endswith('.c') or f.endswith('.py'))
            ]
            failed_when += src_files
    failed_when = list(dict.fromkeys(
        f.split('/')[-1].replace('.py', '').replace('.c', '')
        for f in failed_when
    ))
    failed_when_str = ', '.join(failed_when[:3]) if failed_when else '—'

    sensitive_str = ' | '.join(t['sensitive_to'])
    subcat        = t.get('subcategory', '') or '—'

    lines.append(
        f"  {t['test_id']:<{col_id}}  {t['category']:<{col_cat}}  {subcat:<{col_sub}}  "
        f"{fails:>4}  {runs:>4}  {sensitive_str:<{col_sens}}  FAILED_WHEN:{failed_when_str}"
    )

lines.append("")
history_text = '\n'.join(lines)

# Warn if large — but write everything (never drop test entries silently)
if len(history_text) > MAX_HISTORY_CHARS:
    print(f"  [WARNING] tests_history.txt is large: {len(history_text):,} chars")
    print(f"            MAX_HISTORY_CHARS={MAX_HISTORY_CHARS:,}. Full file is written.")
    print(f"            Consider upgrading to qwen2.5-coder:14b (32k context) or")
    print(f"            raising MAX_HISTORY_CHARS if the LLM rejects the input.")

with open(os.path.join(OUTPUT_DIR, 'tests_history.txt'), 'w', encoding='utf-8') as f:
    f.write(history_text)
print(f"        ✓ ai_inputs/tests_history.txt  ({len(history_text):,} chars, {len(tests_data)} tests)")

print(f"\n  Done. store={len(history_store)} entries\n")
print("  Generated files:")
print("    - ai_inputs/git_diff.txt  (diff + full controller sources)")
print("    - ai_inputs/tests_history.txt  (all tests, no silent truncation)")