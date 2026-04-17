"""3 000 calculs trigonométriques pour cinématique UR."""
import pytest, time, math

def test_stress_3000_calculs_trigo():
    """3 000 calculs sin/cos pour cinématique inversée UR sont-ils stables ?"""
    time.sleep(10.0)
    resultats = []
    for i in range(3000):
        angle = (i / 3000.0) * 2 * math.pi - math.pi
        s = math.sin(angle)
        c = math.cos(angle)
        norme = s**2 + c**2
        resultats.append(norme)
    erreurs = [abs(n - 1.0) for n in resultats if abs(n - 1.0) > 1e-10]
    assert len(erreurs) == 0, \
        f"{len(erreurs)} calculs instables sur 3 000 (sin²+cos²≠1)"
    print(f" 3 000 calculs trigo stables (sin²+cos²=1 ✓)")
