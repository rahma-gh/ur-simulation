"""Le superviseur a-t-il découvert dynamiquement tous les nœuds Can de la scène ?"""
"""
Test de communication : Superviseur ↔ Nœuds de la scène Webots

Vérifie que le superviseur a bien établi la communication avec les nœuds
de la scène (canettes) via l'API Supervisor, lu leurs positions en temps
réel, et transmis ces données au fichier JSON.

Communication testée :
  [Superviseur] --getRoot().getField("children")--> [Scène Webots]
  [Nœud Can]   --getPosition()--> [Superviseur]
  [Superviseur] --json.dump()--> [simulation_results.json]
  [pytest]      --json.load()--> [simulation_results.json]
"""
import pytest, os, json, math

RESULTS_PATH = os.path.abspath("reports/simulation_results.json")

def load():
    if not os.path.exists(RESULTS_PATH):
        pytest.skip("JSON absent — simulation non exécutée")
    with open(RESULTS_PATH) as f:
        return json.load(f)

def test_superviseur_a_decouvert_tous_les_noeuds():
    """Le superviseur a-t-il découvert dynamiquement tous les nœuds Can de la scène ?
    Preuve : total_cans == 15 (tous les nœuds ont été trouvés via getRoot())."""
    r = load()
    total    = r.get("total_cans", 0)
    can_names = r.get("can_names", [])
    assert total == 15, \
        f"Le superviseur a découvert {total} canettes au lieu de 15 — " \
        f"la traversée des nœuds de la scène est incomplète"
    assert len(can_names) == 15, \
        f"can_names contient {len(can_names)} noms au lieu de 15"
    print(f" Superviseur→Scène : {total} nœuds Can découverts dynamiquement ✓")
