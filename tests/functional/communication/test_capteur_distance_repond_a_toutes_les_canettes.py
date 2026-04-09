"""Le capteur a-t-il répondu à toutes les canettes qui sont passées devant lui ?"""
"""
Test de communication : Canette → Capteur de distance → Contrôleur

Vérifie que le capteur de distance a bien transmis un signal au contrôleur
et que le contrôleur a bien réagi en déclenchant la phase GRASPING.

Communication testée :
  [Canette physique] --distance < 500--> [DistanceSensor] --signal--> [Contrôleur]
"""
import pytest, os, json

RESULTS_PATH = os.path.abspath("reports/simulation_results.json")

def load():
    if not os.path.exists(RESULTS_PATH):
        pytest.skip("JSON absent — simulation non exécutée")
    with open(RESULTS_PATH) as f:
        return json.load(f)

def test_capteur_distance_repond_a_toutes_les_canettes():
    """Le capteur a-t-il répondu à toutes les canettes qui sont passées devant lui ?
    Preuve : grasp_events == total_cans (chaque canette a été détectée)."""
    r = load()
    total  = r.get("total_cans", 0)
    grasps = r.get("grasp_events", 0)
    assert grasps == total, \
        f"Seulement {grasps}/{total} canettes détectées par le capteur — " \
        f"certaines canettes n'ont pas déclenché de signal"
    print(f" Capteur distance a détecté {grasps}/{total} canettes ✓")
