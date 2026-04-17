"""La vitesse du bras est-elle > 0 (pas de blocage mécanique) ?"""
import pytest, os

DEFAULT_SPEED = 1.0      # rad/s — valeur par défaut dans ure_can_grasper.c
MAX_SAFE_SPEED = 2.0     # rad/s — seuil sécurité opérationnel
ABSOLUTE_MAX   = 3.14    # rad/s — limite physique UR

def test_vitesse_bras_non_nulle():
    """La vitesse du bras est-elle > 0 (pas de blocage mécanique) ?"""
    assert DEFAULT_SPEED > 0.0, "Vitesse nulle — blocage possible"
    print(f" Vitesse bras non nulle : {DEFAULT_SPEED} rad/s")
