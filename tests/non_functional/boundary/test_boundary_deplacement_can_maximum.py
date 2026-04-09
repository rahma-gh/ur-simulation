"""Aucune canette n'a-t-elle été éjectée hors de la scène (< 7.5m) ?"""
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

def test_boundary_deplacement_can_maximum():
    """Aucune canette n'a-t-elle été éjectée hors de la scène (< 7.5m) ?"""
    r = load()
    initials = r.get("can_initial_positions", [[0,0,0]])
    finals   = r.get("can_final_positions",   [[0,0,0]])
    names    = r.get("can_names", [f"can({i+1})" for i in range(len(initials))])
    if not initials or not finals:
        pytest.skip("Positions non disponibles")
    for i, (init, final) in enumerate(zip(initials, finals)):
        dist = math.sqrt(sum((a-b)**2 for a,b in zip(init, final)))
        name = names[i] if i < len(names) else f"can({i+1})"
        assert dist <= PRECISION_MAX, \
            f"{name} éjectée : déplacement={dist:.3f}m > {PRECISION_MAX}m"
    print(f" Aucune canette éjectée (max déplacement ≤ {PRECISION_MAX}m) ✅")
