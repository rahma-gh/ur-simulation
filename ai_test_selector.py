#!/usr/bin/env python3
"""
ai_test_selector.py — ur-simulation
────────────────────────────────────────────────────────────────────────────────
Framework intelligent de sélection et priorisation des tests via LLM (gratuit).

Workflow :
  1. Lit les 3 fichiers générés par prepare_inputs.py :
       ai_inputs/git_diff.txt
       ai_inputs/tests_history.txt
       ai_inputs/codebase_map.txt
  2. Construit un prompt structuré (prompt engineering) et l'envoie à Qwen 3.6
     via OpenRouter (clé API gratuite sur https://openrouter.ai)
  3. Parse la réponse JSON du LLM
  4. Lance uniquement les tests sélectionnés, dans l'ordre de priorité fourni

Usage :
  python ai_test_selector.py [--dry-run] [--verbose] [--skip-prepare]

Variables d'environnement :
  OPENROUTER_API_KEY   → clé API OpenRouter (gratuite sur https://openrouter.ai)

Modèle utilisé :
  qwen/qwen3.6-plus-preview:free  (via OpenRouter)
"""

import os
import sys
import json
import argparse
import subprocess
import textwrap
import urllib.request
import urllib.error
import re
from pathlib import Path

# ── Configuration ────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent.resolve()
AI_INPUTS    = PROJECT_ROOT / "ai_inputs"

# Modèle recommandé : Qwen 3.6 Plus Preview (gratuit, raisonnement intégré)
DEEPSEEK_MODEL = "qwen/qwen3.6-plus-preview:free"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Troncature des inputs (réduite pour laisser plus de place à la sortie JSON)
MAX_DIFF_CHARS    = 4_000
MAX_HISTORY_CHARS = 3_000
MAX_MAP_CHARS     = 2_000


# ── Lecture des fichiers d'entrée ─────────────────────────────────────────────

def read_input(filename: str, max_chars: int) -> str:
    path = AI_INPUTS / filename
    if not path.exists():
        print(f"  [!] Fichier manquant : {path}")
        print(f"      → Lancez d'abord : python prepare_inputs.py")
        sys.exit(1)
    content = path.read_text(encoding="utf-8")
    if len(content) > max_chars:
        content = content[:max_chars] + f"\n\n... [tronqué à {max_chars} caractères]"
    return content


def load_all_inputs() -> dict:
    print("  [1/4] Lecture des fichiers ai_inputs/ ...")
    data = {
        "git_diff":      read_input("git_diff.txt",      MAX_DIFF_CHARS),
        "tests_history": read_input("tests_history.txt",  MAX_HISTORY_CHARS),
        "codebase_map":  read_input("codebase_map.txt",   MAX_MAP_CHARS),
    }
    for k, v in data.items():
        print(f"        ✓ {k:16s}  ({len(v):,} chars)")
    return data


# ── Construction du prompt ────────────────────────────────────────────────────

