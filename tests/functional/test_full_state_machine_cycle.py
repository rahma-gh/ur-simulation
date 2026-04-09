"""Test fonctionnel : le cycle complet de la machine d'états est-il réalisé ?"""
import pytest, os, json

RESULTS_PATH = os.path.abspath("reports/simulation_results.json")

def load():
    if not os.path.exists(RESULTS_PATH):
        pytest.skip("JSON absent")
    with open(RESULTS_PATH) as f:
        return json.load(f)

def test_full_state_machine_cycle():
    """Le cycle WAITING→GRASPING→ROTATING→RELEASING→ROTATING_BACK est-il complet pour toutes les canettes ?"""
    r = load()
    total     = r.get("total_cans", 0)
    grasps    = r.get("grasp_events", 0)
    rotations = r.get("rotation_events", 0)
    releases  = r.get("release_events", 0)
    returns   = r.get("return_events", 0)
    assert grasps    == total, f"GRASPING    : {grasps}/{total}"
    assert rotations == total, f"ROTATING    : {rotations}/{total}"
    assert releases  == total, f"RELEASING   : {releases}/{total}"
    assert returns   == total, f"ROTATING_BACK : {returns}/{total}"
    print(f" Cycle complet pour {total}/{total} canettes ✓")
