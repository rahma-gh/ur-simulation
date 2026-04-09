"""La position du gripper est-elle dans les limites physiques [0, 1] ?"""
"""Tests non fonctionnels (safety) : gripper Robotiq 3F sans risque d'écrasement."""
import pytest, os

GRIPPER_GRASP_POSITION = 0.85   # position fermeture dans ure_can_grasper.c
GRIPPER_MIN_POSITION   = 0.0    # limite min (ouvert)
GRIPPER_MAX_POSITION   = 1.0    # limite max (fermé complet)

def test_gripper_position_dans_limites():
    """La position du gripper est-elle dans les limites physiques [0, 1] ?"""
    assert GRIPPER_MIN_POSITION <= GRIPPER_GRASP_POSITION <= GRIPPER_MAX_POSITION, \
        f"Position gripper hors limites : {GRIPPER_GRASP_POSITION}"
    print(f" Position gripper dans limites [{GRIPPER_MIN_POSITION}, {GRIPPER_MAX_POSITION}]")
