#!/usr/bin/env python3


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

# ══════════════════════════════════════════════════════════════
# SENSITIVITY DETECTION
# Pour chaque fichier test, détecte à quelle constante précise
# du code source il est sensible — basé sur les mots-clés dans
# le code source du test.
# ══════════════════════════════════════════════════════════════
def detect_sensitivity(src):
    """
    Lit le code source d'un test et retourne la liste des éléments
    du code source que ce test vérifie.

    Logique : on cherche des mots-clés ou valeurs numériques qui
    correspondent aux constantes définies dans les fichiers source.

    Retourne une liste comme :
      ['ure_can_grasper::speed', 'ure_can_grasper::TIME_STEP']
    ou ['—'] si le test est purement algorithmique.
    """
    sensitive = []

    # ── ure_can_grasper.c ───────────────────────────────────────

    # speed : la vitesse du bras (double speed = X.X)
    if re.search(
        r'\bDEFAULT_SPEED\b'
        r'|\bspeed\b.*(?:rad|bras|vitesse|securis|limit|=\s*1\.0|=\s*0\.0|=\s*2\.0)'
        r'|(?:rad|bras|vitesse|securis).*\bspeed\b',
        src, re.IGNORECASE
    ):
        sensitive.append('ure_can_grasper::speed')

    # TIME_STEP : l'intervalle de simulation (#define TIME_STEP 32)
    if re.search(r'\bTIME_STEP\b|\bTIMESTEP\b', src):
        sensitive.append('ure_can_grasper::TIME_STEP')

    # structure : états de la machine ou positions joints ou référence au .c
    if re.search(
        r'-1\.88|-2\.14|-2\.38|-1\.51'
        r'|\btarget_positions\b'
        r'|\bETATS_MACHINE\b'
        r'|WAITING.*GRASPING|GRASPING.*ROTATING'
        r'|ure_can_grasper\.c',
        src
    ):
        sensitive.append('ure_can_grasper::structure')

    # distance_threshold : seuil du capteur de distance (500)
    if re.search(
        r'\bTHRESHOLD\b.*\b500\b'
        r'|\b500\b.*\bTHRESHOLD\b'
        r'|\bTHRESHOLD\s*=\s*500'
        r'|\bSENSOR_THRESHOLD\b',
        src
    ):
        sensitive.append('ure_can_grasper::distance_threshold')

    # wrist_threshold : seuils de position du poignet (-2.3, -0.1)
    if re.search(r'-2\.3\b|-0\.1\b|\bWRIST_THRESH\b', src):
        sensitive.append('ure_can_grasper::wrist_threshold')

    # gripper_position : position de fermeture du gripper (0.85)
    if re.search(r'\b0\.85\b|\bGRIPPER_GRASP_POSITION\b', src):
        sensitive.append('ure_can_grasper::gripper_position')

    # ── ure_supervisor.py ───────────────────────────────────────

    # HAUTEUR_SAISIE : hauteur de détection de saisie (0.80m)
    if re.search(r'\bHAUTEUR_SAISIE\b|\bHAUTEUR_MIN\b', src):
        sensitive.append('ure_supervisor::HAUTEUR_SAISIE')

    # DEPLACEMENT_DEPOT : distance de détection du dépôt (0.30m)
    if re.search(
        r'\bDEPLACEMENT_DEPOT\b'
        r'|\bDEPLACEMENT_MIN\b'
        r'|\bDEPLACEMENT_MAX\b',
        src
    ):
        sensitive.append('ure_supervisor::DEPLACEMENT_DEPOT')

    # behavior : lit simulation_results.json sans constante hardcodée
    # Ces tests vérifient le comportement global — affectés par tout changement source.
    if 'simulation_results.json' in src and not sensitive:
        sensitive.append('ure_can_grasper::behavior | ure_supervisor::behavior')

    return sensitive if sensitive else ['—']


# ── Parser les tests ──────────────────────────────────────────
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
            # Sous-catégorie : nom du dossier dans non_functional/
            # Nouvelle nomenclature ISO 25010 + IEC 61508 :
            #   interoperability    (était : communication)
            #   functional_safety   (était : safety)
            #   performance_efficiency (était : performance + realtime)
            #   reliability         (extrait de stress)
            #   stress, boundary    (inchangés)
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


print("  [1/4] Parsing des tests...")
tests_data = parse_tests()
n_func    = sum(1 for t in tests_data if t['category'] == 'functional')
n_nonfunc = sum(1 for t in tests_data if t['category'] == 'non_functional')
print(f"        {len(tests_data)} tests  |  functional: {n_func}  |  non_functional: {n_nonfunc}")


# ── Lire l'historique git ─────────────────────────────────────
def extract_changed_element(diff_text):
    """
    Extrait la constante modifiée et sa nouvelle valeur depuis un diff.
    Retourne (element, value) comme ('speed', '0.0').
    """
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


