"""La vitesse par défaut du bras (1.0 rad/s) est-elle dans les limites ?"""
import pytest

DEFAULT_SPEED = 1.0   # valeur par défaut dans ure_can_grasper.c
MAX_UR_SPEED  = 3.14  # rad/s — limite sécurité UR series

def test_vitesse_bras_par_defaut():
    """La vitesse par défaut du bras (1.0 rad/s) est-elle dans les limites ?"""
    assert 0.0 < DEFAULT_SPEED <= MAX_UR_SPEED, \
        f"Vitesse {DEFAULT_SPEED} hors limites [0, {MAX_UR_SPEED}]"
    print(f" Vitesse bras par défaut : {DEFAULT_SPEED} rad/s ✓")
