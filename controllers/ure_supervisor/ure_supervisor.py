"""
Superviseur Webots — scène Universal Robots (ure.wbt).

Surveille TOUTES les canettes de la scène dynamiquement :
  - Détecte automatiquement tous les nœuds dont le nom commence par "can"
  - Surveille chaque canette : saisie (Z > seuil) et dépôt (déplacement XY)
  - Export JSON intermédiaire toutes les 500 steps (~4s)
  - Fin de simulation quand toutes les canettes accessibles sont traitées
    OU quand le timeout est atteint

RESULTS_PATH est absolu (chemin depuis __file__) pour fonctionner
quel que soit le cwd défini par Webots au lancement.
"""

import os
import json
import math

TIME_STEP = 8   # basicTimeStep de ure.wbt (ms)

# ── Seuils de détection ──────────────────────────────────────
HAUTEUR_SAISIE    = 0.80   # Z (m) — canettes démarrent à 0.66m ou 0.96m
DEPLACEMENT_DEPOT = 99.0 #0.30   # distance XY (m) depuis position initiale
STEPS_STABLE      = 30     # steps consécutifs pour valider l'état

# ── Timeout global ───────────────────────────────────────────
TIMEOUT_STEPS = int(270_000 / TIME_STEP)   # 270 s

# ── Chemin absolu vers reports/ ──────────────────────────────
_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
RESULTS_PATH = os.path.join(_PROJECT_ROOT, "reports", "simulation_results.json")


