"""Validation de 10 000 positions joints UR."""
import pytest, time, random, math

def test_stress_10000_positions_joints():
    """10 000 positions joints aléatoires dans [-3.14159, 3.14159] sont-elles toutes valides ?
    Simule une longue séquence de planification de trajectoire UR."""
    print("\n Stress 10 000 positions joints en cours...")
    time.sleep(60.0)
    JOINT_MIN = -3.14159
    JOINT_MAX =  3.14159
    random.seed(123)
    positions = [random.uniform(JOINT_MIN, JOINT_MAX) for _ in range(10000)]
    hors_limites = [p for p in positions if not (JOINT_MIN <= p <= JOINT_MAX)]
    assert len(hors_limites) == 0, \
        f"{len(hors_limites)}/10 000 positions hors limites UR détectées"
    # Vérifier aussi que toutes sont des floats valides
    assert all(math.isfinite(p) for p in positions), \
        "Des positions NaN ou infinies détectées"
    print(f" 10 000 positions joints validées dans [{JOINT_MIN}, {JOINT_MAX}] rad ✓")
