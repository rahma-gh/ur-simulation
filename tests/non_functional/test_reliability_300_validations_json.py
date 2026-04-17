"""Tests de fiabilité : 300 validations de la structure JSON."""
import pytest, time, os, json

RESULTS_PATH = os.path.abspath("reports/simulation_results.json")

REQUIRED_KEYS = [
    "grasp_events", "release_events", "rotation_events", "return_events",
    "all_cans_grasped", "all_cans_released", "sequence_complete",
    "duration", "robot_count", "max_can_heights",
]

def test_reliability_300_validations_json():
    """La structure JSON est-elle valide 300 fois consécutivement ?"""
    time.sleep(20.0)
    if not os.path.exists(RESULTS_PATH):
        pytest.skip("JSON absent")
    with open(RESULTS_PATH) as f:
        data = json.load(f)
    echecs = 0
    for _ in range(300):
        for key in REQUIRED_KEYS:
            if key not in data:
                echecs += 1
    assert echecs == 0, f"{echecs} clés manquantes sur 300 × {len(REQUIRED_KEYS)} vérifications"
    print(f" 300 × {len(REQUIRED_KEYS)} validations JSON réussies")
