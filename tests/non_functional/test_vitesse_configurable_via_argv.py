"""La vitesse est-elle configurable via argument au lancement ?"""
import pytest

DEFAULT_SPEED = 1.0   # valeur par défaut dans ure_can_grasper.c
MAX_UR_SPEED  = 3.14  # rad/s — limite sécurité UR series

def test_vitesse_configurable_via_argv():
    """La vitesse est-elle configurable via argument au lancement ?"""
    import os
    ctrl = "controllers/ure_can_grasper/ure_can_grasper.c"
    if not os.path.exists(ctrl):
        pytest.skip("Contrôleur C absent")
    with open(ctrl) as f:
        content = f.read()
    assert "argc" in content and "argv" in content, \
        "Contrôleur ne supporte pas d'argument de vitesse"
    assert "sscanf" in content, "sscanf absent — vitesse non parsée depuis argv"
    print(" Vitesse configurable via argv[1]")
