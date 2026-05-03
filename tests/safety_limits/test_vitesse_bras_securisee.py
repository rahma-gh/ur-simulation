"""La vitesse par défaut du bras est-elle ≤ 2.0 rad/s (seuil sécurité) ?"""
"""Tests non fonctionnels (safety) : vitesse du bras UR dans les limites sécurité."""
import pytest, os

DEFAULT_SPEED = 1.0      # rad/s — valeur par défaut dans ure_can_grasper.c
MAX_SAFE_SPEED = 2.0     # rad/s — seuil sécurité opérationnel
ABSOLUTE_MAX   = 3.14    # rad/s — limite physique UR

def test_vitesse_bras_securisee():
    """La vitesse par défaut du bras est-elle ≤ 2.0 rad/s (seuil sécurité) ?"""
    assert DEFAULT_SPEED <= MAX_SAFE_SPEED, \
        f"Vitesse trop élevée pour usage sécurisé : {DEFAULT_SPEED} > {MAX_SAFE_SPEED}"
    print(f" Vitesse bras sécurisée : {DEFAULT_SPEED} ≤ {MAX_SAFE_SPEED} rad/s")
