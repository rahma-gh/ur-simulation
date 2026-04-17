"""Le JSON de résultats est-il présent et lisible ?"""
import os, json, pytest

RESULTS_PATH = os.path.abspath("reports/simulation_results.json")

def test_json_readable_by_pytest():
    """Le JSON de résultats est-il présent et lisible ?"""
    if not os.path.exists(RESULTS_PATH):
        pytest.skip("JSON absent — simulation non exécutée")
    with open(RESULTS_PATH) as f:
        data = json.load(f)
    assert isinstance(data, dict), "Le JSON doit être un objet"
    assert len(data) > 0, "Le JSON est vide"
    print(f" JSON lisible, {len(data)} clés trouvées")
