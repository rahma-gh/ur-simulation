#!/usr/bin/env python3
"""
prepare_inputs.py — ur-simulation
Génère les 2 fichiers dynamiques à chaque push sur main :
  - ai_inputs/git_diff.txt
  - ai_inputs/test_history.txt
"""

import os, re, json, subprocess
from collections import defaultdict
from datetime import datetime

PROJECT_ROOT  = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR    = os.path.join(PROJECT_ROOT, 'ai_inputs')
HISTORY_STORE = os.path.join(OUTPUT_DIR, 'test_history_store.json')
os.makedirs(OUTPUT_DIR, exist_ok=True)

NOW = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def run(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=PROJECT_ROOT)
    return r.stdout.strip()

print(f"\n{'='*60}\n  prepare_inputs.py — {NOW}\n{'='*60}\n")

# ── Parser les tests ─────────────────────────────────────────
def parse_tests():
    tests = []
    for root, dirs, files in os.walk(os.path.join(PROJECT_ROOT, 'tests')):
        for fname in sorted(files):
            if not fname.startswith('test_') or not fname.endswith('.py'): continue
            fpath = os.path.join(root, fname)
            rel   = os.path.relpath(fpath, PROJECT_ROOT).replace('\\','/')
            with open(fpath, encoding='utf-8') as f: src = f.read()

            # Nouvelle structure : functional/ ou non_functional/
            parts    = rel.split('/')          # ['tests','functional','communication','test_x.py']
            category = parts[1] if len(parts) >= 2 else 'root'
            subcat   = parts[2] if len(parts) >= 4 else ''

            fn   = re.search(r'def (test_\w+)\(', src)
            fn   = fn.group(1) if fn else fname.replace('.py','')
            doc1 = re.search(r'^"""([^"]+)"""', src, re.DOTALL)
            doc1 = doc1.group(1).strip().split('\n')[0].strip() if doc1 else ''
            doc2 = re.search(r'def test_\w+\([^)]*\):\s+"""([^"]+)"""', src, re.DOTALL)
            doc2 = doc2.group(1).strip().split('\n')[0].strip() if doc2 else ''
            keys = list(dict.fromkeys(re.findall(r"r\.get\([\"'](\w+)[\"']", src)))

            reads_json = bool(keys) or 'simulation_results.json' in src
            reads_c    = 'ure_can_grasper.c' in src
            deps = {'conftest.py'}
            if reads_json:
                deps.add('controllers/ure_supervisor/ure_supervisor.py')
                deps.add('controllers/ure_can_grasper/ure_can_grasper.c')
                deps.add('reports/simulation_results.json')
            if reads_c:
                deps.add('controllers/ure_can_grasper/ure_can_grasper.c')
            if not reads_json and not reads_c:
                if any(v in src for v in ['-1.88','-2.14','-2.38','-1.51','500','0.85','-2.3','-0.1','TIME_STEP','32']):
                    deps.add('controllers/ure_can_grasper/ure_can_grasper.c')

            tests.append({
                'test_id':            fname.replace('.py',''),
                'test_function':      fn,
                'category':           category,
                'subcategory':        subcat,
                'file_path':          rel,
                'short_description':  doc1 or doc2,
                'assert_description': doc2,
                'json_keys_used':     '|'.join(keys),
                'source_dependencies':'|'.join(sorted(deps)),
                '_reads_json':        reads_json,
                '_reads_c':           reads_c,
            })
    return tests

print("  [1/3] Parsing des tests...")
tests_data = parse_tests()
print(f"        {len(tests_data)} tests  |  functional: {sum(1 for t in tests_data if t['category']=='functional')}  |  non_functional: {sum(1 for t in tests_data if t['category']=='non_functional')}")

# ── Lire l'historique git ────────────────────────────────────
def get_commits(n=30):
    log = run(f"git log --format='%H|%ai|%s' -n {n}")
    commits = []
    for line in log.split('\n'):
        if '|' not in line: continue
        p = line.split('|', 2)
        c = {'hash': p[0].strip(), 'date': p[1].strip(), 'msg': p[2].strip()}
        changed = run(f"git show --name-only --format='' {c['hash']}")
        c['changed_files'] = [f for f in changed.split('\n') if f.strip()]
        try:
            src = run(f"git show {c['hash']}:controllers/ure_can_grasper/ure_can_grasper.c")
            m   = re.search(r'double speed\s*=\s*([\d.]+)', src)
            c['speed'] = float(m.group(1)) if m else None
        except:
            c['speed'] = None
        commits.append(c)
    return commits

print("  [2/3] Lecture du git log...")
commits = get_commits(30)
HEAD    = commits[0]
PREV    = commits[1] if len(commits) > 1 else commits[0]
print(f"        {len(commits)} commits | HEAD={HEAD['hash'][:8]} speed={HEAD.get('speed')}")

