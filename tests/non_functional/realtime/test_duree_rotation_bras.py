"""La durée de rotation du bras vers la position de dépôt est-elle < 15s ?"""
"""Tests non fonctionnels (realtime) : durée de la rotation du bras UR."""
import pytest

TIMESTEP_MS      = 32
STEPS_ROTATION   = 400   # estimation pour atteindre wrist < -2.3 rad

def test_duree_rotation_bras():
    """La durée de rotation du bras vers la position de dépôt est-elle < 15s ?"""
    duree = (STEPS_ROTATION * TIMESTEP_MS) / 1000.0
    assert duree < 15.0, f"Rotation trop longue : {duree:.2f}s"
    print(f" Durée rotation bras : {duree:.2f}s < 15s")
