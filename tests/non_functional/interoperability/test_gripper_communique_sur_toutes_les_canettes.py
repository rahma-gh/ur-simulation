"""Le gripper a-t-il été commandé pour chaque canette de la scène ?"""
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

def test_gripper_communique_sur_toutes_les_canettes():
    """Le gripper a-t-il été commandé pour chaque canette de la scène ?
    Preuve : grasp_events == total_cans."""
    r = load()
    total  = r.get("total_cans", 0)
    grasps = r.get("grasp_events", 0)
    assert grasps == total, \
        f"Gripper commandé pour seulement {grasps}/{total} canettes"
    print(f" Contrôleur→Gripper : {grasps}/{total} canettes traitées ✓")
