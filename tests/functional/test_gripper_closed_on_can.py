"""Le gripper s'est-il fermé sur toutes les canettes ?"""
import pytest, os, json

RESULTS_PATH = os.path.abspath("reports/simulation_results.json")

def load():
    if not os.path.exists(RESULTS_PATH):
        pytest.skip("JSON absent")
    with open(RESULTS_PATH) as f:
        return json.load(f)

def test_gripper_closed_on_can():
    """Le gripper s'est-il fermé sur toutes les canettes de la scène ?"""
    r = load()
    total  = r.get("total_cans", 0)
    grasps = r.get("grasp_events", 0)
    assert r.get("gripper_closed", False), \
        "Gripper n'a jamais fermé"
    assert grasps == total, \
        f"Gripper fermé sur seulement {grasps}/{total} canettes"
    print(f" Gripper fermé sur {grasps}/{total} canettes ✓")
