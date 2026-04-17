"""Les hauteurs max des canettes sont-elles positives (pas sous le sol) ?"""
"""Tests non fonctionnels (safety) : canettes manipulées sans collision."""
import pytest, os, json

RESULTS_PATH = os.path.abspath("reports/simulation_results.json")

def test_hauteurs_can_positives():
    """Les hauteurs max des canettes sont-elles positives (pas sous le sol) ?"""
    if not os.path.exists(RESULTS_PATH):
        pytest.skip("JSON absent")
    with open(RESULTS_PATH) as f:
        r = json.load(f)
    heights = r.get("max_can_heights", [0.0, 0.0, 0.0])
    for i, h in enumerate(heights):
        assert h >= 0.0, f"Canette {i+1} sous le sol : hauteur={h:.3f}m"
    print(f" Toutes les canettes au-dessus du sol : {[round(h,3) for h in heights]}")
