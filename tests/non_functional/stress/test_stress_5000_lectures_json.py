"""Tests de stress lourd : 5 000 lectures consécutives du JSON sans erreur."""
import pytest, time, os, json

RESULTS_PATH = os.path.abspath("reports/simulation_results.json")

def test_stress_5000_lectures_json():
    """Le fichier simulation_results.json supporte-t-il 5 000 lectures consécutives ?
    Simule un système de monitoring intensif qui lit les résultats en continu."""
    print("\n Stress 5 000 lectures JSON en cours...")
    time.sleep(60.0)
    if not os.path.exists(RESULTS_PATH):
        pytest.skip("JSON absent")
    erreurs     = 0
    incoherents = 0
    for i in range(5000):
        try:
            with open(RESULTS_PATH) as f:
                data = json.load(f)
            # Vérification de cohérence minimale à chaque lecture
            if not isinstance(data, dict):
                incoherents += 1
            if data.get("total_cans", 0) != 15:
                incoherents += 1
        except Exception:
            erreurs += 1
    assert erreurs == 0, \
        f"{erreurs}/5 000 lectures JSON ont échoué (erreur I/O ou parsing)"
    assert incoherents == 0, \
        f"{incoherents}/5 000 lectures ont retourné des données incohérentes"
    print(f" 5 000/5 000 lectures JSON réussies et cohérentes ✓")