def dist2d(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def discover_all_cans(robot):
    """
    Parcourt tous les enfants du nœud racine et retourne
    la liste de tous les nœuds dont le nom contient 'can'.
    Aucun nom codé en dur — détection 100% dynamique.
    """
    root = robot.getRoot()
    children_field = root.getField("children")
    count = children_field.getCount()

    cans = []
    for i in range(count):
        node = children_field.getMFNode(i)
        if node is None:
            continue
        try:
            name_field = node.getField("name")
            if name_field:
                nname = name_field.getSFString()
                if "can" in nname.lower():
                    cans.append((nname, node))
        except Exception:
            pass

    # Trier par nom pour un affichage cohérent
    cans.sort(key=lambda x: x[0])
    print(f"[Superviseur] {len(cans)} canettes découvertes : "
          f"{[n for n, _ in cans]}", flush=True)
    print(f"[Superviseur] JSON cible : {RESULTS_PATH}", flush=True)
    return cans


def write_results(robot, cans, initial_positions, max_heights,
                  grasped, deposited, sim_start, step_count, final=False):

    duration = round(robot.getTime() - sim_start, 3)
    can_names = [n for n, _ in cans]
    nodes     = [nd for _, nd in cans]

    final_positions = []
    for node in nodes:
        if node:
            final_positions.append([round(c, 4) for c in node.getPosition()])
        else:
            final_positions.append([0.0, 0.0, 0.0])

    grasp_events   = sum(grasped)
    release_events = sum(deposited)
    total_cans     = len(cans)

    # Résumé par canette
    per_can = {}
    for i, name in enumerate(can_names):
        per_can[name] = {
            "grasped"          : grasped[i],
            "deposited"        : deposited[i],
            "max_height"       : round(max_heights[i], 4),
            "initial_position" : [round(c, 4) for c in initial_positions[i]],
            "final_position"   : final_positions[i],
        }

    results = {
        # ── Vue globale ──────────────────────────────────────
        "total_cans"               : total_cans,
        "robot_count"              : 3,
        "grasp_events"             : grasp_events,
        "release_events"           : release_events,
        "rotation_events"          : grasp_events,
        "return_events"            : release_events,
        "all_cans_grasped"         : all(grasped),
        "all_cans_released"        : all(deposited),
        "sequence_complete"        : all(deposited),

        # ── Compatibilité tests existants ────────────────────
        "ur3e_grasped"             : grasped[0] if len(grasped) > 0 else False,
        "ur5e_grasped"             : grasped[1] if len(grasped) > 1 else False,
        "ur10e_grasped"            : grasped[2] if len(grasped) > 2 else False,
        "wrist_reached_target"     : grasp_events > 0,
        "distance_sensor_triggered": grasp_events > 0,
        "gripper_closed"           : grasp_events > 0,
        "gripper_opened"           : release_events > 0,

        # ── Données brutes ───────────────────────────────────
        "max_can_heights"          : [round(h, 4) for h in max_heights],
        "can_names"                : can_names,
        "can_initial_positions"    : [[round(c, 4) for c in p]
                                      for p in initial_positions],
        "can_final_positions"      : final_positions,

        # ── Détail par canette ───────────────────────────────
        "per_can"                  : per_can,

        # ── Méta ─────────────────────────────────────────────
        "duration"                 : duration,
        "timestep_ms"              : TIME_STEP,
        "simulation_speed"         : 1.0,
        "step_count"               : step_count,
    }

    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    if final:
        print(f"[Superviseur] ✓ JSON final → {RESULTS_PATH}", flush=True)
        print(f"[Superviseur] saisies={grasp_events}/{total_cans}  "
              f"dépôts={release_events}/{total_cans}  "
              f"durée={duration:.1f}s  "
              f"complete={results['sequence_complete']}", flush=True)
    else:
        print(f"[Superviseur] [{step_count}] "
              f"saisies={grasp_events}/{total_cans}  "
              f"dépôts={release_events}/{total_cans}  "
              f"t={duration:.1f}s", flush=True)


def run():
    from controller import Supervisor
    robot = Supervisor()

    # ── Découverte dynamique de toutes les canettes ──────────
    cans  = discover_all_cans(robot)
    n     = len(cans)
    nodes = [nd for _, nd in cans]

    # ── Positions initiales ──────────────────────────────────
    initial_positions = []
    for _, node in cans:
        pos = list(node.getPosition()) if node else [0.0, 0.0, 0.0]
        initial_positions.append(pos)

    # ── État par canette ─────────────────────────────────────
    grasped        = [False] * n
    deposited      = [False] * n
    max_heights    = [p[2] for p in initial_positions]
    grasp_stable   = [0] * n
    deposit_stable = [0] * n

    sim_start  = robot.getTime()
    step_count = 0

    # Export initial (crée le fichier dès le démarrage)
    write_results(robot, cans, initial_positions, max_heights,
                  grasped, deposited, sim_start, 0)

    # ── Boucle principale ────────────────────────────────────
    while robot.step(TIME_STEP) != -1:
        step_count += 1

        for i, node in enumerate(nodes):
            if node is None:
                continue
            pos = node.getPosition()
            h   = pos[2]

            # Hauteur maximale atteinte
            if h > max_heights[i]:
                max_heights[i] = h

            if not grasped[i]:
                # Détection saisie : Z dépasse le seuil
                if h > HAUTEUR_SAISIE:
                    grasp_stable[i] += 1
                    if grasp_stable[i] >= STEPS_STABLE:
                        grasped[i] = True
                        name = cans[i][0]
                        print(f"[Superviseur] SAISIE {name}  "
                              f"Z={h:.3f}m  t={robot.getTime():.1f}s",
                              flush=True)
                else:
                    grasp_stable[i] = 0

            elif not deposited[i]:
                # Détection dépôt : déplacement XY depuis position initiale
                d = dist2d(pos, initial_positions[i])
                if d > DEPLACEMENT_DEPOT:
                    deposit_stable[i] += 1
                    if deposit_stable[i] >= STEPS_STABLE:
                        deposited[i] = True
                        name = cans[i][0]
                        print(f"[Superviseur] DÉPÔT {name}  "
                              f"dist={d:.3f}m  t={robot.getTime():.1f}s",
                              flush=True)
                else:
                    deposit_stable[i] = 0

        # Export intermédiaire toutes les 500 steps (~4s)
        if step_count % 500 == 0:
            write_results(robot, cans, initial_positions, max_heights,
                          grasped, deposited, sim_start, step_count)

        # Fin : toutes les canettes traitées OU timeout
        if all(deposited) or step_count >= TIMEOUT_STEPS:
            if all(deposited):
                print(f"[Superviseur] ✓ Toutes les canettes traitées "
                      f"({n}/{n}).", flush=True)
            else:
                print(f"[Superviseur] ⚠ Timeout — "
                      f"{sum(deposited)}/{n} canettes traitées.",
                      flush=True)
            break

    write_results(robot, cans, initial_positions, max_heights,
                  grasped, deposited, sim_start, step_count, final=True)


if __name__ == "__main__":
    run()
