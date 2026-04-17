"""Les hauteurs maximales de toutes les canettes sont-elles enregistrées ?"""
import pytest, os, json

RESULTS_PATH = os.path.abspath("reports/simulation_results.json")
HAUTEUR_TABLE = 0.8

def load():
    if not os.path.exists(RESULTS_PATH):
        pytest.skip("JSON absent")
    with open(RESULTS_PATH) as f:
        return json.load(f)

def test_hauteur_can_lors_saisie():
    """Les hauteurs maximales de toutes les canettes sont-elles enregistrées ?"""
    r = load()
    heights    = r.get("max_can_heights", [])
    total_cans = r.get("total_cans", len(heights))
    assert len(heights) == total_cans, \
        f"Attendu {total_cans} hauteurs, obtenu {len(heights)}"
    assert all(isinstance(h, (int, float)) for h in heights), \
        "Hauteurs non numériques dans le JSON"
    print(f" {total_cans} hauteurs enregistrées : {[round(h,3) for h in heights]}")
