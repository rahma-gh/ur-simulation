"""Toutes les phases sont-elles déclarées dans le contrôleur C ?"""
import pytest

# États définis dans ure_can_grasper.c
ETATS_MACHINE = ["WAITING", "GRASPING", "ROTATING", "RELEASING", "ROTATING_BACK"]
NB_ETATS = len(ETATS_MACHINE)

def test_phases_presentes_dans_source():
    """Toutes les phases sont-elles déclarées dans le contrôleur C ?"""
    import os
    ctrl = "controllers/ure_can_grasper/ure_can_grasper.c"
    if not os.path.exists(ctrl):
        pytest.skip("Contrôleur C absent")
    with open(ctrl) as f:
        content = f.read()
    for etat in ETATS_MACHINE:
        assert etat in content, f"État manquant dans le contrôleur : {etat}"
    print(f" 5 états présents dans le contrôleur C")
