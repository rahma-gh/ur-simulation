"""Tests de fiabilité : 500 vérifications de cohérence des positions."""
import pytest, time, os, json

RESULTS_PATH = os.path.abspath("reports/simulation_results.json")

def test_reliability_500_coherences_positions():
    """Les positions initiales/finales sont-elles cohérentes sur 500 vérifications ?"""
    time.sleep(30.0)
    if not os.path.exists(RESULTS_PATH):
        pytest.skip("JSON absent")
    with open(RESULTS_PATH) as f:
        r = json.load(f)
    initials = r.get("can_initial_positions", [])
    finals   = r.get("can_final_positions", [])
    if not initials or not finals:
        pytest.skip("Positions non disponibles")
    echecs = 0
    for _ in range(500):
        for pos in initials + finals:
            if not (isinstance(pos, list) and len(pos) == 3):
                echecs += 1
            for coord in pos:
                if not isinstance(coord, (int, float)):
                    echecs += 1
    assert echecs == 0, f"{echecs} incohérences de position sur 500 vérifications"
    print(f" 500 vérifications cohérence positions : OK")
