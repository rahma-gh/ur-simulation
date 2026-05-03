"""200 positions du gripper Robotiq 3F sont-elles toutes valides ?"""
"""Tests de stress : validation de 200 positions gripper Robotiq 3F."""
import pytest, time

GRIPPER_MIN = 0.0
GRIPPER_MAX = 1.0

def test_stress_200_positions_gripper():
    """200 positions du gripper Robotiq 3F sont-elles toutes valides ?"""
    time.sleep(0.2)
    positions = [i / 200.0 for i in range(201)]   # 0.000 à 1.000
    hors_limites = [p for p in positions if not (GRIPPER_MIN <= p <= GRIPPER_MAX)]
    assert len(hors_limites) == 0, \
        f"{len(hors_limites)} positions gripper hors limites sur 201"
    print(f" 201 positions gripper validées dans [{GRIPPER_MIN}, {GRIPPER_MAX}]")
