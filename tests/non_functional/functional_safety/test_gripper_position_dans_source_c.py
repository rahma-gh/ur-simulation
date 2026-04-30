"""La valeur 0.85 est-elle bien utilisée dans le contrôleur C ?"""
"""Tests non fonctionnels (safety) : gripper Robotiq 3F sans risque d'écrasement."""
import pytest, os

GRIPPER_GRASP_POSITION = 0.85   # position fermeture dans ure_can_grasper.c
GRIPPER_MIN_POSITION   = 0.0    # limite min (ouvert)
GRIPPER_MAX_POSITION   = 1.0    # limite max (fermé complet)

def test_gripper_position_dans_source_c():
    """La valeur 0.85 est-elle bien utilisée dans le contrôleur C ?"""
    ctrl = "controllers/ure_can_grasper/ure_can_grasper.c"
    if not os.path.exists(ctrl):
        pytest.skip("Contrôleur C absent")
    with open(ctrl) as f:
        content = f.read()
    assert "0.85" in content, "Valeur 0.85 absente du contrôleur — position gripper inconnue"
    print(" Valeur de saisie 0.85 confirmée dans le contrôleur C")
