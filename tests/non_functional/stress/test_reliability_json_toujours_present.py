"""Le JSON est-il toujours présent après la simulation ?"""
"""Tests de fiabilité : JSON de résultats toujours présent après simulation."""
import pytest, time, os, json

RESULTS_PATH = os.path.abspath("reports/simulation_results.json")

def test_reliability_json_toujours_present():
    """Le JSON est-il toujours présent après la simulation ?"""
    time.sleep(2.0)
    assert os.path.exists(RESULTS_PATH), \
        "JSON absent — le superviseur n'a pas exporté les résultats"
    print(f" JSON présent : {RESULTS_PATH}")
