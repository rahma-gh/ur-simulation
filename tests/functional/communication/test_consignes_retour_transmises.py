"""Le contrôleur a-t-il transmis les consignes de retour (0.0 rad) aux moteurs ?"""
"""
Test de communication : Contrôleur → Moteurs du bras UR

Vérifie que le contrôleur a bien transmis les consignes de position
aux 4 moteurs du bras UR (shoulder_lift, elbow, wrist_1, wrist_2),
et que ces consignes ont produit un mouvement physique observable.

Communication testée :
  [Contrôleur] --set_position([-1.88,-2.14,-2.38,-1.51])--> [Motors bras UR]
  [Contrôleur] --set_position([0.0, 0.0, 0.0, 0.0])--> [Motors bras UR] (retour)
  [Contrôleur] --set_velocity(1.0)--> [Motors bras UR]
"""
import pytest, os, json

RESULTS_PATH = os.path.abspath("reports/simulation_results.json")

def load():
    if not os.path.exists(RESULTS_PATH):
        pytest.skip("JSON absent — simulation non exécutée")
    with open(RESULTS_PATH) as f:
        return json.load(f)

def test_consignes_retour_transmises():
    """Le contrôleur a-t-il transmis les consignes de retour (0.0 rad) aux moteurs ?
    Preuve : return_events > 0 (les moteurs ont ramené le bras en position d'attente)."""
    r = load()
    assert r.get("return_events", 0) > 0, \
        "Aucun retour en position d'attente — les consignes de retour " \
        "(set_position 0.0) n'ont pas été transmises aux moteurs"
    print(f" Contrôleur→Moteurs bras (retour) : {r['return_events']} retour(s) exécuté(s) ✓")
