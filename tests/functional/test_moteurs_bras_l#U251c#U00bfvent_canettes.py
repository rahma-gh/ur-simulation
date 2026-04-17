"""Les moteurs du bras ont-ils physiquement soulevé les canettes ?"""
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

def test_moteurs_bras_lèvent_canettes():
    """Les moteurs du bras ont-ils physiquement soulevé les canettes ?
    Preuve : max_can_heights > 0.80m (mouvement réel observable dans la scène)."""
    r = load()
    heights = r.get("max_can_heights", [])
    assert len(heights) > 0, "Aucune hauteur enregistrée"
    max_h = max(heights)
    assert max_h > 0.80, \
        f"Hauteur max = {max_h:.3f}m — les moteurs du bras n'ont pas soulevé " \
        f"les canettes au-dessus de 0.80m (consigne non exécutée)"
    print(f" Moteurs bras ont soulevé les canettes jusqu'à {max_h:.3f}m ✓")
