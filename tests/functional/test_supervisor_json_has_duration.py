"""Le JSON contient-il une durée de simulation valide ?"""
import os, json, pytest

RESULTS_PATH = os.path.abspath("reports/simulation_results.json")

def test_supervisor_json_has_duration():
    """Le JSON contient-il une durée de simulation valide ?"""
    if not os.path.exists(RESULTS_PATH):
        pytest.skip("JSON absent")
    with open(RESULTS_PATH) as f:
        data = json.load(f)
    assert "duration" in data
    assert isinstance(data["duration"], (int, float))
    assert data["duration"] >= 0.0
    print(f" Durée simulation : {data['duration']}s")
