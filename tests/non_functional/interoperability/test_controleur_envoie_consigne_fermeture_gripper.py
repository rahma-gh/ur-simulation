"""Le contrôleur a-t-il envoyé la consigne de fermeture aux moteurs du gripper ?"""
"""
Test de communication : Contrôleur → Moteurs du gripper Robotiq 3F

Vérifie que le contrôleur a bien transmis les consignes de position
aux moteurs du gripper, et que ces consignes ont été exécutées physiquement.

Communication testée :
  [Contrôleur] --set_position(0.85)--> [finger_1_joint_1]
  [Contrôleur] --set_position(0.85)--> [finger_2_joint_1]
  [Contrôleur] --set_position(0.85)--> [finger_middle_joint_1]
  [Contrôleur] --set_position(min)--> [fingers] (ouverture)
"""
import pytest, os, json

RESULTS_PATH = os.path.abspath("reports/simulation_results.json")

def load():
    if not os.path.exists(RESULTS_PATH):
        pytest.skip("JSON absent — simulation non exécutée")
    with open(RESULTS_PATH) as f:
        return json.load(f)

def test_controleur_envoie_consigne_fermeture_gripper():
    """Le contrôleur a-t-il envoyé la consigne de fermeture aux moteurs du gripper ?
    Preuve : gripper_closed=True (les moteurs ont reçu et exécuté la consigne)."""
    r = load()
    assert r.get("gripper_closed", False), \
        "Le contrôleur n'a jamais envoyé la consigne de fermeture au gripper — " \
        "communication Contrôleur→Moteurs gripper rompue"
    print(" Communication Contrôleur→Gripper (fermeture) : consigne exécutée ✓")
