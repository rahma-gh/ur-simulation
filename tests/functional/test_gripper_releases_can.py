"""Le gripper s'est-il ouvert pour relâcher les canettes ?"""
import pytest, os, json

RESULTS_PATH = os.path.abspath("reports/simulation_results.json")

def load():
    if not os.path.exists(RESULTS_PATH):
        pytest.skip("JSON absent")
    with open(RESULTS_PATH) as f:
        return json.load(f)

def test_gripper_releases_can():
    """Le gripper s'est-il ouvert pour relâcher toutes les canettes ?"""
    r = load()
    total    = r.get("total_cans", 0)
    releases = r.get("release_events", 0)
    assert r.get("gripper_opened", False), \
        "Gripper n'a jamais ouvert"
    assert releases == total, \
        f"Seulement {releases}/{total} canettes relâchées"
    print(f" Gripper ouvert — {releases}/{total} canettes relâchées ✓")
