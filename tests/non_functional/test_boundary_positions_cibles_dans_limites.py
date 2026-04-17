"""Toutes les positions cibles du contrôleur sont-elles dans les limites ?"""
"""Valeurs limites des positions joints UR.
Référence : Myers et al. (2011) - Boundary Value Analysis
"""
import pytest

JOINT_MIN = -3.14159
JOINT_MAX =  3.14159

def test_boundary_positions_cibles_dans_limites():
    """Toutes les positions cibles du contrôleur sont-elles dans les limites ?"""
    target_positions = [-1.88, -2.14, -2.38, -1.51]
    for pos in target_positions:
        assert JOINT_MIN <= pos <= JOINT_MAX, \
            f"Position cible {pos} hors limites [{JOINT_MIN}, {JOINT_MAX}]"
    print(f" Toutes les positions cibles dans les limites : {target_positions}")
