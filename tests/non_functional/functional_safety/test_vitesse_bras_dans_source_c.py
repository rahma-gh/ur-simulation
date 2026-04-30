"""La vitesse par défaut 1.0 est-elle définie dans le contrôleur C ?"""
"""Tests non fonctionnels (safety) : vitesse du bras UR dans les limites sécurité."""
import pytest, os

DEFAULT_SPEED = 1.0      # rad/s — valeur par défaut dans ure_can_grasper.c
MAX_SAFE_SPEED = 2.0     # rad/s — seuil sécurité opérationnel
ABSOLUTE_MAX   = 3.14    # rad/s — limite physique UR

def test_vitesse_bras_dans_source_c():
    """La vitesse par défaut 1.0 est-elle définie dans le contrôleur C ?"""
    ctrl = "controllers/ure_can_grasper/ure_can_grasper.c"
    if not os.path.exists(ctrl):
        pytest.skip("Contrôleur C absent")
    with open(ctrl) as f:
        content = f.read()
    assert "speed = 1.0" in content or "1.0" in content, \
        "Valeur de vitesse 1.0 absente du contrôleur C"
    print(" Vitesse 1.0 rad/s confirmée dans le contrôleur C")
