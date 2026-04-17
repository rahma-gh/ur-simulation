"""La simulation s'est-elle terminée normalement (sequence_complete) ?"""
import pytest, os, json

RESULTS_PATH = os.path.abspath("reports/simulation_results.json")
TIMEOUT_LIMITE = 300.0  # secondes (seuil Docker CMD)

def test_simulation_termine_normalement():
    """La simulation s'est-elle terminée normalement (sequence_complete) ?"""
    if not os.path.exists(RESULTS_PATH):
        pytest.skip("JSON absent")
    with open(RESULTS_PATH) as f:
        r = json.load(f)
    assert r.get("sequence_complete", False), \
        "Simulation terminée par timeout, pas par fin normale de séquence"
    print(" Simulation terminée normalement (séquence complète)")
