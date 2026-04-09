"""Test fonctionnel : les positions cibles du bras sont-elles dans les limites UR ?"""
import pytest

TARGET_POSITIONS = [-1.88, -2.14, -2.38, -1.51]
UR_JOINT_MIN = -3.14159
UR_JOINT_MAX =  3.14159

def test_arm_target_positions_conformes():
    """Les 4 positions cibles [-1.88, -2.14, -2.38, -1.51] sont-elles dans [-3.14, 3.14] ?"""
    for pos in TARGET_POSITIONS:
        assert UR_JOINT_MIN <= pos <= UR_JOINT_MAX, \
            f"Position cible {pos} rad hors limites UR"
    print(f" Positions cibles conformes : {TARGET_POSITIONS} ✓")
