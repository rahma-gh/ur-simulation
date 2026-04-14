#!/usr/bin/env python3
"""
prepare_inputs.py — ur-simulation
Génère les fichiers dynamiques à chaque push sur main :
  - ai_inputs/git_diff.txt
  - ai_inputs/tests_history.txt    (fusion de test_cases + test_history)
  - ai_inputs/codebase_map.txt     (version allégée : file_path, module, function, dependencies)
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

            # Deux catégories uniquement : functional ou non_functional
            parts    = rel.split('/')
            category = parts[1] if len(parts) >= 2 else 'root'
            # subcategory supprimée — on garde seulement functional / non_functional

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
                'file_path':          rel,
                'short_description':  doc1 or doc2,
                'assert_description': doc2,
                'json_keys_used':     '|'.join(keys),
                'source_dependencies':'|'.join(sorted(deps)),
                '_reads_json':        reads_json,
                '_reads_c':           reads_c,
            })
    return tests

print("  [1/4] Parsing des tests...")
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

print("  [2/4] Lecture du git log...")
commits = get_commits(30)
HEAD    = commits[0]
PREV    = commits[1] if len(commits) > 1 else commits[0]
print(f"        {len(commits)} commits | HEAD={HEAD['hash'][:8]} speed={HEAD.get('speed')}")

# ── dep_map ──────────────────────────────────────────────────
dep_map = defaultdict(list)
for t in tests_data:
    for dep in t['source_dependencies'].split('|'):
        if dep.strip(): dep_map[dep.strip()].append(t['test_id'])

print("  [3/4] Génération git_diff + tests_history...")

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

for label, c in [("DERNIER COMMIT (HEAD)", HEAD), ("AVANT-DERNIER COMMIT (HEAD~1)", PREV)]:
    lines += ["─"*80, label, "─"*80]
    lines.append(f"  Hash    : {c['hash']}")
    lines.append(f"  Date    : {c['date']}")
    lines.append(f"  Message : {c['msg']}")
    if c.get('speed') is not None:
        lines.append(f"  speed   : {c['speed']}  (wb_motor_set_velocity dans ure_can_grasper.c)")
    lines.append("")

lines += ["─"*80, "FICHIERS MODIFIÉS", "─"*80]
for cf in changed_files: lines.append(f"  {cf}")
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
                by_cat[t['category']].append(tid); break
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
# Historique — mise à jour du store
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
    if test['category'] == 'non_functional' and not reads_json:
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

# ════════════════════════════════════════════════════════════
# tests_history.txt  (fusion test_cases + test_history, sans doublon test_id)
# ════════════════════════════════════════════════════════════
n_func    = sum(1 for t in tests_data if t['category'] == 'functional')
n_nonfunc = sum(1 for t in tests_data if t['category'] == 'non_functional')

lines = []
lines += ["="*100,
          "TESTS HISTORY — ur-simulation",
          f"Generated  : {NOW}",
          f"HEAD       : {HEAD['hash'][:8]}  {HEAD['date'][:19]}  speed={HEAD.get('speed')}  \"{HEAD['msg']}\"",
          "="*100,
          ""]

# Détail par catégorie (functional puis non_functional)
lines += ["─"*100, "DÉTAIL PAR TEST", "─"*100, ""]
current_cat = None
for t in tests_data:
    if t['category'] != current_cat:
        lines += ["", "━"*100, f"  CATEGORY: {t['category'].upper()}", "━"*100]
        current_cat = t['category']

    h      = history_by_test[t['test_id']]
    fails  = [(r['commit_hash'],r['commit_date'],r['speed'],r['commit_message']) for r in h if r['result']=='FAILED']

    lines.append(f"  ┌─ TEST_ID     : {t['test_id']}")
    lines.append(f"  │  FILE        : {t['file_path']}")
    if t['short_description']:
        lines.append(f"  │  DESCRIPTION : {t['short_description']}")
    if t['json_keys_used']:
        lines.append(f"  │  JSON KEYS   : {t['json_keys_used']}")
    lines.append(f"  │  DEPENDS ON  : {t['source_dependencies']}")
    if fails:
        lines.append(f"  │  ECHECS      :")
        for fh, fd, fs, fm in fails[:8]: lines.append(f"  │    {fh} | {fd} | speed={fs} | \"{fm}\"")
    lines.append(f"  └──────────────────────────────────────────────────────")
    lines.append("")

with open(os.path.join(OUTPUT_DIR, 'tests_history.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print(f"        ✓ ai_inputs/tests_history.txt")

# ════════════════════════════════════════════════════════════
# codebase_map.txt  (allégé : file_path, module_name, function_name, dependencies)
# ════════════════════════════════════════════════════════════
print("  [4/4] Generation codebase_map...")

SOURCE_FILES = [
    ('controllers/ure_can_grasper/ure_can_grasper.c', 'ure_can_grasper', 'c'),
    ('controllers/ure_supervisor/ure_supervisor.py',  'ure_supervisor',  'python'),
    ('conftest.py',                                    'conftest',        'python'),
]

# Dépendances inter-fichiers : quelles fonctions interagissent avec d'autres fichiers
CROSS_FILE_DEPS = {
    'ure_can_grasper': {
        '<defines_enums>': [],
        'main':            ['controllers/ure_supervisor/ure_supervisor.py'],
    },
    'ure_supervisor': {
        '<module_constants>': [],
        'dist2d':             [],
        'discover_all_cans':  ['worlds/ure.wbt'],
        'write_results':      ['reports/simulation_results.json'],
        'run':                ['controllers/ure_can_grasper/ure_can_grasper.c',
                               'reports/simulation_results.json'],
    },
    'conftest': {
        'pytest_sessionstart':       ['reports/simulation_results.json'],
        'pytest_runtest_makereport': [],
        'pytest_sessionfinish':      ['reports/simulation_results.json'],
        '_generate_report':          ['reports/simulation_results.json',
                                      'controllers/ure_can_grasper/ure_can_grasper.c',
                                      'controllers/ure_supervisor/ure_supervisor.py'],
    },
}

def extract_functions_c(src):
    fns = []
    if re.search(r'#define|enum\s+\w+', src):
        fns.append('<defines_enums>')
    for m in re.finditer(r'^[\w\s\*]+\s+(\w+)\s*\([^)]*\)\s*\{', src, re.MULTILINE):
        name = m.group(1)
        if name not in ('if','for','while','switch'): fns.append(name)
    return list(dict.fromkeys(fns))

def extract_functions_py(src):
    fns = []
    if re.search(r'^[A-Z_]{3,}\s*=', src, re.MULTILINE):
        fns.append('<module_constants>')
    for m in re.finditer(r'^def (\w+)\(', src, re.MULTILINE):
        fns.append(m.group(1))
    return list(dict.fromkeys(fns))

file_to_tests = defaultdict(lambda: defaultdict(list))
for t in tests_data:
    for dep in t['source_dependencies'].split('|'):
        dep = dep.strip()
        if dep: file_to_tests[dep][t['category']].append(t['test_id'])

codebase_lines = []
codebase_lines += ["="*100,
                   "CODEBASE MAP — ur-simulation",
                   "Colonnes : file_path | module_name | function_name | dependencies",
                   "="*100, ""]

for src_rel, module_name, lang in SOURCE_FILES:
    src_abs = os.path.join(PROJECT_ROOT, src_rel)
    if not os.path.exists(src_abs):
        continue
    with open(src_abs, encoding='utf-8', errors='replace') as f:
        src_content = f.read()

    fns = extract_functions_c(src_content) if lang == 'c' else extract_functions_py(src_content)
    cross_deps = CROSS_FILE_DEPS.get(module_name, {})

    related_by_cat = file_to_tests.get(src_rel, {})
    total_related  = sum(len(v) for v in related_by_cat.values())

    codebase_lines += ["━"*100,
                       f"FILE PATH   : {src_rel}",
                       f"MODULE NAME : {module_name}",
                       "─"*100]

    for fn in fns:
        fn_deps = cross_deps.get(fn, [])
        codebase_lines.append(f"  FUNCTION NAME : {fn}")
        if fn_deps:
            codebase_lines.append(f"  DEPENDENCIES  : {' | '.join(fn_deps)}")
        else:
            codebase_lines.append(f"  DEPENDENCIES  : (aucune)")
        codebase_lines.append("")

    codebase_lines.append("")

with open(os.path.join(OUTPUT_DIR, 'codebase_map.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(codebase_lines))
print(f"        ✓ ai_inputs/codebase_map.txt")

print(f"\n  Termine. store={len(history_store)} entrees, +{new_entries} nouvelles\n")
print("  Fichiers generes :")
print("    - ai_inputs/git_diff.txt")
print("    - ai_inputs/tests_history.txt    (fusion test_cases + test_history)")
print("    - ai_inputs/codebase_map.txt     (file_path | module | function | dependencies)")