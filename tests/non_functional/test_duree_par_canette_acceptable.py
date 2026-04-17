"""La durée moyenne par canette est-elle < 100s ?"""
import pytest, os, json

RESULTS_PATH = os.path.abspath("reports/simulation_results.json")

def test_duree_par_canette_acceptable():
    """La durée moyenne par canette est-elle < 100s ?"""
    if not os.path.exists(RESULTS_PATH):
        pytest.skip("JSON absent")
    with open(RESULTS_PATH) as f:
        r = json.load(f)
    duree = r.get("duration", 0)
    grasp = r.get("grasp_events", 1)
    if grasp == 0:
        pytest.skip("Aucune saisie, calcul impossible")
    duree_par_can = duree / grasp
    assert duree_par_can < 100.0, \
        f"Durée par canette trop longue : {duree_par_can:.1f}s"
    print(f" Durée moyenne par canette : {duree_par_can:.1f}s")
