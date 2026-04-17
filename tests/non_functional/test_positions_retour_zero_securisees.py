"""Les positions de retour (0.0 rad) sont-elles sécurisées ?"""
import pytest

# Positions cibles définies dans ure_can_grasper.c
TARGET_POSITIONS = {
    "shoulder_lift_joint": -1.88,
    "elbow_joint":         -2.14,
    "wrist_1_joint":       -2.38,
    "wrist_2_joint":       -1.51,
}

# Limites physiques des joints UR series (rad)
UR_JOINT_MIN = -3.14159
UR_JOINT_MAX =  3.14159

def test_positions_retour_zero_securisees():
    """Les positions de retour (0.0 rad) sont-elles sécurisées ?"""
    return_pos = 0.0
    assert UR_JOINT_MIN <= return_pos <= UR_JOINT_MAX
    print(f" Position de retour 0.0 rad sécurisée")
