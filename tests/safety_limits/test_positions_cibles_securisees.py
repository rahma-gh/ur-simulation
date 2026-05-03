"""Toutes les positions cibles sont-elles dans les limites physiques UR ?"""
"""Tests non fonctionnels (safety) : positions joints UR dans les limites sécurité."""
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

def test_positions_cibles_securisees():
    """Toutes les positions cibles sont-elles dans les limites physiques UR ?"""
    for joint, pos in TARGET_POSITIONS.items():
        assert UR_JOINT_MIN <= pos <= UR_JOINT_MAX, \
            f"Position hors limites pour {joint}: {pos} rad"
    print(f" Toutes les positions cibles sécurisées : {TARGET_POSITIONS}")
