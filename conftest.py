import sys
import os
import pytest
from datetime import datetime

# ─────────────────────────────────────────────
# Chemins Webots selon le système d'exploitation
# ─────────────────────────────────────────────
if os.name == 'nt':  # Windows
    WEBOTS_HOME = "C:/Program Files/Webots"
    sys.path.insert(0, f"{WEBOTS_HOME}/lib/controller/python")
    os.environ["WEBOTS_HOME"] = WEBOTS_HOME
    os.add_dll_directory(f"{WEBOTS_HOME}/lib/controller")
    os.environ["PATH"] = f"{WEBOTS_HOME}/lib/controller;" + os.environ["PATH"]
else:  # Linux (GitHub Actions / Docker)
    WEBOTS_HOME = "/usr/local/webots"
    sys.path.insert(0, f"{WEBOTS_HOME}/lib/controller/python")
    os.environ["WEBOTS_HOME"] = WEBOTS_HOME

# ─────────────────────────────────────────────
# Collecte des résultats pour le rapport custom
# ─────────────────────────────────────────────
_failed_tests = []
_total = 0
_passed = 0
_failed = 0
_start_time = None


def pytest_sessionstart(session):
    global _start_time
    _start_time = datetime.now()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    global _total, _passed, _failed
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":
        _total += 1
        if report.failed:
            _failed += 1
            error_msg = ""
            if report.longrepr:
                error_msg = str(report.longrepr)
                lines = error_msg.split("\n")
                short_lines = [l for l in lines if
                               "AssertionError" in l or
                               "assert" in l.lower() or
                               "FAILED" in l]
                error_msg = "\n".join(short_lines[:5]) if short_lines else "\n".join(lines[-5:])

            _failed_tests.append({
                "name": item.name,
                "file": str(item.fspath.basename) if hasattr(item, 'fspath') else "unknown",
                "nodeid": report.nodeid,
                "duration": round(report.duration, 3),
                "error": error_msg.strip()
            })
        elif report.passed:
            _passed += 1


def pytest_sessionfinish(session, exitstatus):
    end_time = datetime.now()
    duration = (end_time - _start_time).total_seconds() if _start_time else 0
    _generate_report(duration)


