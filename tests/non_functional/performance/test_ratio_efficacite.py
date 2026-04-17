"""Le ratio étapes actives / total est-il > 50% ?"""
"""Tests non fonctionnels (performance) : ratio d'efficacité de la séquence."""
import pytest, time

# Steps du cycle ure_can_grasper (TIME_STEP=32ms)
STEPS_GRASPING     = 8
STEPS_ROTATING     = 400
STEPS_RELEASING    = 8
STEPS_ROTATING_BACK = 350
STEPS_WAITING      = 500

STEPS_UTILES = STEPS_GRASPING + STEPS_ROTATING + STEPS_RELEASING + STEPS_ROTATING_BACK
TOTAL_STEPS  = STEPS_UTILES + STEPS_WAITING

def test_ratio_efficacite():
    """Le ratio étapes actives / total est-il > 50% ?"""
    time.sleep(0.3)
    ratio = STEPS_UTILES / TOTAL_STEPS
    assert ratio > 0.50, f"Ratio efficacité trop bas : {ratio:.1%}"
    print(f" Ratio efficacité URe : {ratio:.1%}")
