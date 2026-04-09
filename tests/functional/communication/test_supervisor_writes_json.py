"""Le superviseur a-t-il généré le fichier de résultats ?"""
"""Le superviseur écrit-il correctement le fichier JSON de résultats ?"""
import os, json, pytest

RESULTS_PATH = os.path.abspath("reports/simulation_results.json")

def test_supervisor_writes_json():
    """Le superviseur a-t-il généré le fichier de résultats ?"""
    assert os.path.exists(RESULTS_PATH), \
        f"JSON absent : {RESULTS_PATH} — le superviseur n'a pas exporté les résultats"
    size = os.path.getsize(RESULTS_PATH)
    assert size > 10, f"JSON trop petit ({size} octets) — probablement vide"
    print(f" JSON présent ({size} octets)")
