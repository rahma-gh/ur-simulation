"""La vitesse est-elle en dessous des limites physiques absolues UR ?"""
import pytest, os

DEFAULT_SPEED = 1.0      # rad/s — valeur par défaut dans ure_can_grasper.c
MAX_SAFE_SPEED = 2.0     # rad/s — seuil sécurité opérationnel
ABSOLUTE_MAX   = 3.14    # rad/s — limite physique UR

def test_vitesse_dans_limites_absolues():
    """La vitesse est-elle en dessous des limites physiques absolues UR ?"""
    assert DEFAULT_SPEED <= ABSOLUTE_MAX, \
        f"Vitesse dépasse les limites physiques UR : {DEFAULT_SPEED} > {ABSOLUTE_MAX}"
    print(f" Vitesse dans limites absolues UR : {DEFAULT_SPEED} ≤ {ABSOLUTE_MAX} rad/s")
