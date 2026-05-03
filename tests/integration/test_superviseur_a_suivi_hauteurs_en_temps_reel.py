"""Le superviseur a-t-il suivi les hauteurs Z des canettes en temps réel ?"""
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

def test_superviseur_a_suivi_hauteurs_en_temps_reel():
    """Le superviseur a-t-il suivi les hauteurs Z des canettes en temps réel ?
    Preuve : max_can_heights > positions initiales Z (le suivi temps réel a fonctionné)."""
    r = load()
    heights  = r.get("max_can_heights", [])
    initials = r.get("can_initial_positions", [])
    assert len(heights) == len(initials), "Nombre de hauteurs != nombre de positions"
    # Au moins une canette doit avoir une hauteur max > sa hauteur initiale
    eleves = sum(
        1 for h, init in zip(heights, initials)
        if h > init[2] + 0.10   # au moins 10cm de plus que la position initiale
    )
    assert eleves > 0, \
        "Aucune canette n'a été détectée en mouvement vertical — " \
        "le suivi temps réel getPosition() n'a pas fonctionné"
    print(f" Superviseur suivi temps réel : {eleves}/{len(heights)} canettes soulevées ✓")
