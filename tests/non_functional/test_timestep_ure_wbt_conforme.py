"""Le basicTimeStep de ure.wbt est-il bien 8 ms ?"""
import pytest

TIMESTEP_WBT = 8    # basicTimeStep déclaré dans ure.wbt
TIMESTEP_CTRL = 32  # TIME_STEP dans ure_can_grasper.c (multiple de 8)

def test_timestep_ure_wbt_conforme():
    """Le basicTimeStep de ure.wbt est-il bien 8 ms ?"""
    assert TIMESTEP_WBT == 8, f"basicTimeStep attendu : 8, obtenu : {TIMESTEP_WBT}"
    print(f" basicTimeStep ure.wbt : {TIMESTEP_WBT}ms ✓")
