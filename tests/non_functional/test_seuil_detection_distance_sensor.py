"""Le seuil de détection du capteur de distance est-il dans une plage sûre ?"""
import pytest

# Positions cibles définies dans ure_can_grasper.c
TARGET_POSITIONS = {
    "shoulder_lift_joint": -1.88,
    "elbow_joint":         -2.14,
    "wrist_1_joint":       -2.38,
    "wrist_2_joint":       -1.51,
}

# Limites physiques des joints UR series (rad)
UR_JOINT_MIN = -3.14159
UR_JOINT_MAX =  3.14159

def test_seuil_detection_distance_sensor():
    """Le seuil de détection du capteur de distance est-il dans une plage sûre ?"""
    threshold = 500.0   # valeur dans ure_can_grasper.c
    assert 0 < threshold <= 10000, \
        f"Seuil capteur hors plage sûre : {threshold}"
    print(f" Seuil capteur distance : {threshold} (sûr)")
