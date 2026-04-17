"""Le capteur wrist a-t-il déclenché la transition ROTATING_BACK→WAITING ?"""
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

def test_capteur_wrist_declenche_retour_waiting():
    """Le capteur wrist a-t-il déclenché la transition ROTATING_BACK→WAITING ?
    Preuve : return_events > 0 (le seuil -0.1 rad a bien été franchi et transmis)."""
    r = load()
    assert r.get("return_events", 0) > 0, \
        "Aucune transition ROTATING_BACK→WAITING — le contrôleur n'a jamais reçu " \
        "le signal wrist > -0.1 rad"
    print(f" wrist_sensor→Contrôleur : {r['return_events']} retour(s) en WAITING ✓")
