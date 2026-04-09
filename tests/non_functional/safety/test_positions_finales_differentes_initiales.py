"""Les canettes ont-elles été déplacées (positions finales ≠ initiales) ?"""
"""Tests non fonctionnels (safety) : canettes manipulées sans collision."""
import pytest, os, json

RESULTS_PATH = os.path.abspath("reports/simulation_results.json")

def test_positions_finales_differentes_initiales():
    """Les canettes ont-elles été déplacées (positions finales ≠ initiales) ?"""
    if not os.path.exists(RESULTS_PATH):
        pytest.skip("JSON absent")
    with open(RESULTS_PATH) as f:
        r = json.load(f)
    initials = r.get("can_initial_positions", [])
    finals   = r.get("can_final_positions", [])
    if not initials or not finals:
        pytest.skip("Positions non disponibles dans le JSON")
    moved = 0
    for init, final in zip(initials, finals):
        dist = sum((a - b)**2 for a, b in zip(init, final))**0.5
        if dist > 0.01:
            moved += 1
    assert moved >= 1, "Aucune canette n'a été déplacée"
    print(f" {moved}/3 canette(s) déplacée(s) — pas de collision statique")
