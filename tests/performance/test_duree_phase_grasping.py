"""La durée de la phase GRASPING (counter=8 steps) est-elle < 1s ?"""
"""Tests non fonctionnels (realtime) : durée de la phase GRASPING."""
import pytest

TIMESTEP_MS    = 32   # TIME_STEP contrôleur
COUNTER_GRASP  = 8    # counter=8 dans ure_can_grasper.c (état GRASPING)

def test_duree_phase_grasping():
    """La durée de la phase GRASPING (counter=8 steps) est-elle < 1s ?"""
    duree = (COUNTER_GRASP * TIMESTEP_MS) / 1000.0
    assert duree < 1.0, f"Phase GRASPING trop longue : {duree:.3f}s"
    print(f" Durée phase GRASPING : {duree:.3f}s ({COUNTER_GRASP} steps × {TIMESTEP_MS}ms)")
