"""Le superviseur a-t-il lu les positions finales des canettes après simulation ?"""
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

def test_superviseur_a_lu_positions_finales():
    """Le superviseur a-t-il lu les positions finales des canettes après simulation ?
    Preuve : can_final_positions présent avec des valeurs différentes des initiales."""
    r = load()
    initials = r.get("can_initial_positions", [])
    finals   = r.get("can_final_positions", [])
    total    = r.get("total_cans", 0)
    assert len(finals) == total, \
        f"Positions finales incomplètes : {len(finals)}/{total}"
    # Au moins une canette doit avoir bougé
    mouvements = 0
    for init, final in zip(initials, finals):
        d = math.sqrt(sum((a-b)**2 for a, b in zip(init, final)))
        if d > 0.01:
            mouvements += 1
    assert mouvements > 0, \
        "Aucune canette n'a bougé selon le superviseur — " \
        "la communication getPosition() n'a pas retourné des valeurs dynamiques"
    print(f" Superviseur→Scène : {mouvements}/{total} canettes en mouvement détectées ✓")
