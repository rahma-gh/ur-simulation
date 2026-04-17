""""""Stress longue durée 1/3 : grasp_events stable après attente."""
    print("\n Stress longue durée 1/3...")
    time.sleep(120.0)
    if not os.path.exists(RESULTS_PATH):
        pytest.skip("JSON absent")
    with open(RESULTS_PATH) as f:
        r = json.load(f)
    assert r.get("grasp_events", 0) >= 1, \
        "Aucun événement de saisie après 60s"
    print(f" Partie 1/3 terminée — grasp_events={r['grasp_events']}")
