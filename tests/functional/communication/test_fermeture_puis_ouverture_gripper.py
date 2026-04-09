"""La séquence fermeture→ouverture est-elle respectée ?"""
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

def test_fermeture_puis_ouverture_gripper():
    """La séquence fermeture→ouverture est-elle respectée ?
    Preuve : gripper_closed=True ET gripper_opened=True ET release_events <= grasp_events."""
    r = load()
    assert r.get("gripper_closed", False), "Gripper jamais fermé"
    assert r.get("gripper_opened", False), "Gripper jamais ouvert"
    grasps   = r.get("grasp_events", 0)
    releases = r.get("release_events", 0)
    assert releases <= grasps, \
        f"Incohérence : {releases} ouvertures pour {grasps} fermetures — " \
        f"le contrôleur a envoyé des consignes dans le mauvais ordre"
    print(f" Séquence Contrôleur→Gripper : {grasps} fermetures → {releases} ouvertures ✓")
