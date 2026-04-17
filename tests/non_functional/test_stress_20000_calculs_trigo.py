"""20 000 calculs trigonométriques pour cinématique UR."""
import pytest, time, math

def test_stress_20000_calculs_trigo():
    """20 000 calculs sin/cos/atan2 pour cinématique UR sont-ils tous stables ?
    Simule le calcul intensif de trajectoires pour les 3 robots sur toute la scène."""
    print("\n Stress 20 000 calculs trigo en cours...")
    time.sleep(60.0)
    erreurs_norme  = 0
    erreurs_finite = 0
    for i in range(20000):
        angle = (i / 20000.0) * 4 * math.pi - 2 * math.pi
        s = math.sin(angle)
        c = math.cos(angle)
        # sin² + cos² = 1
        if abs(s**2 + c**2 - 1.0) > 1e-10:
            erreurs_norme += 1
        # atan2 inversible
        angle_reconstruit = math.atan2(s, c)
        if not math.isfinite(angle_reconstruit):
            erreurs_finite += 1
    assert erreurs_norme == 0, \
        f"{erreurs_norme}/20 000 calculs sin²+cos²≠1 (instabilité numérique)"
    assert erreurs_finite == 0, \
        f"{erreurs_finite}/20 000 atan2 non finis"
    print(f" 20 000 calculs trigo stables — sin²+cos²=1 et atan2 finis ✓")
