"""Le signal du capteur a-t-il bien déclenché la phase GRASPING ?"""
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

def test_capteur_distance_declenche_grasping():
    """Le signal du capteur a-t-il bien déclenché la phase GRASPING ?
    Preuve : grasp_events > 0 (le contrôleur a réagi au signal)."""
    r = load()
    assert r.get("grasp_events", 0) > 0, \
        "Le capteur a peut-être émis un signal mais le contrôleur n'a pas " \
        "déclenché GRASPING — communication incomplète"
    print(f" Capteur→Contrôleur→GRASPING : {r['grasp_events']} déclenchement(s) ✓")
