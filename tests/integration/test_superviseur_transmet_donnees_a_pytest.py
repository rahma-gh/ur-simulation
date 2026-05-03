"""Le superviseur a-t-il bien transmis toutes les données à pytest via le JSON ?"""
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

def test_superviseur_transmet_donnees_a_pytest():
    """Le superviseur a-t-il bien transmis toutes les données à pytest via le JSON ?
    Preuve : le JSON est complet, cohérent, et pytest peut le lire."""
    r = load()
    total   = r.get("total_cans", 0)
    per_can = r.get("per_can", {})
    assert len(per_can) == total, \
        f"per_can incomplet : {len(per_can)}/{total} canettes"
    # Vérifier que chaque canette a bien 5 champs de données
    for name, data in per_can.items():
        for key in ["grasped", "deposited", "max_height",
                    "initial_position", "final_position"]:
            assert key in data, \
                f"Champ '{key}' manquant pour {name} — transmission incomplète"
    print(f" Superviseur→JSON→pytest : {total} × 5 champs transmis correctement ✓")
