# ur-simulation — Pipeline CI/CD Architecture Classique (Sans IA)

Projet de test de régression automatisé sur la scène Webots **Universal Robots URe** (`ure.wbt`).  
Après chaque `git push` sur la branche `develop`, le pipeline CI/CD exécute **l'ensemble** de la suite de tests sans aucune priorisation ni couche d'intelligence.

---

## 🔁 Flux Global

```
Développeur
    │
    ▼ Git Push (branche develop)
    │
    ▼ GitHub
    │
    ▼ Pipeline CI/CD (GitHub Actions)
    │
    ├── Build de l'environnement Docker (Ubuntu 22.04 + Webots + GCC)
    ├── Compilation du contrôleur C (ure_can_grasper.c)
    ├── Démarrage du simulateur CPS (Webots — ure.wbt)
    ├── Exécution du superviseur Python → simulation_results.json
    ├── Exécution de TOUS les tests de régression (pytest)
    ├── Collecte des résultats
    └── Génération du rapport HTML
```

---

## 🤖 Scène simulée : `ure.wbt`

La scène contient **3 robots Universal Robots** (UR3e, UR5e, UR10e), chacun équipé d'un **gripper Robotiq 3F**, qui saisissent des **canettes aluminium** sur un tapis roulant.

### Machine d'états du contrôleur (`ure_can_grasper.c`)

```
WAITING ──(distance < 500)──► GRASPING ──(counter=0)──► ROTATING
                                                              │
                                                   (wrist < -2.3)
                                                              │
                                                              ▼
                                                         RELEASING ──(counter=0)──► ROTATING_BACK
                                                                                          │
                                                                               (wrist > -0.1)
                                                                                          │
                                                                                          ▼
                                                                                       WAITING
```

---

## 📁 Structure du projet

```
ur-simulation/
├── .github/
│   └── workflows/
│       └── ci.yml                    ← Pipeline GitHub Actions
├── controllers/
│   ├── ure_can_grasper/
│   │   └── ure_can_grasper.c         ← Contrôleur C des robots UR
│   └── ure_supervisor/
│       └── ure_supervisor.py         ← Superviseur Python → JSON
├── worlds/
│   └── ure.wbt                       ← Scène Webots
├── reports/                          ← Rapports générés (ignorés par git)
├── tests/
│   ├── functional/                   ← Comportements, communication, capteurs, moteurs
│   └── non_functional/               ← Performance, temps réel, sécurité, limites, stress
├── conftest.py                       ← Hooks pytest + rapport HTML custom
├── Dockerfile                        ← Image Ubuntu 22.04 + Webots + GCC
├── requirements.txt
└── README.md
```

---

## 🧪 Suite de tests (106 tests)

| Catégorie        | Fichiers | Tests |
|------------------|----------|-------|
| Functional       | 35       | 35    |
| Non-functional   | 71       | 71    |
| **Total**        | **106**  | **106** |

---

## 🚀 Lancement local

### Prérequis
- Docker installé
- Webots R2025a (pour exécution locale sans Docker)

### Avec Docker

```bash
# Build
docker build -t ur-simulation .

# Run (simulation + tests)
docker run --name ur-test ur-simulation

# Récupérer les rapports
docker cp ur-test:/app/reports/. ./reports/
```

### Sans Docker (Webots local)

```bash
# 1. Lancer Webots sur la scène
webots --mode=fast --batch worlds/ure.wbt

# 2. Lancer les tests (une fois simulation_results.json généré)
pytest tests/ -v --html=reports/report.html
```

---

## 📊 Rapport

Après chaque exécution, deux rapports sont générés dans `reports/` :
- `report.html` — rapport pytest standard
- `report_failures.html` — rapport custom avec détail des échecs

---

## 🔑 Différences avec pick_and_place

| Aspect              | pick_and_place          | ure (ce projet)                  |
|---------------------|-------------------------|----------------------------------|
| Robots              | 1 robot mobile          | 3 robots fixes (UR3e/5e/10e)     |
| Objet               | Boîte                   | Canette aluminium                |
| Contrôleur          | Python                  | C (compilé GCC)                  |
| Gripper             | Pince simple            | Robotiq 3F (3 doigts)            |
| Timestep            | 32 ms                   | 8 ms                             |
| Logique             | Séquentielle            | Machine à 5 états                |
| JSON clé principale | `box_delivered`         | `sequence_complete`              |
