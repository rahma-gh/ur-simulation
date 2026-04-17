"""Toutes les canettes ont-elles été saisies ?"""
import pytest, os, json

RESULTS_PATH = os.path.abspath("reports/simulation_results.json")

def load():
    if not os.path.exists(RESULTS_PATH):
        pytest.skip("JSON absent")
    with open(RESULTS_PATH) as f:
        return json.load(f)

def test_all_cans_grasped():
    """Toutes les canettes de la scène ont-elles été saisies (grasp_events == total_cans) ?"""
    r = load()
    total  = r.get("total_cans", 0)
    grasps = r.get("grasp_events", 0)
    assert grasps == total, \
        f"Seulement {grasps}/{total} canettes saisies — séquence incomplète"
    print(f" {grasps}/{total} canettes saisies ✓")