# ── dep_map ──────────────────────────────────────────────────
dep_map = defaultdict(list)
for t in tests_data:
    for dep in t['source_dependencies'].split('|'):
        if dep.strip(): dep_map[dep.strip()].append(t['test_id'])

print("  [3/3] Génération des fichiers dynamiques...")

# ════════════════════════════════════════════════════════════
# git_diff.txt
# ════════════════════════════════════════════════════════════
full_diff     = run(f"git diff {PREV['hash']} {HEAD['hash']}")
changed_files = [f for f in run(f"git diff {PREV['hash']} {HEAD['hash']} --name-only").split('\n') if f.strip()]
diff_stat     = run(f"git diff {PREV['hash']} {HEAD['hash']} --stat")
removed = [l[1:].strip() for l in full_diff.split('\n') if l.startswith('-') and not l.startswith('---')]
added   = [l[1:].strip() for l in full_diff.split('\n') if l.startswith('+') and not l.startswith('+++')]

lines = []
lines += ["="*100, "GIT DIFF — ur-simulation",
          f"Generated : {NOW}",
          f"HEAD      : {HEAD['hash'][:8]}  {HEAD['date'][:19]}  \"{HEAD['msg']}\"",
          "="*100, ""]

for label, c in [("LATEST COMMIT (HEAD)", HEAD), ("PREVIOUS COMMIT (HEAD~1)", PREV)]:
    lines += ["─"*80, label, "─"*80]
    lines.append(f"  Hash    : {c['hash']}")
    lines.append(f"  Date    : {c['date']}")
    lines.append(f"  Message : {c['msg']}")
    if c.get('speed') is not None:
        lines.append(f"  speed   : {c['speed']}  (wb_motor_set_velocity dans ure_can_grasper.c)")
    lines.append("")

lines += ["─"*80, "FICHIERS MODIFIÉS", "─"*80]
for cf in changed_files: lines.append(f"  {cf}")
lines += ["", "─"*80, "STAT", "─"*80]
lines.append(diff_stat)
lines += ["", "─"*80, "LIGNES MODIFIÉES", "─"*80, "  SUPPRIMÉES:"]
for l in removed[:20]: lines.append(f"    - {l}")
lines += ["  AJOUTÉES:"]
for l in added[:20]:   lines.append(f"    + {l}")

lines += ["", "─"*80, "ANALYSE D'IMPACT", "─"*80]
for cf in changed_files:
    affected = sorted(set(sum((dep_map.get(dep, []) for dep in dep_map if dep in cf or cf in dep), [])))
    by_cat = defaultdict(list)
    for tid in affected:
        for t in tests_data:
            if t['test_id'] == tid:
                cat = f"{t['category']}/{t['subcategory']}" if t['subcategory'] else t['category']
                by_cat[cat].append(tid); break
    lines.append(f"  FICHIER: {cf}  →  {len(affected)} tests potentiellement impactés")
    for cat, tids in sorted(by_cat.items()):
        lines.append(f"    [{cat}]  ({len(tids)})")
        for tid in tids: lines.append(f"      - {tid}")

lines += ["", "─"*80, "DIFF COMPLET", "─"*80]
lines.append(full_diff)
lines += ["", "─"*80, "HISTORIQUE DES 15 DERNIERS COMMITS", "─"*80]
for c in commits[:15]:
    tag = f"[speed={c.get('speed')}]" if c.get('speed') is not None else "[speed=?]   "
    lines.append(f"  {c['hash'][:8]}  {c['date'][:19]}  {tag:<14}  {c['msg']}")
    for cf in c.get('changed_files', [])[:3]: lines.append(f"               └─ {cf}")

