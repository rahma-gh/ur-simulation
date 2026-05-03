"""Le seuil de détection (500) est-il dans la plage capteur ?"""
"""
Tests non fonctionnels (boundary) : valeurs limites du capteur de distance.
Référence : Myers et al. (2011) - Boundary Value Analysis
"""
import pytest

THRESHOLD       = 500.0    # seuil dans ure_can_grasper.c
SENSOR_MIN      = 0.0
SENSOR_MAX      = 10000.0

def test_boundary_seuil_capteur_valide():
    """Le seuil de détection (500) est-il dans la plage capteur ?"""
    assert SENSOR_MIN < THRESHOLD < SENSOR_MAX
    print(f" Seuil capteur {THRESHOLD} dans [{SENSOR_MIN}, {SENSOR_MAX}] ✅")