SYSTEM_PROMPT = textwrap.dedent("""\
    ## ROLE
    You are a senior CI/CD test automation engineer with deep expertise in:
    - Regression risk analysis from code diffs
    - Test impact analysis based on source dependency graphs
    - Test prioritization strategies for embedded robotics pipelines
    - Python/pytest test suites and C controller code (Webots simulator)

    Your sole responsibility in this pipeline is to read three context files
    provided by the user, reason carefully about what changed in the codebase,
    and decide which tests must run and in which order.
    You are the intelligence layer of an automated CI/CD framework.
    Your output directly controls which pytest tests are executed on every git push.

    ## PROJECT CONTEXT
    The project is "ur-simulation": a Webots-based robotics simulation of Universal
    Robots arms (UR3e, UR5e, UR10e) that grasp and release cans on a conveyor belt.
    The codebase has two source files that tests depend on:
      - controllers/ure_can_grasper/ure_can_grasper.c   (C controller, state machine)
      - controllers/ure_supervisor/ure_supervisor.py     (Python supervisor)
    Tests read either the compiled C behaviour or a JSON report from the supervisor.
    There are two test categories:
      - functional      : verify that the simulation behaves correctly (grasping, states)
      - non_functional  : verify performance, timing, boundary values, real-time

    ## INPUT FILES YOU WILL RECEIVE
    The user message contains three sections:

    [GIT_DIFF]
      What changed between the last two commits.
      Contains: modified files, added/removed lines, impact analysis, commit history.

    [TESTS_HISTORY]
      For every test: its file path, JSON keys it reads, source dependencies,
      past PASSED/FAILED results per commit, last pass date, failure timeline.

    [CODEBASE_MAP]
      Source files broken down by function, with cross-file dependency links.

    ## YOUR REASONING PROCESS  (precise and strict)

    The TESTS_HISTORY table has a column "FAILED_WHEN" showing which source files
    were modified when each test previously failed.

    STEP 1 — Identify modified source files from GIT_DIFF.
      Extract only source files (controllers/*.c or controllers/*.py).
      Example: if ure_can_grasper.c changed → modified = ["ure_can_grasper"]

    STEP 2 — Apply MANDATORY selection rule.
      For EVERY test in TESTS_HISTORY:
        IF FAILED_WHEN contains ANY name matching a modified file → MUST select it.
        IF FAILED_WHEN is "—" → MUST skip it. No exception.
      This rule is absolute. Do not use judgment. Do not skip based on FAIL count.
      Even if FAIL=1/3, if FAILED_WHEN matches → select it.

    STEP 3 — Assign priorities.
      Sort selected tests by FAIL count descending (highest FAIL count = priority 1).
      Limit to at most 8 tests total (prioritize highest FAIL counts).

    STEP 4 — Handle new files (no history).
      If a modified file NEVER appears in any FAILED_WHEN entry anywhere in the table,
      it is a new file with no history. Select tests with RUNS=0 for that file.

    CRITICAL: The number of tests you select must equal the number of tests
    whose FAILED_WHEN column contains at least one modified file name.
    Do not add tests. Do not remove tests. Follow the rule exactly.

    The table also has a column SELECT_IF_DIFF_TOUCHES which is identical to
    FAILED_WHEN — use both to confirm your selection.
    If SELECT_IF_DIFF_TOUCHES contains "ure_can_grasper" and the diff touches
    ure_can_grasper.c → that test IS selected, no matter what its PASS history says.

    ## OUTPUT FORMAT  (strict — do not deviate)
    Output ONLY a valid JSON object. No markdown fences. No prose. No thinking block. Only raw JSON.
    Keep each "reason" under 80 characters (one short sentence).
    Limit selected_tests to at most 8 items.

    Schema:
    {
      "selected_tests": [
        {
          "test_id":  "<exact test_id string from TESTS_HISTORY>",
          "priority": <integer, 1 = run first>,
          "category": "<functional | non_functional>",
          "reason":   "<one precise sentence under 80 chars: what changed + why this test covers it>"
        }
      ],
      "skipped_count": <integer — number of tests NOT selected>,
      "diff_summary":  "<one sentence: what files changed and what the change is>",
      "selection_rationale": "<2-3 sentences explaining the overall selection strategy>"
    }

    Validation rules your JSON MUST satisfy:
      - "test_id" values must be copied exactly from TESTS_HISTORY — no invention
      - "priority" values must be unique integers starting from 1
      - "reason" must reference the specific changed code, not generic statements
      - "skipped_count" must equal (total tests in TESTS_HISTORY) minus (selected count)
      - Do NOT select a test if none of its declared dependencies were modified
        AND it has no FAILED history on similar commits
        AND the diff has no logical impact on what it validates

    ## FEW-SHOT EXAMPLE
    Suppose the diff shows that `double speed = 1.5` changed to `double speed = 2.0`
    in ure_can_grasper.c, and TESTS_HISTORY shows:

      test_vitesse_bras_non_nulle   DEPENDS ON: ure_can_grasper.c   ECHECS: 1 time at speed=0.0
      test_duree_cycle_complet_ure  DEPENDS ON: (no source file)    ECHECS: 0
      test_arm_rotates              DEPENDS ON: ure_supervisor.py   ECHECS: 0

    Correct selection:
      priority 1 → test_vitesse_bras_non_nulle  (depends on ure_can_grasper.c + has fail history)
      priority 2 → test_duree_cycle_complet_ure (speed change affects timing logic)
      skipped    → test_arm_rotates             (depends only on supervisor, not modified)

    ## WHAT YOU MUST NEVER DO
    - Never invent a test_id that does not exist in TESTS_HISTORY
    - Never select ALL tests — be selective; skipping irrelevant tests is correct
    - Never assign the same priority number to two different tests
    - Never output anything other than the raw JSON object
    - Never wrap the JSON in markdown code fences (no ```json)
    - Never add explanatory text after the closing brace of the JSON
""")


