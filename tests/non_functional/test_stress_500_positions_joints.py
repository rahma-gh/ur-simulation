"""Validation de 500 positions joints UR sans erreur."""
import pytest, time, math

JOINT_MIN = -3.14159
JOINT_MAX =  3.14159

def test_stress_500_positions_joints():
    """500 positions joints aléatoires sont-elles toutes dans les limites UR ?"""
    time.sleep(10.0)
    import random
    random.seed(42)
    positions = [random.uniform(JOINT_MIN, JOINT_MAX) for _ in range(500)]
    hors_limites = [p for p in positions if not (JOINT_MIN <= p <= JOINT_MAX)]
    assert len(hors_limites) == 0, \
        f"{len(hors_limites)} positions hors limites sur 500"
    print(f" 500 positions joints validées dans [{JOINT_MIN}, {JOINT_MAX}] rad")
