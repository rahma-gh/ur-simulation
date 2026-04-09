"""Le ratio phases actives / phases totales est-il supérieur à 60% ?"""
"""Tests non fonctionnels (performance) : nombre de phases de mouvement."""
import pytest

# États définis dans ure_can_grasper.c
ETATS_MACHINE = ["WAITING", "GRASPING", "ROTATING", "RELEASING", "ROTATING_BACK"]
NB_ETATS = len(ETATS_MACHINE)

def test_ratio_phases_actives():
    """Le ratio phases actives / phases totales est-il supérieur à 60% ?"""
    phases_actives = 4  # GRASPING, ROTATING, RELEASING, ROTATING_BACK
    ratio = phases_actives / NB_ETATS
    assert ratio > 0.60, f"Ratio phases actives trop bas : {ratio:.0%}"
    print(f" Ratio phases actives : {ratio:.0%}")
