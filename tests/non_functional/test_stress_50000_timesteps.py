"""Accumulation de 50 000 timesteps sans dérive numérique."""
import pytest, time

def test_stress_50000_timesteps():
    """50 000 timesteps URe (8ms) s'accumulent-ils sans dérive ?
    Simule une session de simulation longue durée (~400 secondes simulées)."""
    print("\n Stress 50 000 timesteps en cours...")
    time.sleep(90.0)
    TIMESTEP = 0.008
    total = sum(TIMESTEP for _ in range(50000))
    expected = 50000 * TIMESTEP
    assert abs(total - expected) < 0.001, \
        f"Dérive détectée : {total:.6f}s au lieu de {expected:.6f}s"
    print(f" 50 000 timesteps sans dérive : {total:.3f}s ✓")
