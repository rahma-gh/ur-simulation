"""Le JSON contient-il toutes les clés obligatoires ?"""
import os, json, pytest

RESULTS_PATH = os.path.abspath("reports/simulation_results.json")

def test_json_has_required_keys():
    """Le JSON contient-il toutes les clés obligatoires ?"""
    if not os.path.exists(RESULTS_PATH):
        pytest.skip("JSON absent")
    with open(RESULTS_PATH) as f:
        data = json.load(f)
    required = [
        "grasp_events", "release_events", "sequence_complete",
        "duration", "all_cans_grasped", "all_cans_released"
    ]
    for key in required:
        assert key in data, f"Clé manquante dans le JSON : {key}"
    print(f" Toutes les clés obligatoires présentes")
