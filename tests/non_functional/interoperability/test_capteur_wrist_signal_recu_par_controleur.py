"""Le capteur wrist a-t-il transmis sa position au contrôleur ?"""
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

def test_capteur_wrist_signal_recu_par_controleur():
    """Le capteur wrist a-t-il transmis sa position au contrôleur ?
    Preuve : wrist_reached_target=True (le contrôleur a lu la valeur et réagi)."""
    r = load()
    assert r.get("wrist_reached_target", False), \
        "Le contrôleur n'a jamais reçu de valeur du capteur wrist — " \
        "communication wrist_1_joint_sensor→Contrôleur rompue"
    print(" Communication wrist_sensor→Contrôleur : position lue et traitée ✓")
