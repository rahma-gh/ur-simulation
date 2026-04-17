"""Test fonctionnel : le bras retourne-t-il en position d'attente après chaque dépôt ?"""
import pytest, os, json

RESULTS_PATH = os.path.abspath("reports/simulation_results.json")

def load():
    if not os.path.exists(RESULTS_PATH):
        pytest.skip("JSON absent")
    with open(RESULTS_PATH) as f:
        return json.load(f)

def test_arm_returns_to_waiting():
    """Le bras retourne-t-il en position WAITING pour chaque canette traitée ?"""
    r = load()
    total   = r.get("total_cans", 0)
    returns = r.get("return_events", 0)
    assert returns == total, \
        f"Seulement {returns}/{total} retours en position d'attente"
    print(f" {returns}/{total} retours en position WAITING ✓")
