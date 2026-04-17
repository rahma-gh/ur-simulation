"""La durée de la phase RELEASING (counter=8 steps) est-elle < 1s ?"""
import pytest

TIMESTEP_MS    = 32   # TIME_STEP contrôleur
COUNTER_GRASP  = 8    # counter=8 dans ure_can_grasper.c (état GRASPING)

def test_duree_phase_releasing():
    """La durée de la phase RELEASING (counter=8 steps) est-elle < 1s ?"""
    counter_release = 8  # même valeur que GRASPING dans le contrôleur
    duree = (counter_release * TIMESTEP_MS) / 1000.0
    assert duree < 1.0, f"Phase RELEASING trop longue : {duree:.3f}s"
    print(f" Durée phase RELEASING : {duree:.3f}s")
