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
# Historique — lecture du store réel (alimenté par le JOB 1)
# Le store contient les vrais résultats PASSED/FAILED issus
# des rapports pytest du pipeline classique (JOB 1).
# Ce script ne remplit JAMAIS le store — il le lit seulement.
# ════════════════════════════════════════════════════════════
history_store = {}
if os.path.exists(HISTORY_STORE):
    with open(HISTORY_STORE) as f:
        history_store = json.load(f)
    print(f"        store chargé : {len(history_store)} entrées réelles")
else:
    print("        store absent — premier push, aucun historique disponible")
    print("        Le LLM se basera uniquement sur le diff et la codebase map.")

new_entries = 0  # le store est en lecture seule dans ce script

# Nouvelle structure : le store est organisé par test_id avec un champ "history"
# On construit history_by_test en lisant directement cette structure
history_by_test = defaultdict(list)
for test_id, entry in history_store.items():
    if isinstance(entry, dict) and "history" in entry:
        # Nouvelle structure : {"test_id": ..., "history": [...]}
        for h in entry["history"]:
            history_by_test[test_id].append(h)
    else:
        # Ancienne structure (compatibilité) : entrée plate
        history_by_test[entry.get('test_id', test_id)].append(entry)

total_commits = len(set(
    h.get("commit_message", "")
    for entry in history_store.values()
    if isinstance(entry, dict) and "history" in entry
    for h in entry["history"]
))

# ════════════════════════════════════════════════════════════
# tests_history.txt  (fusion test_cases + test_history, sans doublon test_id)
# ════════════════════════════════════════════════════════════
n_func    = sum(1 for t in tests_data if t['category'] == 'functional')
n_nonfunc = sum(1 for t in tests_data if t['category'] == 'non_functional')

def clean_description(desc):
    """Supprime les préfixes de catégorie dans les descriptions (ex: 'Test fonctionnel : ')."""
    prefixes = [
        r'^Tests?\s+fonctionnel[s]?\s*(?:\([^)]+\))?\s*[:\-]\s*',
        r'^Tests?\s+non[\s_]fonctionnel[s]?\s*(?:\([^)]+\))?\s*[:\-]\s*',
    ]
    for pattern in prefixes:
        desc = re.sub(pattern, '', desc, flags=re.IGNORECASE).strip()
    # Capitalize first letter if lowercased after stripping
    if desc and desc[0].islower():
        desc = desc[0].upper() + desc[1:]
    return desc

lines = []
lines += ["="*100,
          "TESTS HISTORY — ur-simulation",
          f"Generated  : {NOW}",
          f"HEAD       : {HEAD['hash'][:8]}  {HEAD['date'][:19]}  speed={HEAD.get('speed')}  \"{HEAD['msg']}\"",
          "="*100,
          ""]

# ── Tableau RÉSUMÉ PAR TEST ──────────────────────────────────
lines += ["─"*100, "RÉSUMÉ PAR TEST", "─"*100, ""]

# Construire les stats par test
col_id    = max((len(t['test_id']) for t in tests_data), default=20)
col_cat   = max((len(t['category']) for t in tests_data), default=12)
col_last  = 10   # LAST PASS
col_fail  = 6    # FAIL
col_runs  = 6    # RUNS
col_tl    = 20   # TIMELINE

header = (f"  {'TEST_ID':<{col_id}}  {'CATÉGORIE':<{col_cat}}  "
          f"{'FAIL':>{col_fail}}  {'RUNS':>{col_runs}}  {'TIMELINE':<12}  FAILED_WHEN (fichiers modifiés lors des echecs)")
lines.append(header)
lines.append("  " + "─"*(len(header)-2))

for t in tests_data:
    h       = history_by_test[t['test_id']]
    runs    = len(h)
    fails   = sum(1 for r in h if r['result'] == 'FAILED')
    passes  = [r.get('commit_message', '—')[:30] for r in h if r['result'] == 'PASSED']
    last_pass = passes[0] if passes else '—'
    timeline_chars = ''.join('P' if r['result'] == 'PASSED' else 'F' for r in h[:20])

    # Extraire les fichiers modifiés lors des echecs — info cruciale pour le LLM
    failed_when = []
    for r in h:
        if r['result'] == 'FAILED':
            cf = r.get('changed_files', [])
            # Garder seulement les fichiers source (pas les .yml)
            src_files = [f for f in cf if not f.endswith('.yml') and not f.endswith('.disabled')]
            if src_files:
                failed_when += src_files
    # Dédupliquer et raccourcir
    failed_when = list(dict.fromkeys(
        f.split('/')[-1].replace('.py','').replace('.c','') for f in failed_when
    ))
    failed_when_str = ', '.join(failed_when[:3]) if failed_when else '—'

    lines.append(f"  {t['test_id']:<{col_id}}  {t['category']:<{col_cat}}  "
                 f"{fails:>{col_fail}}  {runs:>{col_runs}}  {timeline_chars:<12}  FAILED_WHEN: {failed_when_str}")

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
