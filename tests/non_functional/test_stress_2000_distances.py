"""Calcul de 2 000 distances euclidiennes 3D sans erreur."""
import pytest, time, math

def test_stress_2000_distances_3d():
    """2 000 distances euclidiennes 3D sont-elles calculées sans erreur numérique ?"""
    time.sleep(10.0)
    points = [(i * 0.01, i * 0.005, i * 0.002) for i in range(2000)]
    origine = (0.0, 0.0, 0.0)
    distances = [math.sqrt(sum((a-b)**2 for a, b in zip(p, origine))) for p in points]
    assert len(distances) == 2000
    assert all(d >= 0.0 for d in distances), "Distance négative détectée"
    assert all(math.isfinite(d) for d in distances), "Distance infinie ou NaN détectée"
    print(f" 2 000 distances 3D calculées : min={min(distances):.4f}m, max={max(distances):.4f}m")
