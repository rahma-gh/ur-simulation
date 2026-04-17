"""Le TIME_STEP du contrôleur est-il un multiple du basicTimeStep ?"""
import pytest

TIMESTEP_WBT = 8    # basicTimeStep déclaré dans ure.wbt
TIMESTEP_CTRL = 32  # TIME_STEP dans ure_can_grasper.c (multiple de 8)

def test_timestep_controleur_multiple_wbt():
    """Le TIME_STEP du contrôleur est-il un multiple du basicTimeStep ?"""
    assert TIMESTEP_CTRL % TIMESTEP_WBT == 0, \
        f"TIME_STEP={TIMESTEP_CTRL} n'est pas un multiple de basicTimeStep={TIMESTEP_WBT}"
    print(f" TIME_STEP contrôleur ({TIMESTEP_CTRL}ms) = {TIMESTEP_CTRL//TIMESTEP_WBT}×basicTimeStep")
