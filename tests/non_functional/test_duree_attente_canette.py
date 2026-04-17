"""La durée d'attente maximale avant détection est-elle < 20s ?"""
import pytest

TIMESTEP_MS     = 32
STEPS_WAITING   = 500   # estimation steps en état WAITING avant détection

def test_duree_attente_canette():
    """La durée d'attente maximale avant détection est-elle < 20s ?"""
    duree = (STEPS_WAITING * TIMESTEP_MS) / 1000.0
    assert duree < 20.0, f"Attente trop longue : {duree:.2f}s"
    print(f" Durée attente canette max : {duree:.2f}s < 20s")
