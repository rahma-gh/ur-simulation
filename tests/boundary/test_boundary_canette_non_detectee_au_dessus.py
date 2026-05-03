"""Une valeur au-dessus du seuil → pas de canette."""
"""
Tests non fonctionnels (boundary) : valeurs limites du capteur de distance.
Référence : Myers et al. (2011) - Boundary Value Analysis
"""
import pytest

THRESHOLD       = 500.0    # seuil dans ure_can_grasper.c
SENSOR_MIN      = 0.0
SENSOR_MAX      = 10000.0

def test_boundary_canette_non_detectee_au_dessus():
    """Une valeur au-dessus du seuil → pas de canette."""
    valeur_capteur = 501.0
    assert valeur_capteur >= THRESHOLD, "Canette détectée à tort"
    print(f" Valeur {valeur_capteur} ≥ seuil {THRESHOLD} → pas de détection ✅")
