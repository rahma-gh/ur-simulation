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

# ── LLM : Google AI Studio — API native (gratuit, 1M tokens contexte) ──
# Clé gratuite : https://aistudio.google.com/apikey
# Modèles gratuits : gemini-1.5-flash | gemini-1.5-flash-8b | gemini-1.0-pro
HF_MODEL = "gemini-flash-latest"
HF_URL   = "https://generativelanguage.googleapis.com/v1beta/models/" + HF_MODEL + ":generateContent"


MAX_DIFF_CHARS    = 8_000
MAX_HISTORY_CHARS = 12_000


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
        "git_diff":      read_input("git_diff.txt",     MAX_DIFF_CHARS),
        "tests_history": read_input("tests_history.txt", MAX_HISTORY_CHARS),
    }
    for k, v in data.items():
        print(f"        ✓ {k:16s}  ({len(v):,} chars)")
    return data


SYSTEM_PROMPT = textwrap.dedent("""\
    ## RÔLE
    Tu es un moteur de sélection de tests pour un système cyber-physique industriel.
    Le projet est "ur-simulation" : une simulation Webots de bras robotiques UR
    qui saisissent des canettes sur un tapis roulant.

    Ton seul rôle : analyser ce qui a changé dans le code source et décider
    quels tests doivent être lancés sur ce push — le moins possible, mais tous
    ceux qui sont réellement concernés par le changement.

    ## FICHIERS SOURCE DU PROJET
    Il y a exactement 2 fichiers source qui contrôlent le comportement :

      controllers/ure_can_grasper/ure_can_grasper.c
        Contient une machine à états C avec ces éléments indépendants :
          - speed            : vitesse du bras (double speed = X.X)
          - TIME_STEP        : intervalle simulation (#define TIME_STEP 32)
          - structure        : états (WAITING/GRASPING/ROTATING/RELEASING/ROTATING_BACK)
                               et positions joints {-1.88, -2.14, -2.38, -1.51}
          - distance_threshold : seuil capteur distance (THRESHOLD = 500)
          - wrist_threshold  : seuils poignet (-2.3, -0.1)
          - gripper_position : fermeture gripper (0.85)

      controllers/ure_supervisor/ure_supervisor.py
        Contient ces constantes indépendantes :
          - HAUTEUR_SAISIE    : hauteur détection saisie (0.80m)
          - DEPLACEMENT_DEPOT : distance détection dépôt (0.30m)

      Les tests lisent soit les constantes directement, soit le fichier
      simulation_results.json produit par le supervisor après simulation.

    ## CE QUE TU REÇOIS

    [GIT_DIFF]
      - Quels fichiers source ont changé (controllers/*.c ou controllers/*.py)
      - La constante exacte modifiée et sa nouvelle valeur
      - Le diff complet (lignes + et -)

    [TESTS_HISTORY]
      Tableau avec pour chaque test :
      - TEST_ID      : identifiant exact
      - CATÉGORIE    : functional | non_functional
      - SOUS-CAT     : communication | safety | performance | stress | boundary | realtime
      - FAIL / RUNS  : nombre d'échecs sur total de runs
      - SENSITIVE_TO : constante précise que ce test vérifie
                       Format → fichier::constante
                       Exemple → ure_can_grasper::speed
                       Valeur spéciale "ure_can_grasper::behavior | ure_supervisor::behavior"
                       → ce test lit le JSON de résultats et est affecté par
                         TOUT changement dans les 2 fichiers source
                       Valeur "—" → test purement algorithmique, jamais affecté
      - FAILED_WHEN  : fichier source modifié lors des échecs passés
                       "—" = n'a jamais échoué

    ## ÉTAPES DE SÉLECTION (suivre dans l'ordre strict)

    ÉTAPE 1 — Identifier l'élément changé depuis GIT_DIFF
      Lire "ÉLÉMENT CHANGÉ" dans le diff.
      Identifier le fichier source ET la constante modifiée.
      Exemple : "speed changé 1.0 → 0.0" → élément = ure_can_grasper::speed

    ÉTAPE 2 — Sélectionner les tests (règles par ordre de priorité)

      RÈGLE A — SENSITIVE_TO match (priorité absolue)
        Si SENSITIVE_TO contient l'élément changé identifié à l'étape 1
        → SÉLECTIONNER ce test, même si FAIL=0 et FAILED_WHEN=—
        Exemples de match :
          - élément = ure_can_grasper::speed
            match si SENSITIVE_TO contient "ure_can_grasper::speed"
          - élément = speed (dans ure_can_grasper.c)
            match si SENSITIVE_TO contient "ure_can_grasper::behavior" (comportement global)

      RÈGLE B — SENSITIVE_TO = behavior (filet comportemental)
        Si SENSITIVE_TO = "ure_can_grasper::behavior | ure_supervisor::behavior"
        ET le fichier source modifié est ure_can_grasper.c OU ure_supervisor.py
        → SÉLECTIONNER (ces tests vérifient le comportement global, affecté par tout changement)

      RÈGLE C — Filet de sécurité historique
        Si FAILED_WHEN contient le fichier source modifié
        ET le test n'est pas déjà sélectionné par A ou B
        → SÉLECTIONNER (rattrape les dépendances non détectées statiquement)

      RÈGLE D — Exclusion absolue
        Si SENSITIVE_TO = "—" ET FAILED_WHEN = "—"
        → IGNORER inconditionnellement
        Ces tests sont purement algorithmiques (calculs mathématiques, stress tests
        de valeurs constantes). Ils ne peuvent pas échouer à cause d'un changement
        de code source.

    ÉTAPE 3 — Prioriser les tests sélectionnés
      Groupe 1 (passer en premier) : SOUS-CAT = safety
      Groupe 2 : SOUS-CAT = communication | tests functional sans sous-catégorie
      Groupe 3 : SOUS-CAT = performance | boundary | realtime
      Groupe 4 (passer en dernier) : SOUS-CAT = stress

      Dans chaque groupe, trier par ratio FAIL/RUNS décroissant
      (le test qui a le plus échoué = priorité la plus haute dans son groupe).
      Attribuer des entiers uniques à partir de 1.

    ## VÉRIFICATION AVANT DE RÉPONDRE
      [ ] Chaque test avec SENSITIVE_TO matchant l'élément changé est sélectionné
      [ ] Chaque test avec SENSITIVE_TO = "—" ET FAILED_WHEN = "—" est ignoré
      [ ] Aucun test_id inventé — tous viennent exactement de TESTS_HISTORY
      [ ] Les priorités sont des entiers uniques à partir de 1
      [ ] skipped_count = total tests dans TESTS_HISTORY - nombre sélectionnés

    ## FORMAT DE SORTIE
    Retourne UNIQUEMENT un objet JSON valide.
    Pas de texte avant. Pas de texte après. Pas de balises markdown. JSON brut seulement.

    {
      "selected_tests": [
        {
          "test_id":     "<identifiant exact depuis TESTS_HISTORY>",
          "priority":    <entier, 1 = passer en premier>,
          "category":    "<functional | non_functional>",
          "subcategory": "<communication | safety | performance | stress | boundary | realtime>",
          "reason":      "<une phrase : quelle constante a changé + ce que ce test vérifie>"
        }
      ],
      "skipped_count":        <entier>,
      "diff_summary":         "<une phrase : fichier modifié + nature du changement>",
      "selection_rationale":  "<2 phrases : combien sélectionnés par règle A vs B vs C, et pourquoi>"
    }

    ## EXEMPLE
    GIT_DIFF montre : speed changé de 1.0 à 0.0 dans ure_can_grasper.c

    TESTS_HISTORY contient :
      test_vitesse_bras_securisee   SENSITIVE_TO: ure_can_grasper::speed          FAILED_WHEN: —
      test_arm_rotates              SENSITIVE_TO: ure_can_grasper::behavior | ... FAILED_WHEN: ure_can_grasper
      test_boundary_joint_zero      SENSITIVE_TO: —                               FAILED_WHEN: —
      test_timestep_conforme        SENSITIVE_TO: ure_can_grasper::TIME_STEP      FAILED_WHEN: —

    Sélection correcte :
      SÉLECTIONNER test_vitesse_bras_securisee → RÈGLE A (SENSITIVE_TO::speed match)
      SÉLECTIONNER test_arm_rotates            → RÈGLE B (behavior + fichier source modifié)
      IGNORER      test_boundary_joint_zero    → RÈGLE D (— et —)
      IGNORER      test_timestep_conforme      → RÈGLE A non applicable (TIME_STEP ≠ speed)

    ## CE QU'IL NE FAUT JAMAIS FAIRE
    - Inventer un test_id qui n'existe pas dans TESTS_HISTORY
    - Sélectionner TOUS les tests — être sélectif est correct et attendu
    - Sélectionner un test dont SENSITIVE_TO ne correspond pas à l'élément changé
      et dont FAILED_WHEN est "—"
    - Assigner le même numéro de priorité à deux tests différents
    - Ajouter du texte en dehors de l'objet JSON
""")


