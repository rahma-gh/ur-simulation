import urllib.request, json, os, time

api_key = os.environ.get("GEMINI_API_KEY", "")
if not api_key:
    print("Lance : $env:GEMINI_API_KEY='ta_cle'  puis relance")
    exit(1)

# Modèles candidats gratuits depuis ta liste
candidates = [
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
    "gemini-pro-latest",
    "gemma-3-1b-it",
    "gemma-3-4b-it",
]

payload = json.dumps({
    "contents": [{"role": "user", "parts": [{"text": "Réponds juste: OK"}]}],
    "generationConfig": {"maxOutputTokens": 5}
}).encode()

print("Test des modèles gratuits disponibles...\n")
for model in candidates:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    req = urllib.request.Request(url, data=payload,
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            print(f"  ✓ FONCTIONNE : {model}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:150]
        if "429" in str(e.code):
            print(f"  ✗ 429 quota=0 : {model}")
        elif "404" in str(e.code):
            print(f"  ✗ 404 introuvable : {model}")
        else:
            print(f"  ✗ {e.code} : {model} → {body[:80]}")
    time.sleep(1)
