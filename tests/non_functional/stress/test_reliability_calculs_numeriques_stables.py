"""Tests de fiabilité : calculs numériques stables sur les positions UR."""
import pytest, time, math

def test_reliability_calculs_numeriques_stables():
    """Les calculs de norme de vecteurs 3D sont-ils stables sur 1000 itérations ?"""
    time.sleep(20.0)
    import random
    random.seed(0)
    erreurs = 0
    for _ in range(1000):
        v = [random.uniform(-3.14, 3.14) for _ in range(3)]
        norme = math.sqrt(sum(x**2 for x in v))
        if not math.isfinite(norme) or norme < 0:
            erreurs += 1
    assert erreurs == 0, f"{erreurs}/1000 calculs numériques instables"
    print(f" 1 000 normes 3D calculées sans instabilité numérique")
