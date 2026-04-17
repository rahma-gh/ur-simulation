"""Position exactement au minimum → doit passer."""
"""
Tests non fonctionnels (boundary) : valeurs limites des positions joints UR.
Référence : Myers et al. (2011) - Boundary Value Analysis
"""
import pytest

JOINT_MIN = -3.14159
JOINT_MAX =  3.14159

def test_boundary_joint_minimum():
    """Position exactement au minimum → doit passer."""
    pos = -3.14159
    assert JOINT_MIN <= pos <= JOINT_MAX
    print(f" Position {pos} rad à la limite min ✅")