def _generate_report(duration):
    mins = int(duration // 60)
    secs = int(duration % 60)
    duration_str = f"{mins}m {secs}s"
    now = datetime.now().strftime("%d/%m/%Y à %H:%M:%S")
    success_rate = round((_passed / _total * 100) if _total > 0 else 100, 1)

    failed_cards = ""
    if _failed_tests:
        for i, t in enumerate(_failed_tests):
            error_escaped = (t['error']
                             .replace('&', '&amp;')
                             .replace('<', '&lt;')
                             .replace('>', '&gt;')
                             .replace('"', '&quot;'))
            delay = i * 0.1
            failed_cards += f"""
            <div class="test-card" style="animation-delay:{delay}s">
                <div class="test-card__header">
                    <div class="test-card__icon">✗</div>
                    <div class="test-card__info">
                        <div class="test-card__name">{t['name']}</div>
                        <div class="test-card__file">📄 {t['file']}</div>
                    </div>
                    <div class="test-card__duration">{t['duration']}s</div>
                </div>
                <div class="test-card__error">
                    <div class="test-card__error-label">▸ MESSAGE D'ERREUR</div>
                    <pre class="test-card__error-msg">{error_escaped if error_escaped else 'Voir logs détaillés'}</pre>
                </div>
                <div class="test-card__nodeid">{t['nodeid']}</div>
            </div>
            """
    else:
        failed_cards = """
        <div class="no-failures">
            <div class="no-failures__icon">✓</div>
            <div class="no-failures__title">Aucun échec détecté</div>
            <div class="no-failures__text">Tous les tests ont passé avec succès !</div>
        </div>
        """

    status_badge = "PIPELINE OK" if _failed == 0 else f"{_failed} ÉCHEC(S) DÉTECTÉ(S)"
    badge_class = "badge--ok" if _failed == 0 else "badge--fail"

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rapport CI — Universal Robots URe</title>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:ital,wght@0,400;0,700;1,400&family=Syne:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg:       #08080f;
            --surface:  #101018;
            --surface2: #18181f;
            --border:   #252535;
            --red:      #ff3b5c;
            --red-dim:  rgba(255,59,92,0.10);
            --green:    #00e676;
            --green-dim:rgba(0,230,118,0.08);
            --purple:   #7c5cfc;
            --yellow:   #ffd600;
            --cyan:     #00bcd4;
            --text:     #e4e4f0;
            --text-dim: #55556a;
            --mono:     'JetBrains Mono', monospace;
            --sans:     'Syne', sans-serif;
        }}
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{
            background: var(--bg);
            color: var(--text);
            font-family: var(--sans);
            min-height: 100vh;
            padding: 48px 24px 80px;
        }}
        .topbar {{
            max-width: 860px;
            margin: 0 auto 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border);
        }}
        .topbar__logo {{
            font-family: var(--mono);
            font-size: 12px;
            color: var(--text-dim);
            letter-spacing: 0.15em;
        }}
        .topbar__logo span {{ color: var(--cyan); }}
        .topbar__time {{
            font-family: var(--mono);
            font-size: 11px;
            color: var(--text-dim);
        }}
        .header {{
            max-width: 860px;
            margin: 0 auto 40px;
        }}
        .badge {{
            display: inline-flex;
            align-items: center;
            gap: 7px;
            font-family: var(--mono);
            font-size: 11px;
            padding: 5px 12px;
            border-radius: 6px;
            letter-spacing: 0.1em;
            margin-bottom: 16px;
        }}
        .badge::before {{
            content: '';
            width: 6px; height: 6px;
            border-radius: 50%;
            animation: pulse 1.5s infinite;
        }}
        .badge--fail {{
            background: var(--red-dim);
            border: 1px solid var(--red);
            color: var(--red);
        }}
        .badge--fail::before {{ background: var(--red); }}
        .badge--ok {{
            background: var(--green-dim);
            border: 1px solid var(--green);
            color: var(--green);
        }}
        .badge--ok::before {{ background: var(--green); }}
        @keyframes pulse {{
            0%,100% {{ opacity:1; }}
            50% {{ opacity:0.3; }}
        }}
        .header__title {{
            font-size: 38px;
            font-weight: 800;
            letter-spacing: -0.03em;
            line-height: 1;
            margin-bottom: 10px;
        }}
        .header__title span {{ color: var(--cyan); }}
        .header__sub {{
            font-family: var(--mono);
            font-size: 12px;
            color: var(--text-dim);
        }}
        .stats {{
            max-width: 860px;
            margin: 0 auto 32px;
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
        }}
        .stat {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 18px 16px;
            position: relative;
            overflow: hidden;
        }}
        .stat::after {{
            content: '';
            position: absolute;
            bottom: 0; left: 0; right: 0;
            height: 2px;
        }}
        .stat--f::after {{ background: var(--red); }}
        .stat--p::after {{ background: var(--green); }}
        .stat--t::after {{ background: var(--purple); }}
        .stat--d::after {{ background: var(--yellow); }}
        .stat__val {{
            font-size: 32px;
            font-weight: 800;
            font-family: var(--mono);
            line-height: 1;
            margin-bottom: 4px;
        }}
        .stat--f .stat__val {{ color: var(--red); }}
        .stat--p .stat__val {{ color: var(--green); }}
        .stat--t .stat__val {{ color: var(--purple); }}
        .stat--d .stat__val {{ color: var(--yellow); font-size: 22px; padding-top:5px; }}
        .stat__lbl {{
            font-size: 10px;
            color: var(--text-dim);
            letter-spacing: 0.1em;
            text-transform: uppercase;
            font-family: var(--mono);
        }}
        .progress-wrap {{
            max-width: 860px;
            margin: 0 auto 40px;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 18px 22px;
        }}
        .progress-hdr {{
            display: flex;
            justify-content: space-between;
            font-family: var(--mono);
            font-size: 11px;
            color: var(--text-dim);
            margin-bottom: 10px;
        }}
        .progress-hdr strong {{ color: var(--green); }}
        .pbar {{
            height: 6px;
            background: var(--surface2);
            border-radius: 3px;
            overflow: hidden;
        }}
        .pfill {{
            height: 100%;
            border-radius: 3px;
            background: linear-gradient(90deg, var(--cyan) 0%, var(--purple) 100%);
            width: {success_rate}%;
        }}
        .section {{
            max-width: 860px;
            margin: 0 auto 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .section__line {{ flex:1; height:1px; background: var(--border); }}
        .section__label {{
            font-family: var(--mono);
            font-size: 10px;
            letter-spacing: 0.15em;
            text-transform: uppercase;
            color: var(--text-dim);
        }}
        .section__count {{
            background: var(--red-dim);
            border: 1px solid var(--red);
            color: var(--red);
            font-family: var(--mono);
            font-size: 10px;
            padding: 2px 8px;
            border-radius: 4px;
        }}
        .cards {{
            max-width: 860px;
            margin: 0 auto;
            display: flex;
            flex-direction: column;
            gap: 14px;
        }}
        .test-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-left: 3px solid var(--red);
            border-radius: 10px;
            overflow: hidden;
            animation: rise 0.5s ease both;
        }}
        @keyframes rise {{
            from {{ opacity:0; transform:translateY(14px); }}
            to   {{ opacity:1; transform:translateY(0); }}
        }}
        .test-card__header {{
            display: flex;
            align-items: center;
            gap: 14px;
            padding: 16px 18px;
        }}
        .test-card__icon {{
            width: 34px; height: 34px;
            background: var(--red-dim);
            border: 1px solid var(--red);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--red);
            font-size: 15px;
            font-weight: 700;
            flex-shrink: 0;
        }}
        .test-card__info {{ flex:1; min-width:0; }}
        .test-card__name {{
            font-weight: 600;
            font-size: 14px;
            margin-bottom: 4px;
        }}
        .test-card__file {{
            font-family: var(--mono);
            font-size: 11px;
            color: var(--text-dim);
            background: var(--surface2);
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
        }}
        .test-card__duration {{
            font-family: var(--mono);
            font-size: 11px;
            color: var(--text-dim);
            flex-shrink: 0;
        }}
        .test-card__error {{
            border-top: 1px solid var(--border);
            padding: 14px 18px;
            background: rgba(255,59,92,0.03);
        }}
        .test-card__error-label {{
            font-family: var(--mono);
            font-size: 10px;
            letter-spacing: 0.1em;
            color: var(--red);
            opacity: 0.7;
            margin-bottom: 8px;
        }}
        .test-card__error-msg {{
            font-family: var(--mono);
            font-size: 12px;
            color: #ff8fa3;
            white-space: pre-wrap;
            word-break: break-all;
            line-height: 1.7;
        }}
        .test-card__nodeid {{
            border-top: 1px solid var(--border);
            padding: 8px 18px;
            font-family: var(--mono);
            font-size: 10px;
            color: var(--text-dim);
            opacity: 0.5;
        }}
        .no-failures {{
            background: var(--surface);
            border: 1px solid var(--green);
            border-radius: 10px;
            padding: 56px;
            text-align: center;
        }}
        .no-failures__icon {{
            font-size: 52px;
            color: var(--green);
            margin-bottom: 14px;
        }}
        .no-failures__title {{
            font-size: 20px;
            font-weight: 800;
            color: var(--green);
            margin-bottom: 6px;
        }}
        .no-failures__text {{
            font-family: var(--mono);
            font-size: 12px;
            color: var(--text-dim);
        }}
        .footer {{
            max-width: 860px;
            margin: 56px auto 0;
            padding-top: 20px;
            border-top: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            font-family: var(--mono);
            font-size: 10px;
            color: var(--text-dim);
            opacity: 0.4;
        }}
    </style>
