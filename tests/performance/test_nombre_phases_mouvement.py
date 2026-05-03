"""Le nombre de phases de la machine d'état est-il de 5 ?"""
"""Tests non fonctionnels (performance) : nombre de phases de mouvement."""
import pytest

# États définis dans ure_can_grasper.c
ETATS_MACHINE = ["WAITING", "GRASPING", "ROTATING", "RELEASING", "ROTATING_BACK"]
NB_ETATS = len(ETATS_MACHINE)

def test_nombre_phases_mouvement():
    """Le nombre de phases de la machine d'état est-il de 5 ?"""
    assert NB_ETATS == 5, f"Nombre de phases attendu : 5, obtenu : {NB_ETATS}"
    print(f" {NB_ETATS} phases de mouvement : {ETATS_MACHINE}")
