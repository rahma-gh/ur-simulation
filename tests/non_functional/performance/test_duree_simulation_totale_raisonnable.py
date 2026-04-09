"""La durée de simulation totale (3 cycles) est-elle raisonnable ?"""
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

def test_duree_simulation_totale_raisonnable():
    """La durée de simulation totale (3 cycles) est-elle raisonnable ?"""
    duree_cycle  = (TOTAL_STEPS * 32) / 1000.0  # en secondes (TIME_STEP=32ms)
    duree_totale = 3 * duree_cycle
    assert duree_totale < 150.0, \
        f"3 cycles trop longs : {duree_totale:.1f}s"
    print(f" Durée totale 3 cycles : {duree_totale:.1f}s < 150s")
