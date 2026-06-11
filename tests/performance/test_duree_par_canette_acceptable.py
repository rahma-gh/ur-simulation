"""La durée moyenne par canette est-elle < 100s ?"""
"""Tests non fonctionnels (realtime) : durée du cycle total (3 canettes)."""
import pytest, os, json

RESULTS_PATH = os.path.abspath("reports/simulation_results.json")

def test_duree_par_canette_acceptable():
    """La durée moyenne par canette est-elle < 100s ?"""
    if not os.path.exists(RESULTS_PATH):
        pytest.skip("JSON absent")
    with open(RESULTS_PATH) as f:
        r = json.load(f)
    duree = r.get("duration", 0)
    grasp = r.get("grasp_events", 0)

    # CORRECTION : si aucune saisie n'a eu lieu alors que la simulation a tourné,
    # c'est une régression détectable — on échoue explicitement plutôt que de
    # sauter le test, ce qui masquerait la défaillance dans le rapport final.
    assert grasp > 0, \
        f"Aucune saisie effectuée (grasp_events=0) — " \
        f"durée par canette incalculable car le cycle n'a jamais démarré. " \
        f"Vérifier HAUTEUR_SAISIE, speed ou gripper_position."

    duree_par_can = duree / grasp
    assert duree_par_can < 100.0, \
        f"Durée par canette trop longue : {duree_par_can:.1f}s"
    print(f" Durée moyenne par canette : {duree_par_can:.1f}s")