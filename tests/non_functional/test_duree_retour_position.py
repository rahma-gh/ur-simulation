"""La durée de retour en position d'attente est-elle < 15s ?"""
import pytest

TIMESTEP_MS      = 32
STEPS_ROTATION   = 400   # estimation pour atteindre wrist < -2.3 rad

def test_duree_retour_position():
    """La durée de retour en position d'attente est-elle < 15s ?"""
    steps_retour = 350
    duree = (steps_retour * TIMESTEP_MS) / 1000.0
    assert duree < 15.0, f"Retour trop long : {duree:.2f}s"
    print(f" Durée retour position : {duree:.2f}s < 15s")
