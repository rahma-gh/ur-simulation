"""La macro TIME_STEP est-elle bien définie à 32 dans le contrôleur C ?"""
"""Tests non fonctionnels (performance) : timestep ure.wbt conforme."""
import pytest

TIMESTEP_WBT = 8    # basicTimeStep déclaré dans ure.wbt
TIMESTEP_CTRL = 32  # TIME_STEP dans ure_can_grasper.c (multiple de 8)

def test_timestep_dans_source_c():
    """La macro TIME_STEP est-elle bien définie à 32 dans le contrôleur C ?"""
    import os
    ctrl = "controllers/ure_can_grasper/ure_can_grasper.c"
    if not os.path.exists(ctrl):
        pytest.skip("Contrôleur C absent")
    with open(ctrl) as f:
        content = f.read()
    assert "#define TIME_STEP 32" in content, "Macro TIME_STEP 32 absente du contrôleur"
    print(" #define TIME_STEP 32 présent dans le contrôleur")
