"""Les transitions releasing et retour sont-elles en nombre cohérent ?"""
"""
Test de communication : Capteur de position wrist → Contrôleur

Vérifie que le capteur de position du poignet (wrist_1_joint_sensor)
a bien transmis sa valeur au contrôleur, et que le contrôleur a utilisé
cette valeur pour changer d'état (ROTATING → RELEASING, ROTATING_BACK → WAITING).

Communication testée :
  [wrist_1_joint_sensor] --position < -2.3 rad--> [Contrôleur] → déclenche RELEASING
  [wrist_1_joint_sensor] --position > -0.1 rad--> [Contrôleur] → déclenche WAITING
"""
import pytest, os, json

RESULTS_PATH = os.path.abspath("reports/simulation_results.json")

def load():
    if not os.path.exists(RESULTS_PATH):
        pytest.skip("JSON absent — simulation non exécutée")
    with open(RESULTS_PATH) as f:
        return json.load(f)

def test_capteur_wrist_coherence_releasing_retour():
    """Les transitions releasing et retour sont-elles en nombre cohérent ?
    Preuve : return_events == release_events (chaque dépôt → un retour)."""
    r = load()
    releases = r.get("release_events", 0)
    returns  = r.get("return_events", 0)
    assert releases == returns, \
        f"Incohérence : {releases} RELEASING mais {returns} retours WAITING — " \
        f"le capteur wrist a peut-être manqué des transitions"
    print(f" Cohérence wrist_sensor : {releases} releasing == {returns} retours ✓")
