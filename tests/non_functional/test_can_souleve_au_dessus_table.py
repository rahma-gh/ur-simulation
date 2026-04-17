"""Au moins une canette a-t-elle été soulevée au-dessus du seuil de saisie ?"""
import pytest, os, json

RESULTS_PATH = os.path.abspath("reports/simulation_results.json")
HAUTEUR_TABLE = 0.8

def load():
    if not os.path.exists(RESULTS_PATH):
        pytest.skip("JSON absent")
    with open(RESULTS_PATH) as f:
        return json.load(f)

def test_can_souleve_au_dessus_table():
    """Au moins une canette a-t-elle été soulevée au-dessus du seuil de saisie ?"""
    r = load()
    heights = r.get("max_can_heights", [0.0])
    max_h   = max(heights) if heights else 0.0
    assert max_h > HAUTEUR_TABLE, \
        f"Aucune canette soulevée au-dessus de {HAUTEUR_TABLE}m (max={max_h:.3f}m)"
    print(f" Hauteur max canette : {max_h:.3f}m > {HAUTEUR_TABLE}m ✓")
