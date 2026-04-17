"""La simulation s'est-elle terminée avant le timeout de 300s ?"""
import pytest, os, json

RESULTS_PATH = os.path.abspath("reports/simulation_results.json")
TIMEOUT_LIMITE = 300.0  # secondes (seuil Docker CMD)

def test_simulation_sans_timeout():
    """La simulation s'est-elle terminée avant le timeout de 300s ?"""
    if not os.path.exists(RESULTS_PATH):
        pytest.skip("JSON absent")
    with open(RESULTS_PATH) as f:
        r = json.load(f)
    duree = r.get("duration", 0)
    assert duree < TIMEOUT_LIMITE, \
        f"Simulation trop longue : {duree:.1f}s ≥ {TIMEOUT_LIMITE}s"
    print(f" Simulation terminée en {duree:.1f}s < {TIMEOUT_LIMITE}s")
