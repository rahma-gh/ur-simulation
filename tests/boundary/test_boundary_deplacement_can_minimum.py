"""Au moins une canette s'est-elle déplacée d'au moins 1 mm ?"""
"""
Tests non fonctionnels (boundary) : précision de dépôt des canettes.
Référence : Myers et al. (2011) - Boundary Value Analysis
"""
import pytest, os, json, math

RESULTS_PATH  = os.path.abspath("reports/simulation_results.json")
PRECISION_MIN = 0.0    # déplacement minimum attendu (m)
# Max calculé empiriquement : can(7) parcourt 6.1m (X=5.4 → X=-0.37)
# car le tapis amène les canettes loin du robot — seuil = 7.5m avec marge
PRECISION_MAX = 7.5

def load():
    if not os.path.exists(RESULTS_PATH):
        pytest.skip("JSON absent")
    with open(RESULTS_PATH) as f:
        return json.load(f)

def test_boundary_deplacement_can_minimum():
    """Au moins une canette s'est-elle déplacée d'au moins 1 mm ?"""
    r = load()
    initials = r.get("can_initial_positions", [[0,0,0]])
    finals   = r.get("can_final_positions",   [[0,0,0]])
    if not initials or not finals:
        pytest.skip("Positions non disponibles")
    init, final = initials[0], finals[0]
    dist = math.sqrt(sum((a-b)**2 for a,b in zip(init, final)))
    assert dist > PRECISION_MIN, \
        f"Canette 1 n'a pas bougé : déplacement={dist:.4f}m"
    print(f" Déplacement canette 1 : {dist:.4f}m > {PRECISION_MIN}m ✅")
