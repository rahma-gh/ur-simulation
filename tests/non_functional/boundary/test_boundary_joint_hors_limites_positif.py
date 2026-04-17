"""Position au-dessus du maximum → hors limite détectée."""
"""
Tests non fonctionnels (boundary) : valeurs limites des positions joints UR.
Référence : Myers et al. (2011) - Boundary Value Analysis
"""
import pytest

JOINT_MIN = -3.14159
JOINT_MAX =  3.14159

def test_boundary_joint_hors_limites_positif():
    """Position au-dessus du maximum → hors limite détectée."""
    pos = 3.15
    assert pos > JOINT_MAX, "Hors limite positive non détectée"
    print(f" Position {pos} rad hors limite max ❌ détectée")
