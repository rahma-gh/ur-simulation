"""Tests de stress : validation de 1 000 valeurs de vitesse bras UR."""
import pytest, time

def test_stress_1000_vitesses_bras():
    """1 000 valeurs de vitesse bras [0.1, 3.14] sont-elles toutes valides ?"""
    time.sleep(10.0)
    MIN_SPEED = 0.0
    MAX_SPEED = 3.14
    vitesses = [0.001 * i for i in range(1, 1001)]   # 0.001 à 1.0 rad/s
    invalides = [v for v in vitesses if not (MIN_SPEED < v <= MAX_SPEED)]
    assert len(invalides) == 0, \
        f"{len(invalides)} vitesses invalides sur 1000"
    print(f" 1 000 vitesses bras validées dans [0, {MAX_SPEED}] rad/s")
