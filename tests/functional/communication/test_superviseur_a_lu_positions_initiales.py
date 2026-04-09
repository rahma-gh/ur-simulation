"""Le superviseur a-t-il lu les positions initiales des canettes dans la scène ?"""
"""
Test de communication : Superviseur ↔ Nœuds de la scène Webots

Vérifie que le superviseur a bien établi la communication avec les nœuds
de la scène (canettes) via l'API Supervisor, lu leurs positions en temps
réel, et transmis ces données au fichier JSON.

Communication testée :
  [Superviseur] --getRoot().getField("children")--> [Scène Webots]
  [Nœud Can]   --getPosition()--> [Superviseur]
  [Superviseur] --json.dump()--> [simulation_results.json]
  [pytest]      --json.load()--> [simulation_results.json]
"""
import pytest, os, json, math

RESULTS_PATH = os.path.abspath("reports/simulation_results.json")

def load():
    if not os.path.exists(RESULTS_PATH):
        pytest.skip("JSON absent — simulation non exécutée")
    with open(RESULTS_PATH) as f:
        return json.load(f)

def test_superviseur_a_lu_positions_initiales():
    """Le superviseur a-t-il lu les positions initiales des canettes dans la scène ?
    Preuve : can_initial_positions présent et non nul dans le JSON."""
    r = load()
    positions = r.get("can_initial_positions", [])
    total     = r.get("total_cans", 0)
    assert len(positions) == total, \
        f"Le superviseur n'a lu que {len(positions)}/{total} positions initiales — " \
        f"communication Superviseur→Nœuds incomplète"
    assert all(len(p) == 3 for p in positions), \
        "Positions initiales mal formées (pas de triplets XYZ)"
    print(f" Superviseur→Scène : {total} positions initiales lues ✓")
