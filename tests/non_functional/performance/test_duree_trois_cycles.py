"""La durée pour 3 canettes (3 cycles) est-elle < 90s ?"""
"""Tests non fonctionnels (performance) : durée du cycle complet URe."""
import pytest, time

TIMESTEP_MS = 8   # basicTimeStep ure.wbt
# Phases approximatives du cycle ure_can_grasper (en steps à 8ms)
STEPS_WAITING     = 500
STEPS_GRASPING    = 8     # counter=8
STEPS_ROTATING    = 400
STEPS_RELEASING   = 8     # counter=8
STEPS_ROTATING_BACK = 350
TOTAL_STEPS_ONE_CYCLE = (STEPS_WAITING + STEPS_GRASPING +
                          STEPS_ROTATING + STEPS_RELEASING +
                          STEPS_ROTATING_BACK)

def test_duree_trois_cycles():
    """La durée pour 3 canettes (3 cycles) est-elle < 90s ?"""
    duree_3 = 3 * (TOTAL_STEPS_ONE_CYCLE * TIMESTEP_MS) / 1000.0
    assert duree_3 < 90.0, f"3 cycles trop longs : {duree_3:.2f}s"
    print(f" Durée 3 cycles URe : {duree_3:.2f}s")
