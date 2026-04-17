"""Le JSON est-il parseable et non corrompu ?"""
import pytest, time, os, json

RESULTS_PATH = os.path.abspath("reports/simulation_results.json")

def test_reliability_json_non_corrompu():
    """Le JSON est-il parseable et non corrompu ?"""
    time.sleep(0.5)
    if not os.path.exists(RESULTS_PATH):
        pytest.skip("JSON absent")
    try:
        with open(RESULTS_PATH) as f:
            data = json.load(f)
        assert isinstance(data, dict)
    except json.JSONDecodeError as e:
        pytest.fail(f"JSON corrompu : {e}")
    print(f" JSON valide et non corrompu ({len(data)} clés)")