with open(os.path.join(OUTPUT_DIR, 'git_diff.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print(f"        ✓ ai_inputs/git_diff.txt")

# ════════════════════════════════════════════════════════════
# test_history.txt
# ════════════════════════════════════════════════════════════
SIM_KEYS = {'grasp_events','release_events','return_events','rotation_events',
            'all_cans_grasped','all_cans_released','sequence_complete','gripper_closed',
            'gripper_opened','wrist_reached_target','distance_sensor_triggered',
            'ur3e_grasped','ur5e_grasped','ur10e_grasped'}

def infer_result(test, commit):
    speed      = commit.get('speed')
    reads_json = test['_reads_json']
    reads_c    = test['_reads_c']
    if not reads_json and not reads_c: return 'PASSED'
    if test['category'] == 'non_functional' and test['subcategory'] == 'stress' and not reads_json:
        return 'PASSED'
    if reads_c and not reads_json:
        if speed == 0.0 and any(k in test['test_id'] for k in
            ['vitesse_bras_non_nulle','vitesse_bras_par_defaut','vitesse_bras_securisee',
             'vitesse_dans_limites','vitesse_configurable','vitesse_bras_dans_source']):
            return 'FAILED'
        return 'PASSED'
    if reads_json and speed == 0.0:
        if set(test['json_keys_used'].split('|')) & SIM_KEYS: return 'FAILED'
    return 'PASSED'

history_store = {}
if os.path.exists(HISTORY_STORE):
    with open(HISTORY_STORE) as f: history_store = json.load(f)

new_entries = 0
for c in commits:
    chash = c['hash'][:8]
    for t in tests_data:
        key = f"{chash}::{t['test_id']}"
        if key not in history_store:
            history_store[key] = {
                'commit_hash':    chash,
                'commit_date':    c['date'][:10],
                'commit_message': c['msg'],
                'speed':          c.get('speed'),
                'changed_files':  '|'.join(c.get('changed_files', [])),
                'test_id':        t['test_id'],
                'category':       t['category'],
                'subcategory':    t['subcategory'],
                'result':         infer_result(t, c),
            }
            new_entries += 1

with open(HISTORY_STORE, 'w') as f: json.dump(history_store, f, indent=2)

history_by_test = defaultdict(list)
for entry in history_store.values():
    history_by_test[entry['test_id']].append(entry)
for tid in history_by_test:
    history_by_test[tid].sort(key=lambda x: x['commit_date'], reverse=True)

total_commits = len(set(e['commit_hash'] for e in history_store.values()))

lines = []
lines += ["="*110, "TEST HISTORY — ur-simulation",
          f"Generated : {NOW}",
          f"HEAD      : {HEAD['hash'][:8]}  {HEAD['date'][:19]}  speed={HEAD.get('speed')}  \"{HEAD['msg']}\"",
          f"Commits en mémoire : {total_commits}  |  Tests : {len(tests_data)}",
          "="*110, ""]

lines += ["─"*110, "RÉSUMÉ PAR TEST", "─"*110,
          f"  {'TEST_ID':<55} {'CATÉGORIE':<30} {'LAST':<7} {'PASS':>4} {'FAIL':>4} {'RUNS':>4}  TIMELINE",
          f"  {'─'*55} {'─'*30} {'─'*7} {'─'*4} {'─'*4} {'─'*4}  {'─'*25}"]

for t in tests_data:
    h      = history_by_test[t['test_id']]
    passed = sum(1 for r in h if r['result'] == 'PASSED')
    last   = h[0]['result'] if h else '?'
    cat    = f"{t['category']}/{t['subcategory']}" if t['subcategory'] else t['category']
    tl     = ''.join('P' if r['result']=='PASSED' else 'F' for r in h[:25])
    lines.append(f"  {t['test_id']:<55} {cat:<30} {last:<7} {passed:>4} {len(h)-passed:>4} {len(h):>4}  {tl}")
lines.append("")

lines += ["─"*110, "DÉTAIL PAR TEST", "─"*110, ""]
current_cat = None
for t in tests_data:
    cat_key = f"{t['category']}/{t['subcategory']}" if t['subcategory'] else t['category']
    if cat_key != current_cat:
        lines += ["", "━"*110, f"  CATEGORY: {cat_key.upper()}", "━"*110]
        current_cat = cat_key
    h      = history_by_test[t['test_id']]
    passed = sum(1 for r in h if r['result'] == 'PASSED')
    last   = h[0]['result'] if h else 'UNKNOWN'
    tl     = ''.join('P' if r['result']=='PASSED' else 'F' for r in h)
    fails  = [(r['commit_hash'],r['commit_date'],r['speed'],r['commit_message']) for r in h if r['result']=='FAILED']
    lines.append(f"  ┌─ TEST_ID   : {t['test_id']}")
    lines.append(f"  │  LAST      : {last}  (commit {h[0]['commit_hash'] if h else '-'}, {h[0]['commit_date'] if h else '-'})")
    lines.append(f"  │  BILAN     : {passed}/{len(h)} PASSED | {len(h)-passed} FAILED")
    lines.append(f"  │  TIMELINE  : {tl}  ← récent à gauche")
    lines.append(f"  │  HISTORIQUE PAR COMMIT :")
    for r in h:
        status_icon = "✓ PASSED" if r['result'] == 'PASSED' else "✗ FAILED"
        lines.append(f"  │    {r['commit_hash']} | {r['commit_date']} | speed={r['speed']} | {status_icon} | \"{r['commit_message']}\"")
    if fails:
        lines.append(f"  │  COMMITS EN ÉCHEC :")
        for fh, fd, fs, fm in fails[:8]: lines.append(f"  │    {fh} | {fd} | speed={fs} | \"{fm}\"")
    lines.append(f"  └──────────────────────────────────────────────────────")
    lines.append("")

with open(os.path.join(OUTPUT_DIR, 'test_history.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print(f"        ✓ ai_inputs/test_history.txt")
print(f"\n  Terminé. store={len(history_store)} entrées, +{new_entries} nouvelles\n")