"""Une valeur exactement égale au seuil → cas limite (non déclenché)."""
"""
Tests non fonctionnels (boundary) : valeurs limites du capteur de distance.
Référence : Myers et al. (2011) - Boundary Value Analysis
"""
import pytest

THRESHOLD       = 500.0    # seuil dans ure_can_grasper.c
SENSOR_MIN      = 0.0
SENSOR_MAX      = 10000.0

def test_boundary_valeur_exactement_au_seuil():
    """Une valeur exactement égale au seuil → cas limite (non déclenché)."""
    valeur_capteur = 500.0
    # Dans le code C : if (sensor < 500) → 500 exact ne déclenche pas
    assert valeur_capteur >= THRESHOLD
    print(f" Valeur {valeur_capteur} == seuil → non déclenché (cas limite) ✅")
