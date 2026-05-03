"""La durée totale de simulation (JSON) est-elle dans les limites temps réel ?"""
"""Tests non fonctionnels (realtime) : durée du cycle total (3 canettes)."""
import pytest, os, json

RESULTS_PATH = os.path.abspath("reports/simulation_results.json")

def test_duree_cycle_total_simulation():
    """La durée totale de simulation (JSON) est-elle dans les limites temps réel ?"""
    if not os.path.exists(RESULTS_PATH):
        pytest.skip("JSON absent")
    with open(RESULTS_PATH) as f:
        r = json.load(f)
    duree = r.get("duration", 0)
    assert duree > 0.0, "Durée nulle dans le JSON"
    assert duree < 300.0, f"Durée totale trop longue : {duree:.1f}s"
    print(f" Durée totale simulation : {duree:.1f}s")
