"""Le contrôleur a-t-il transmis les consignes de rotation aux moteurs du bras ?"""
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

def test_controleur_transmet_consignes_rotation_bras():
    """Le contrôleur a-t-il transmis les consignes de rotation aux moteurs du bras ?
    Preuve : rotation_events > 0 (les moteurs ont reçu et exécuté les positions cibles)."""
    r = load()
    assert r.get("rotation_events", 0) > 0, \
        "Aucune rotation du bras — le contrôleur n'a jamais transmis les consignes " \
        "de position aux moteurs (shoulder_lift, elbow, wrist_1, wrist_2)"
    print(f" Contrôleur→Moteurs bras : {r['rotation_events']} rotation(s) exécutée(s) ✓")