def build_user_prompt(inputs: dict) -> str:
    return textwrap.dedent(f"""\
        Here are the three context files for the current git push.
        Analyse them carefully and produce the test selection JSON as instructed.

        ═══════════════════════════════════════════════════════════════════════
        [GIT_DIFF]
        ═══════════════════════════════════════════════════════════════════════
        {inputs['git_diff']}

        ═══════════════════════════════════════════════════════════════════════
        [TESTS_HISTORY]
        ═══════════════════════════════════════════════════════════════════════
        {inputs['tests_history']}

        ═══════════════════════════════════════════════════════════════════════
        [CODEBASE_MAP]
        ═══════════════════════════════════════════════════════════════════════
        {inputs['codebase_map']}

        ═══════════════════════════════════════════════════════════════════════
        Output ONLY the raw JSON object. Nothing else.
        ═══════════════════════════════════════════════════════════════════════
    """)


# ── Appel au LLM (via OpenRouter) ────────────────────────────────────────────

def call_llm(system: str, user: str, verbose: bool) -> str:
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        print("\n  [!] Variable OPENROUTER_API_KEY non définie.")
        print("      Obtenez une clé gratuite sur https://openrouter.ai")
        print("      Puis : export OPENROUTER_API_KEY=sk-or-...")
        sys.exit(1)

    print(f"  [2/4] Envoi au LLM : {DEEPSEEK_MODEL} ...")

    payload = json.dumps({
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        "temperature": 0.0,
        "max_tokens": 16384,   # augmenté pour éviter la troncature
    }).encode("utf-8")

    req = urllib.request.Request(
        OPENROUTER_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type":  "application/json",
            "HTTP-Referer":  "https://github.com/ur-simulation",
            "X-Title":       "ur-simulation CI test selector",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        print(f"\n  [!] Erreur HTTP {e.code} : {err_body[:500]}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"\n  [!] Erreur réseau : {e.reason}")
        sys.exit(1)

    raw = body["choices"][0]["message"]["content"].strip()

    if verbose:
        print("\n  ── Réponse brute du LLM (thinking + JSON) ──")
        print(raw[:3000])
        print("  ────────────────────────────────────────────\n")

    usage = body.get("usage", {})
    print(f"        ✓ tokens utilisés — prompt: {usage.get('prompt_tokens','?')}  "
          f"completion: {usage.get('completion_tokens','?')}")
    return raw


# ── Réparation d'un JSON tronqué ─────────────────────────────────────────────

def repair_truncated_json(partial: str) -> str:
    """Tente de fermer un JSON tronqué (ajoute accolades et crochets manquants)."""
    # Enlever tout ce qui pourrait être après la dernière accolade complète
    # On va simplement équilibrer les accolades et crochets ouverts
    open_braces = partial.count('{') - partial.count('}')
    open_brackets = partial.count('[') - partial.count(']')
    # Ajouter les caractères fermants
    repaired = partial.rstrip(',')  # enlever une virgule finale éventuelle
    if open_braces > 0:
        repaired += '}' * open_braces
    if open_brackets > 0:
        repaired += ']' * open_brackets
    return repaired


# ── Parsing de la réponse JSON ────────────────────────────────────────────────

def parse_llm_response(raw: str) -> dict:
    print("  [3/4] Parsing de la réponse LLM ...")

    # Supprimer le bloc <thinking> (DeepSeek R1) – au cas où
    cleaned = re.sub(r"<thinking>[\s\S]*?</thinking>", "", raw).strip()

    # Nettoyer les éventuels blocs markdown ```json ... ```
    if "```" in cleaned:
        m = re.search(r"```(?:json)?\s*([\s\S]+?)```", cleaned)
        if m:
            cleaned = m.group(1).strip()

    # Extraire le premier objet JSON
    m = re.search(r"\{[\s\S]+\}", cleaned)
    if m:
        cleaned = m.group(0)

    # Tentative de parsing normal
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"  [!] JSON invalide, tentative de réparation... ({e})")
        repaired = repair_truncated_json(cleaned)
        try:
            data = json.loads(repaired)
            print("      ✓ JSON réparé avec succès (troncature détectée).")
        except json.JSONDecodeError as e2:
            print(f"\n  [!] Le LLM n'a pas retourné du JSON valide, même après réparation.")
            print(f"      Réponse nettoyée (500 premiers chars) : {cleaned[:500]}")
            sys.exit(1)

    if "selected_tests" not in data:
        print("  [!] Clé 'selected_tests' absente dans la réponse du LLM.")
        sys.exit(1)

    # Trier par priorité croissante
    data["selected_tests"].sort(key=lambda t: t.get("priority", 999))
    return data


# ── Affichage du plan de test ─────────────────────────────────────────────────

def display_plan(data: dict) -> None:
    selected  = data["selected_tests"]
    skipped   = data.get("skipped_count", "?")
    diff_sum  = data.get("diff_summary", "")
    rationale = data.get("selection_rationale", "")

    print()
    print("  ╔══════════════════════════════════════════════════════════════╗")
    print("  ║           PLAN DE TEST GÉNÉRÉ PAR L'IA (Qwen 3.6)           ║")
    print("  ╚══════════════════════════════════════════════════════════════╝")
    if diff_sum:
        print(f"\n  Diff    : {diff_sum}")
    if rationale:
        print(f"  Analyse : {rationale}")
    print(f"\n  Tests sélectionnés : {len(selected)}   |   Ignorés : {skipped}\n")
    print(f"  {'PRIO':<5}  {'CATÉGORIE':<16}  {'TEST_ID':<50}  RAISON")
    print("  " + "─" * 120)
    for t in selected:
        reason_short = t.get("reason", "")[:55]
        cat          = t.get("category", "")
        print(f"  {t['priority']:<5}  {cat:<16}  {t['test_id']:<50}  {reason_short}")
    print()


# ── Construction des arguments pytest ────────────────────────────────────────

def build_pytest_args(selected_tests: list) -> list:
    """Convertit les test_id en chemins de fichiers pytest valides."""
    test_dir = PROJECT_ROOT / "tests"
    args = []
    not_found = []

    for entry in selected_tests:
        tid = entry["test_id"]
        matches = list(test_dir.rglob(f"{tid}.py"))
        if matches:
            args.append(str(matches[0].relative_to(PROJECT_ROOT)))
        else:
            not_found.append(tid)

    if not_found:
        print(f"  [!] Tests introuvables sur disque (ignorés) : {not_found}")

    return args


# ── Lancement des tests ───────────────────────────────────────────────────────

def run_tests(pytest_args: list, dry_run: bool, verbose: bool) -> int:
    print("  [4/4] Lancement des tests sélectionnés ...")
    print()

    cmd = [sys.executable, "-m", "pytest"] + pytest_args + [
        "-v",
        "--tb=short",
        f"--html=reports/ai_selected_report.html",
        "--self-contained-html",
    ]
    if verbose:
        cmd.append("-s")

    print("  Commande :", " ".join(cmd))
    print()

    if dry_run:
        print("  [dry-run] Aucun test lancé (--dry-run actif).")
        return 0

    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    return result.returncode


# ── Sauvegarde du résultat de sélection (pour audit CI) ──────────────────────

def save_selection_log(data: dict) -> None:
    log_path = AI_INPUTS / "last_selection.json"
    log = {
        "model":              DEEPSEEK_MODEL,
        "selected":           data["selected_tests"],
        "skipped":            data.get("skipped_count"),
        "diff_summary":       data.get("diff_summary"),
        "selection_rationale": data.get("selection_rationale"),
    }
    log_path.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  ✓ Sélection sauvegardée : ai_inputs/last_selection.json")


# ── Point d'entrée ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Sélection et priorisation intelligente des tests via LLM (gratuit)."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Affiche le plan de test sans lancer pytest."
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Affiche la réponse brute du LLM et les sorties pytest détaillées."
    )
    parser.add_argument(
        "--skip-prepare", action="store_true",
        help="Ne pas relancer prepare_inputs.py avant la sélection."
    )
    args = parser.parse_args()

    print()
    print("=" * 70)
    print("  AI TEST SELECTOR — ur-simulation")
    print(f"  Modèle : {DEEPSEEK_MODEL}")
    print("=" * 70)
    print()

    # 0. Régénérer les inputs si nécessaire
    if not args.skip_prepare:
        print("  [0/4] Régénération des inputs (prepare_inputs.py) ...")
        r = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "prepare_inputs.py")],
            cwd=PROJECT_ROOT,
        )
        if r.returncode != 0:
            print("  [!] prepare_inputs.py a échoué — vérifiez votre dépôt git.")
            sys.exit(1)
        print()

    # 1. Charger les 3 fichiers
    inputs = load_all_inputs()
    print()

    # 2. Construire et envoyer le prompt au LLM
    raw_response = call_llm(SYSTEM_PROMPT, build_user_prompt(inputs), args.verbose)
    print()

    # 3. Parser la réponse
    selection = parse_llm_response(raw_response)
    print()

    # 4. Afficher le plan
    display_plan(selection)

    # 5. Sauvegarder le log de sélection
    save_selection_log(selection)
    print()

    # 6. Construire les args pytest
    pytest_args = build_pytest_args(selection["selected_tests"])
    if not pytest_args:
        print("  Aucun test à lancer (tous ignorés ou introuvables).")
        return 0

    # 7. Lancer les tests
    exit_code = run_tests(pytest_args, args.dry_run, args.verbose)

    print()
    if exit_code == 0:
        print("   Tous les tests sélectionnés ont passé.")
    else:
        print(f"   Certains tests ont échoué (exit code {exit_code}).")
    print()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
