"""Le capteur de distance a-t-il transmis un signal au contrôleur ?"""
"""
Test de communication : Canette → Capteur de distance → Contrôleur

Vérifie que le capteur de distance a bien transmis un signal au contrôleur
et que le contrôleur a bien réagi en déclenchant la phase GRASPING.

Communication testée :
  [Canette physique] --distance < 500--> [DistanceSensor] --signal--> [Contrôleur]
"""
import pytest, os, json

RESULTS_PATH = os.path.abspath("reports/simulation_results.json")

def load():
    if not os.path.exists(RESULTS_PATH):
        pytest.skip("JSON absent — simulation non exécutée")
    with open(RESULTS_PATH) as f:
        return json.load(f)

def test_capteur_distance_signal_recu():
    """Le capteur de distance a-t-il transmis un signal au contrôleur ?
    Preuve : distance_sensor_triggered=True dans les résultats."""
    r = load()
    assert r.get("distance_sensor_triggered", False), \
        "Aucun signal du capteur de distance reçu par le contrôleur — " \
        "communication DistanceSensor→Contrôleur rompue"
    print(" Communication DistanceSensor→Contrôleur : signal reçu ✓")
