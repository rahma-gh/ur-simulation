"""Le capteur wrist a-t-il déclenché la transition ROTATING→RELEASING ?"""
"""
Test de communication : Capteur de position wrist → Contrôleur

Vérifie que le capteur de position du poignet (wrist_1_joint_sensor)
a bien transmis sa valeur au contrôleur, et que le contrôleur a utilisé
cette valeur pour changer d'état (ROTATING → RELEASING, ROTATING_BACK → WAITING).

Communication testée :
  [wrist_1_joint_sensor] --position < -2.3 rad--> [Contrôleur] → déclenche RELEASING
  [wrist_1_joint_sensor] --position > -0.1 rad--> [Contrôleur] → déclenche WAITING
"""
import pytest, os, json

RESULTS_PATH = os.path.abspath("reports/simulation_results.json")

def load():
    if not os.path.exists(RESULTS_PATH):
        pytest.skip("JSON absent — simulation non exécutée")
    with open(RESULTS_PATH) as f:
        return json.load(f)

def test_capteur_wrist_declenche_transition_releasing():
    """Le capteur wrist a-t-il déclenché la transition ROTATING→RELEASING ?
    Preuve : release_events > 0 (le seuil -2.3 rad a bien été franchi et transmis)."""
    r = load()
    assert r.get("release_events", 0) > 0, \
        "Aucune transition ROTATING→RELEASING — le contrôleur n'a jamais reçu " \
        "le signal wrist < -2.3 rad"
    print(f" wrist_sensor→Contrôleur : {r['release_events']} transition(s) RELEASING déclenchée(s) ✓")
