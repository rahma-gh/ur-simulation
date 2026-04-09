FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV WEBOTS_HOME=/usr/local/webots
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

RUN apt-get update && apt-get install -y \
    wget python3 python3-pip xvfb gcc make build-essential \
    libgl1 libegl1 libxkbcommon0 libdbus-1-3 \
    libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 \
    libxcb-render-util0 libxcb-xinerama0 gnupg software-properties-common \
    && rm -rf /var/lib/apt/lists/*

RUN wget -qO- https://cyberbotics.com/Cyberbotics.asc | apt-key add - && \
    apt-add-repository 'deb https://cyberbotics.com/debian/ binary-amd64/' && \
    apt-get update && apt-get install -y webots && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest pytest-html numpy

COPY . /app
WORKDIR /app

RUN mkdir -p reports && \
    echo "=== Compilation ure_can_grasper ===" > reports/build.log && \
    cd /app/controllers/ure_can_grasper && \
    gcc ure_can_grasper.c \
        -I${WEBOTS_HOME}/include/controller/c \
        -L${WEBOTS_HOME}/lib/controller \
        -lController \
        -Wl,-rpath,${WEBOTS_HOME}/lib/controller \
        -o ure_can_grasper 2>> /app/reports/build.log && \
    echo "COMPILATION OK" >> /app/reports/build.log && \
    ls -lh ure_can_grasper >> /app/reports/build.log || \
    echo "COMPILATION ECHOUEE" >> /app/reports/build.log

ENV PYTHONPATH=${WEBOTS_HOME}/lib/controller/python
ENV LD_LIBRARY_PATH=${WEBOTS_HOME}/lib/controller
ENV DISPLAY=:99
ENV WEBOTS_DISABLE_SAVE_SCREEN_PERSPECTIVE_ON_CLOSE=1

CMD ["bash", "-c", "\
    export DISPLAY=:99 && \
    Xvfb :99 -screen 0 1280x1024x24 -ac +extension GLX +render -noreset & \
    sleep 3 && \
    echo '=== BUILD LOG ===' && cat /app/reports/build.log && \
    echo '' && \
    echo '===========================================' && \
    echo ' Lancement Webots (mode fast + batch)...' && \
    echo '===========================================' && \
    webots --mode=fast --batch --no-rendering worlds/ure.wbt \
        1>/app/reports/webots_stdout.log \
        2>/app/reports/webots_stderr.log & \
    WEBOTS_PID=$! && \
    echo \" Webots PID=$WEBOTS_PID\" && \
    echo ' Attente du JSON de résultats (superviseur)...' && \
    WAITED=0 && \
    while [ $WAITED -lt 270 ]; do \
        sleep 5; \
        WAITED=$((WAITED + 5)); \
        if [ -f /app/reports/simulation_results.json ]; then \
            TOTAL=$(python3 -c \"import json; d=json.load(open('/app/reports/simulation_results.json')); print(d.get('total_cans',0))\" 2>/dev/null); \
            GRASPS=$(python3 -c \"import json; d=json.load(open('/app/reports/simulation_results.json')); print(d.get('grasp_events',0))\" 2>/dev/null); \
            DONE=$(python3 -c \"import json; d=json.load(open('/app/reports/simulation_results.json')); print(d.get('sequence_complete',False))\" 2>/dev/null); \
            echo \" [${WAITED}s] total_cans=${TOTAL}  grasp_events=${GRASPS}  sequence_complete=${DONE}\"; \
            if [ \"$DONE\" = \"True\" ]; then \
                echo ' Toutes les canettes traitées !'; \
                break; \
            fi; \
        else \
            echo \" [${WAITED}s] JSON pas encore créé...\"; \
        fi; \
        if ! kill -0 $WEBOTS_PID 2>/dev/null; then \
            echo ' Webots process terminé.'; \
            break; \
        fi; \
    done && \
    kill $WEBOTS_PID 2>/dev/null || true && \
    sleep 2 && \
    echo '' && \
    echo '=== WEBOTS STDOUT ===' && \
    tail -30 /app/reports/webots_stdout.log 2>/dev/null || echo '(vide)' && \
    echo '=== WEBOTS STDERR ===' && \
    tail -20 /app/reports/webots_stderr.log 2>/dev/null || echo '(vide)' && \
    echo '' && \
    echo '===========================================' && \
    echo ' Lancement pytest...' && \
    echo '===========================================' && \
    pytest tests/ -v --html=reports/report.html || true \
"]
