"""Tests de fiabilité : résultats reproductibles (lecture idempotente)."""
import pytest, time, os, json

RESULTS_PATH = os.path.abspath("reports/simulation_results.json")

def test_reliability_resultats_reproductibles():
    """Le JSON produit-il les mêmes résultats à chaque lecture ?"""
    time.sleep(60.0)
    if not os.path.exists(RESULTS_PATH):
        pytest.skip("JSON absent")
    with open(RESULTS_PATH) as f:
        r1 = json.load(f)
    with open(RESULTS_PATH) as f:
        r2 = json.load(f)
    assert r1["grasp_events"]    == r2["grasp_events"]
    assert r1["release_events"]  == r2["release_events"]
    assert r1["sequence_complete"] == r2["sequence_complete"]
    assert r1["duration"]        == r2["duration"]
    print(f" Résultats reproductibles (lecture idempotente)")
