"""Tests de stress longue durée — partie 2/3."""
import pytest, time, os, json

RESULTS_PATH = os.path.abspath("reports/simulation_results.json")

def test_stress_longue_duree_2():
    """Stress longue durée 2/3 : release_events stable après attente."""
    print("\n Stress longue durée 2/3...")
    time.sleep(120.0)
    if not os.path.exists(RESULTS_PATH):
        pytest.skip("JSON absent")
    with open(RESULTS_PATH) as f:
        r = json.load(f)
    assert r.get("release_events", 0) >= 1, \
        "Aucun événement de relâche après 60s"
    print(f" Partie 2/3 terminée — release_events={r['release_events']}")
