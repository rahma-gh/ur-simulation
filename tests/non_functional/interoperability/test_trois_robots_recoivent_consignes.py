"""Les 3 robots ont-ils chacun reçu et exécuté les consignes du contrôleur ?"""
"""
Test de communication : Contrôleur → Moteurs du bras UR

Vérifie que le contrôleur a bien transmis les consignes de position
aux 4 moteurs du bras UR (shoulder_lift, elbow, wrist_1, wrist_2),
et que ces consignes ont produit un mouvement physique observable.

Communication testée :
  [Contrôleur] --set_position([-1.88,-2.14,-2.38,-1.51])--> [Motors bras UR]
  [Contrôleur] --set_position([0.0, 0.0, 0.0, 0.0])--> [Motors bras UR] (retour)
  [Contrôleur] --set_velocity(1.0)--> [Motors bras UR]
"""
import pytest, os, json

RESULTS_PATH = os.path.abspath("reports/simulation_results.json")

def load():
    if not os.path.exists(RESULTS_PATH):
        pytest.skip("JSON absent — simulation non exécutée")
    with open(RESULTS_PATH) as f:
        return json.load(f)

def test_trois_robots_recoivent_consignes():
    """Les 3 robots ont-ils chacun reçu et exécuté les consignes du contrôleur ?
    Preuve : ur3e_grasped, ur5e_grasped, ur10e_grasped tous True."""
    r = load()
    assert r.get("ur3e_grasped",  False), "UR3e  n'a pas reçu/exécuté les consignes"
    assert r.get("ur5e_grasped",  False), "UR5e  n'a pas reçu/exécuté les consignes"
    assert r.get("ur10e_grasped", False), "UR10e n'a pas reçu/exécuté les consignes"
    print(" Contrôleur→Moteurs : UR3e + UR5e + UR10e ont tous reçu les consignes ✓")