def build_user_prompt(inputs: dict) -> str:
    # Google AI Studio : 1 000 000 tokens de contexte — aucune troncature nécessaire
    history = inputs['tests_history']

    return textwrap.dedent(f"""\
        Voici les fichiers de contexte pour le push actuel.
        Analyse-les et produis le JSON de sélection de tests.

        ═══════════════════════════════════════════════════════════
        [GIT_DIFF]
        ═══════════════════════════════════════════════════════════
        {inputs['git_diff']}

        ═══════════════════════════════════════════════════════════
        [TESTS_HISTORY]
        ═══════════════════════════════════════════════════════════
        {history}

        ═══════════════════════════════════════════════════════════
        Retourne UNIQUEMENT l'objet JSON brut. Rien d'autre.
        ═══════════════════════════════════════════════════════════
    """)



def call_llm(system: str, user: str, verbose: bool) -> str:
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("\n  [!] Variable GEMINI_API_KEY non définie.")
        print("      Créez une clé gratuite sur https://aistudio.google.com/apikey")
        print("      Puis : export GEMINI_API_KEY=AIza...")
        sys.exit(1)

    print(f"  [2/4] Envoi au LLM : {HF_MODEL} ...")

    # API native Google AI Studio (generateContent)
    # La clé passe en query param, pas en header Authorization
    url = HF_URL + f"?key={api_key}"

    payload = json.dumps({
        "system_instruction": {
            "parts": [{"text": system}]
        },
        "contents": [
            {"role": "user", "parts": [{"text": user}]}
        ],
        "generationConfig": {
            "maxOutputTokens": 8192,
            "temperature":     0.01,
        }
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent":   "ur-simulation-ci/1.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        print(f"\n  [!] Erreur HTTP {e.code} : {err_body[:500]}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"\n  [!] Erreur réseau : {e.reason}")
        sys.exit(1)

    # Format réponse API native Google
    raw = body["candidates"][0]["content"]["parts"][0]["text"].strip()

    if verbose:
        print("\n  ── Réponse brute du LLM ──")
        print(raw[:3000])
        print("  ──────────────────────────\n")

    usage = body.get("usageMetadata", {})
    print(f"        ✓ tokens utilisés — prompt: {usage.get('promptTokenCount','?')}  "
          f"completion: {usage.get('candidatesTokenCount','?')}")
    return raw

def repair_truncated_json(partial: str) -> str:
    """Tente de fermer un JSON tronqué."""
    repaired     = partial.rstrip(',')
    open_braces  = repaired.count('{') - repaired.count('}')
    open_brackets = repaired.count('[') - repaired.count(']')
    if open_brackets > 0:
        repaired += ']' * open_brackets
    if open_braces > 0:
        repaired += '}' * open_braces
    return repaired


def parse_llm_response(raw: str) -> dict:
    print("  [3/4] Parsing de la réponse LLM ...")

    # Supprimer les blocs <thinking> (certains modèles)
    cleaned = re.sub(r"<thinking>[\s\S]*?</thinking>", "", raw).strip()

    # Nettoyer les balises markdown ```json ... ```
    if "```" in cleaned:
        m = re.search(r"```(?:json)?\s*([\s\S]+?)```", cleaned)
        if m:
            cleaned = m.group(1).strip()

    # Extraire le premier objet JSON
    m = re.search(r"\{[\s\S]+\}", cleaned)
    if m:
        cleaned = m.group(0)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"  [!] JSON invalide, tentative de réparation... ({e})")
        repaired = repair_truncated_json(cleaned)
        try:
            data = json.loads(repaired)
            print("      ✓ JSON réparé avec succès.")
        except json.JSONDecodeError as e2:
            print(f"\n  [!] JSON invalide même après réparation.")
            print(f"      Réponse (500 premiers chars) : {cleaned[:500]}")
            sys.exit(1)

    if "selected_tests" not in data:
        print("  [!] Clé 'selected_tests' absente dans la réponse du LLM.")
        sys.exit(1)

    data["selected_tests"].sort(key=lambda t: t.get("priority", 999))
    return data


def display_plan(data: dict) -> None:
    selected  = data["selected_tests"]
    skipped   = data.get("skipped_count", "?")
    diff_sum  = data.get("diff_summary", "")
    rationale = data.get("selection_rationale", "")

    print()
    print("  " + "=" * 70)
    print(f"  PLAN DE TEST GÉNÉRÉ PAR L'IA — {HF_MODEL} (Google AI Studio — gratuit)")
    print("  " + "=" * 70)
    if diff_sum:
        print(f"\n  Diff    : {diff_sum}")
    if rationale:
        print(f"  Analyse : {rationale}")
    print(f"\n  Tests sélectionnés : {len(selected)}   |   Ignorés : {skipped}\n")
    print(f"  {'PRIO':<5}  {'CATÉGORIE':<16}  {'SOUS-CAT':<14}  {'TEST_ID':<50}  RAISON")
    print("  " + "─" * 130)
    for t in selected:
        reason_short = t.get("reason", "")[:50]
        cat          = t.get("category", "")
        sub          = t.get("subcategory", "")
        print(f"  {t['priority']:<5}  {cat:<16}  {sub:<14}  {t['test_id']:<50}  {reason_short}")
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
        print(f"  [!] Tests introuvables sur disque (ignorés) : {not_found}")

    return args


def run_tests(pytest_args: list, dry_run: bool, verbose: bool) -> int:
    print("  [4/4] Lancement des tests sélectionnés ...")
    print()

    cmd = [sys.executable, "-m", "pytest"] + pytest_args + [
        "-v",
        "--tb=short",
        "--html=reports/ai_selected_report.html",
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
    print(f"  ✓ Sélection sauvegardée : ai_inputs/last_selection.json")


def main():
    parser = argparse.ArgumentParser(
        description="Sélection et priorisation intelligente des tests via LLM."
    )
    parser.add_argument("--dry-run",      action="store_true",
                        help="Affiche le plan sans lancer pytest.")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Affiche la réponse brute du LLM.")
    parser.add_argument("--skip-prepare", action="store_true",
                        help="Ne pas relancer prepare_inputs.py.")
    args = parser.parse_args()

    print()
    print("=" * 70)
    print("  AI TEST SELECTOR — ur-simulation")
    print(f"  Modèle : {HF_MODEL} (Google AI Studio — gratuit)")
    print("=" * 70)
    print()

    # 0. Régénérer les inputs
    if not args.skip_prepare:
        print("  [0/4] Régénération des inputs (prepare_inputs.py) ...")
        r = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "prepare_inputs.py")],
            cwd=PROJECT_ROOT,
        )
        if r.returncode != 0:
            print("  [!] prepare_inputs.py a échoué.")
            sys.exit(1)
        print()

    # 1. Charger les inputs
    inputs = load_all_inputs()
    print()

    # 2. Envoyer au LLM
    raw_response = call_llm(SYSTEM_PROMPT, build_user_prompt(inputs), args.verbose)
    print()

    # 3. Parser la réponse
    selection = parse_llm_response(raw_response)
    print()

    # 4. Afficher le plan
    display_plan(selection)

    # 5. Sauvegarder
    save_selection_log(selection)
    print()

    # 6. Construire les args pytest
    pytest_args = build_pytest_args(selection["selected_tests"])
    if not pytest_args:
        print("  Aucun test à lancer (tous ignorés ou introuvables).")
        return 0

    # 7. Lancer
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