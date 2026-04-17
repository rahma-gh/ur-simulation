"""Position zéro (position neutre) → doit passer."""
"""Valeurs limites des positions joints UR.
Référence : Myers et al. (2011) - Boundary Value Analysis
"""
import pytest

JOINT_MIN = -3.14159
JOINT_MAX =  3.14159

def test_boundary_joint_zero():
    """Position zéro (position neutre) → doit passer."""
    pos = 0.0
    assert JOINT_MIN <= pos <= JOINT_MAX
    print(f" Position {pos} rad (neutre) dans les limites ✅")
