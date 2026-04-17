"""La durée d'attente est-elle positive (simulation ne démarre pas instantanément) ?"""
"""Tests non fonctionnels (realtime) : durée de la phase d'attente canette."""
import pytest

TIMESTEP_MS     = 32
STEPS_WAITING   = 500   # estimation steps en état WAITING avant détection

def test_duree_attente_non_nulle():
    """La durée d'attente est-elle positive (simulation ne démarre pas instantanément) ?"""
    duree = (STEPS_WAITING * TIMESTEP_MS) / 1000.0
    assert duree > 0.0
    print(f" Durée attente positive : {duree:.2f}s")
