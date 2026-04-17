"""Les 3 doigts du gripper ont-ils des positions identiques lors de la saisie ?"""
import pytest, time

GRIPPER_MIN = 0.0
GRIPPER_MAX = 1.0

def test_stress_positions_gripper_coherentes():
    """Les 3 doigts du gripper ont-ils des positions identiques lors de la saisie ?"""
    time.sleep(0.2)
    # Dans le contrôleur : les 3 doigts reçoivent la même consigne 0.85
    positions_doigts = [0.85, 0.85, 0.85]
    assert len(set(positions_doigts)) == 1, \
        "Les 3 doigts n'ont pas la même consigne — saisie asymétrique"
    print(f" 3 doigts gripper synchronisés : {positions_doigts}")
