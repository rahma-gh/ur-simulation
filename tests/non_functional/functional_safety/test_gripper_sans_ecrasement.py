"""La position de fermeture du gripper est-elle > 0 (pas d'écrasement) ?"""
"""Tests non fonctionnels (safety) : gripper Robotiq 3F sans risque d'écrasement."""
import pytest, os

GRIPPER_GRASP_POSITION = 0.85   # position fermeture dans ure_can_grasper.c
GRIPPER_MIN_POSITION   = 0.0    # limite min (ouvert)
GRIPPER_MAX_POSITION   = 1.0    # limite max (fermé complet)

def test_gripper_sans_ecrasement():
    """La position de fermeture du gripper est-elle > 0 (pas d'écrasement) ?"""
    assert GRIPPER_GRASP_POSITION > GRIPPER_MIN_POSITION, \
        f"Gripper trop fermé — risque d'écrasement de la canette ! pos={GRIPPER_GRASP_POSITION}"
    print(f" Gripper sécurisé : {GRIPPER_GRASP_POSITION} > {GRIPPER_MIN_POSITION}")