print("  [2/4] Lecture du git log...")
commits = get_commits(10)
HEAD = commits[0] if commits else {
    'hash': 'unknown', 'date': NOW, 'msg': 'unknown',
    'changed_files': [], 'changed_element': 'unknown', 'value_at_change': 'unknown'
}
PREV = commits[1] if len(commits) > 1 else HEAD
print(f"        {len(commits)} commits | HEAD={HEAD['hash'][:8]} "
      f"element={HEAD.get('changed_element')} value={HEAD.get('value_at_change')}")

print("  [3/4] Génération git_diff + tests_history...")

# ══════════════════════════════════════════════════════════════
# git_diff.txt
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

lines = []
lines += [
    "=" * 80,
    "GIT DIFF — ur-simulation",
    f"Generated : {NOW}",
    f"HEAD      : {HEAD['hash'][:8]}  {HEAD['date'][:19]}  \"{HEAD['msg']}\"",
    "=" * 80, ""
]

lines += ["─" * 80, "FICHIERS SOURCE MODIFIÉS (controllers/ uniquement)", "─" * 80]
if source_files_changed:
    for f in source_files_changed:
        lines.append(f"  {f}")
else:
    lines.append("  (aucun fichier source controllers/ modifié)")

lines += ["", "─" * 80, "ÉLÉMENT CHANGÉ", "─" * 80]
lines.append(f"  Constante     : {HEAD.get('changed_element', 'unknown')}")
lines.append(f"  Nouvelle valeur : {HEAD.get('value_at_change', 'unknown')}")

lines += ["", "─" * 80, "DIFF COMPLET", "─" * 80]
lines.append(full_diff)

with open(os.path.join(OUTPUT_DIR, 'git_diff.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print(f"        ✓ ai_inputs/git_diff.txt")

# ══════════════════════════════════════════════════════════════
# Lecture du store (en lecture seule)
# ══════════════════════════════════════════════════════════════
history_store = {}
if os.path.exists(HISTORY_STORE):
    with open(HISTORY_STORE) as f:
        history_store = json.load(f)
    print(f"        store chargé : {len(history_store)} entrées")
else:
    print("        store absent — premier push, aucun historique disponible")

history_by_test = defaultdict(list)
for test_id, entry in history_store.items():
    if isinstance(entry, dict) and "history" in entry:
        for h in entry["history"]:
            history_by_test[test_id].append(h)
    else:
        history_by_test[entry.get('test_id', test_id)].append(entry)

# ══════════════════════════════════════════════════════════════
# tests_history.txt
# ══════════════════════════════════════════════════════════════
lines = []
lines += [
    "=" * 100,
    "TESTS HISTORY — ur-simulation",
    f"Generated  : {NOW}",
    f"HEAD       : {HEAD['hash'][:8]}  {HEAD['date'][:19]}  "
    f"element={HEAD.get('changed_element')}  value={HEAD.get('value_at_change')}  "
    f"\"{HEAD['msg']}\"",
    "",
    "COLONNES :",
    "  TEST_ID      : identifiant exact du test",
    "  CATÉGORIE    : functional | non_functional",
    "  SOUS-CAT     : communication | safety | performance | stress | boundary | realtime",
    "  FAIL / RUNS  : nombre d'échecs sur nombre total de runs",
    "  SENSITIVE_TO : constante précise du code source que ce test vérifie",
    "                 Format → fichier::constante",
    "                 '—' = test purement algorithmique, jamais affecté par le code",
    "  FAILED_WHEN  : fichier source modifié lors des échecs passés de ce test",
    "                 '—' = n'a jamais échoué",
    "=" * 100, ""
]

col_id   = max((len(t['test_id']) for t in tests_data), default=20)
col_cat  = 14
col_sub  = 14
col_sens = 55

header = (
    f"  {'TEST_ID':<{col_id}}  {'CATÉGORIE':<{col_cat}}  {'SOUS-CAT':<{col_sub}}  "
    f"{'FAIL':>4}  {'RUNS':>4}  {'SENSITIVE_TO':<{col_sens}}  FAILED_WHEN"
)
lines.append(header)
lines.append("  " + "─" * (len(header) - 2))

for t in tests_data:
    h     = history_by_test[t['test_id']]
    runs  = len(h)
    fails = sum(1 for r in h if r['result'] == 'FAILED')

    # FAILED_WHEN : fichiers source présents lors des échecs
    # Support nouvelle structure (source_files_changed) et ancienne (changed_files)
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

with open(os.path.join(OUTPUT_DIR, 'tests_history.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print(f"        ✓ ai_inputs/tests_history.txt")

print(f"\n  Terminé. store={len(history_store)} entrées\n")
print("  Fichiers générés :")
print("    - ai_inputs/git_diff.txt")
print("    - ai_inputs/tests_history.txt")