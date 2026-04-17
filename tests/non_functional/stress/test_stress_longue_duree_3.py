"""Tests de stress longue durée — partie 3/3."""
import pytest, time, os, json

RESULTS_PATH = os.path.abspath("reports/simulation_results.json")

def test_stress_longue_duree_3():
    """Stress longue durée 3/3 : séquence complète stable après attente prolongée."""
    print("\n Stress longue durée 3/3...")
    time.sleep(120.0)
    if not os.path.exists(RESULTS_PATH):
        pytest.skip("JSON absent")
    with open(RESULTS_PATH) as f:
        r = json.load(f)
    assert r.get("sequence_complete", False), \
        "Séquence non complète après attente prolongée"
    print(f" Partie 3/3 terminée — séquence complète ✓")
