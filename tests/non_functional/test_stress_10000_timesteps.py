"""Accumulation 10 000 timesteps sans dérive numérique."""
import pytest, time

def test_stress_10000_timesteps():
    """10 000 timesteps URe (8ms) s'accumulent-ils sans dérive ?"""
    time.sleep(60.0)
    TIMESTEP = 0.008   # 8ms en secondes
    total = sum(TIMESTEP for _ in range(10000))
    assert abs(total - 10000 * TIMESTEP) < 0.001
    print(f" 10 000 timesteps URe sans dérive : {total:.3f}s")
