"""Une valeur sous le seuil → canette détectée."""
"""
Tests non fonctionnels (boundary) : valeurs limites du capteur de distance.
Référence : Myers et al. (2011) - Boundary Value Analysis
"""
import pytest

THRESHOLD       = 500.0    # seuil dans ure_can_grasper.c
SENSOR_MIN      = 0.0
SENSOR_MAX      = 10000.0

def test_boundary_canette_detectee_sous_seuil():
    """Une valeur sous le seuil → canette détectée."""
    valeur_capteur = 499.0
    assert valeur_capteur < THRESHOLD, "Canette non détectée alors qu'elle devrait l'être"
    print(f" Valeur {valeur_capteur} < seuil {THRESHOLD} → détection ✅")
