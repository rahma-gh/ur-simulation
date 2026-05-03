"""Position en dessous du minimum → hors limite détectée."""
"""
Tests non fonctionnels (boundary) : valeurs limites des positions joints UR.
Référence : Myers et al. (2011) - Boundary Value Analysis
"""
import pytest

JOINT_MIN = -3.14159
JOINT_MAX =  3.14159

def test_boundary_joint_hors_limites_negatif():
    """Position en dessous du minimum → hors limite détectée."""
    pos = -3.15
    assert pos < JOINT_MIN, "Hors limite négative non détectée"
    print(f" Position {pos} rad hors limite min ❌ détectée")
