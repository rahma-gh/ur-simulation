"""Test fonctionnel : le poignet a-t-il atteint la position cible ?"""
import pytest, os, json

RESULTS_PATH = os.path.abspath("reports/simulation_results.json")

def load():
    if not os.path.exists(RESULTS_PATH):
        pytest.skip("JSON absent")
    with open(RESULTS_PATH) as f:
        return json.load(f)

def test_wrist_reaches_target():
    """Le poignet (wrist_1_joint) a-t-il atteint la position cible (-2.3 rad) ?"""
    r = load()
    assert r.get("wrist_reached_target", False), \
        "Le poignet n'a jamais atteint la position cible — bras bloqué à speed=0 ?"
    total    = r.get("total_cans", 0)
    releases = r.get("release_events", 0)
    assert releases == total, \
        f"Poignet atteint mais seulement {releases}/{total} dépôts effectués"
    print(f" Poignet a atteint la cible pour {releases}/{total} canettes ✓")
