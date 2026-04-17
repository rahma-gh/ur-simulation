"""Le capteur de distance a-t-il détecté une canette ?"""
import pytest, os, json

RESULTS_PATH = os.path.abspath("reports/simulation_results.json")

def load():
    if not os.path.exists(RESULTS_PATH):
        pytest.skip("JSON absent")
    with open(RESULTS_PATH) as f:
        return json.load(f)

def test_distance_sensor_triggered():
    """Le capteur de distance a-t-il détecté une canette ?"""
    r = load()
    assert r.get("distance_sensor_triggered", False), \
        "Capteur de distance jamais déclenché — aucune canette détectée"
    print(" Capteur de distance déclenché ✓")
