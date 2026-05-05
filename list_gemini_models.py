
import urllib.request, json, os

api_key = os.environ.get("GEMINI_API_KEY", "")
if not api_key:
    print("Lance : export GEMINI_API_KEY=AIza... puis relance ce script")
    exit(1)

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
req = urllib.request.Request(url, headers={"User-Agent": "ur-simulation-ci/1.0"})

try:
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.loads(r.read())
    models = body.get("models", [])
    print(f"\n{len(models)} modèles disponibles :")
    for m in models:
        name = m.get("name","")
        methods = m.get("supportedGenerationMethods", [])
        if "generateContent" in methods:
            print(f"  ✓ {name}")
except Exception as e:
    print(f"Erreur : {e}")
