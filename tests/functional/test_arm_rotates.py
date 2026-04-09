"""Test fonctionnel : le bras a-t-il effectué toutes les rotations ?"""
import pytest, os, json

RESULTS_PATH = os.path.abspath("reports/simulation_results.json")

def load():
    if not os.path.exists(RESULTS_PATH):
        pytest.skip("JSON absent")
    with open(RESULTS_PATH) as f:
        return json.load(f)

def test_arm_rotates():
    """Le bras a-t-il effectué une rotation vers la position de dépôt pour chaque canette ?"""
    r = load()
    total    = r.get("total_cans", 0)
    rotations = r.get("rotation_events", 0)
    assert rotations == total, \
        f"Seulement {rotations}/{total} rotations effectuées — bras bloqué ?"
    print(f" {rotations}/{total} rotations effectuées ✓")