</head>
<body>
    <div class="topbar">
        <div class="topbar__logo">CI/<span>CD</span> — ARCHITECTURE 1 — UNIVERSAL ROBOTS URe</div>
        <div class="topbar__time">{now}</div>
    </div>
    <div class="header">
        <div class="badge {badge_class}">{status_badge}</div>
        <div class="header__sub">Régression complète — scène ure.wbt — branche develop</div>
    </div>
    <div class="stats">
        <div class="stat stat--f">
            <div class="stat__val">{_failed}</div>
            <div class="stat__lbl">Échoués</div>
        </div>
        <div class="stat stat--p">
            <div class="stat__val">{_passed}</div>
            <div class="stat__lbl">Passés</div>
        </div>
        <div class="stat stat--t">
            <div class="stat__val">{_total}</div>
            <div class="stat__lbl">Total</div>
        </div>
        <div class="stat stat--d">
            <div class="stat__val">{duration_str}</div>
            <div class="stat__lbl">Durée</div>
        </div>
    </div>
    <div class="progress-wrap">
        <div class="progress-hdr">
            <span>Taux de réussite</span>
            <strong>{success_rate}%</strong>
        </div>
        <div class="pbar"><div class="pfill"></div></div>
    </div>
    <div class="section">
        <div class="section__line"></div>
        <div class="section__label">Tests échoués</div>
        <div class="section__count">{_failed}</div>
        <div class="section__line"></div>
    </div>
    <div class="cards">
        {failed_cards}
    </div>
    <div class="footer">
        <span>Généré par le pipeline CI/CD automatique</span>
        <span>Architecture Classique — Universal Robots URe</span>
    </div>
</body>
</html>"""

    os.makedirs("reports", exist_ok=True)
    with open("reports/report_failures.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n📊 Rapport échecs généré : reports/report_failures.html")
