"""Test fonctionnel : les relâches se produisent-elles après les saisies ?"""
import pytest, os, json

RESULTS_PATH = os.path.abspath("reports/simulation_results.json")

def load():
    if not os.path.exists(RESULTS_PATH):
        pytest.skip("JSON absent")
    with open(RESULTS_PATH) as f:
        return json.load(f)

def test_release_after_grasp():
    """Les relâches se produisent-elles après les saisies et en nombre égal ?"""
    r = load()
    total    = r.get("total_cans", 0)
    grasps   = r.get("grasp_events", 0)
    releases = r.get("release_events", 0)
    assert grasps == total, \
        f"Seulement {grasps}/{total} saisies"
    assert releases == total, \
        f"Seulement {releases}/{total} relâches"
    assert releases == grasps, \
        f"Incohérence : {grasps} saisies mais {releases} relâches"
    print(f" Séquence cohérente : {grasps} saisies = {releases} relâches ✓")
