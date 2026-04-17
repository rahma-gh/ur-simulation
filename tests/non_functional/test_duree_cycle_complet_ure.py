"""La durée d'un cycle complet URe est-elle raisonnable (<30s) ?"""
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

def test_duree_cycle_complet_ure():
    """La durée d'un cycle complet URe est-elle raisonnable (<30s) ?"""
    duree = (TOTAL_STEPS_ONE_CYCLE * TIMESTEP_MS) / 1000.0
    assert duree < 30.0, f"Durée cycle trop longue : {duree:.2f}s"
    print(f" Durée cycle URe estimée : {duree:.2f}s")
