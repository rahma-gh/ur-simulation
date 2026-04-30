"""Tests de fiabilité : 100 lectures du JSON de résultats sans erreur."""
import pytest, time, os, json

RESULTS_PATH = os.path.abspath("reports/simulation_results.json")

def test_reliability_100_lectures_json():
    """Le JSON peut-il être lu 100 fois consécutivement sans erreur ?"""
    time.sleep(15.0)
    if not os.path.exists(RESULTS_PATH):
        pytest.skip("JSON absent")
    erreurs = 0
    for _ in range(100):
        try:
            with open(RESULTS_PATH) as f:
                data = json.load(f)
            assert isinstance(data, dict)
        except Exception:
            erreurs += 1
    assert erreurs == 0, f"{erreurs}/100 lectures JSON en échec"
    print(f" 100/100 lectures JSON réussies")
