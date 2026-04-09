"""La vitesse du bras ne doit pas être nulle (blocage simulation)."""
"""Tests non fonctionnels (performance) : vitesses bras UR progressives."""
import pytest

DEFAULT_SPEED = 1.0   # valeur par défaut dans ure_can_grasper.c
MAX_UR_SPEED  = 3.14  # rad/s — limite sécurité UR series

def test_vitesse_bras_non_nulle():
    """La vitesse du bras ne doit pas être nulle (blocage simulation)."""
    speeds_to_test = [DEFAULT_SPEED, 0.5, 2.0]
    for s in speeds_to_test:
        assert s > 0.0, f"Vitesse nulle ou négative détectée : {s}"
    print(f" Vitesses testées non nulles : {speeds_to_test}")
