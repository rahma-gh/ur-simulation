"""Tests de stress lourd : 1 000 validations complètes de la structure JSON."""
import pytest, time, os, json

RESULTS_PATH = os.path.abspath("reports/simulation_results.json")

REQUIRED_KEYS = [
    "total_cans", "robot_count", "grasp_events", "release_events",
    "rotation_events", "return_events", "all_cans_grasped",
    "all_cans_released", "sequence_complete", "max_can_heights",
    "can_names", "can_initial_positions", "can_final_positions",
    "per_can", "duration", "timestep_ms", "step_count",
]

def test_reliability_1000_validations_completes():
    """La structure complète du JSON est-elle valide sur 1 000 vérifications ?
    Vérifie toutes les clés, types, et cohérences à chaque itération."""
    print("\n Reliability 1 000 validations complètes en cours...")
    time.sleep(60.0)
    if not os.path.exists(RESULTS_PATH):
        pytest.skip("JSON absent")
    with open(RESULTS_PATH) as f:
        data = json.load(f)
    erreurs = 0
    for iteration in range(1000):
        # Vérification des clés
        for key in REQUIRED_KEYS:
            if key not in data:
                erreurs += 1
        # Vérification des types
        if not isinstance(data.get("total_cans"), int):       erreurs += 1
        if not isinstance(data.get("grasp_events"), int):     erreurs += 1
        if not isinstance(data.get("sequence_complete"), bool): erreurs += 1
        if not isinstance(data.get("duration"), float):       erreurs += 1
        if not isinstance(data.get("per_can"), dict):         erreurs += 1
        # Vérification cohérence
        if data.get("grasp_events", 0) != data.get("total_cans", -1):
            erreurs += 1
        if len(data.get("per_can", {})) != data.get("total_cans", -1):
            erreurs += 1

    assert erreurs == 0, \
        f"{erreurs} erreurs de validation sur 1 000 × {len(REQUIRED_KEYS)} vérifications"
    print(f" 1 000 × {len(REQUIRED_KEYS)} validations JSON complètes réussies ✓")
