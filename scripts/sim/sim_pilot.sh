#!/usr/bin/env bash
# ==============================================================================
# Module: scripts/sim/sim_pilot.sh
# Purpose & Role:
#   Orchestration script for Lasius Hexapod 3D Physics Simulation (PyBullet)
#   and real-time Gamepad Teleoperation (lasius-pilot).
#
#   Launches the PyBullet physics digital twin with embedded WebSocket server,
#   verifies socket readiness, and attaches the local teleoperation client
#   configured with Sony PlayStation 5 DualSense profile (or Stadia / Xbox).
#   Ensures clean lifecycle management and single-signal (Ctrl+C) teardown.
# ==============================================================================
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

# ------------------------------------------------------------------------------
# Configuration & Defaults
# ------------------------------------------------------------------------------
PROFILE="ps5"
JOYSTICK_DEV="/dev/input/js0"
WS_PORT=8765
SIM_ONLY=0
START_WALK=""

usage() {
    cat << 'EOF'
Verwendung: ./scripts/sim/sim_pilot.sh [OPTIONEN]

Orchestriert die PyBullet 3D-Physiksimulation und das Lasius-Pilot Gamepad-Teleoperations-Tool.

Optionen:
  -p, --profile <name>     Gamepad-Profil (Standard: ps5; Auswahl: ps5, stadia, xbox, auto)
  -d, --device <dev>       Linux Joystick Device (Standard: /dev/input/js0)
  --port <port>            WebSocket-Port (Standard: 8765)
  -w, --walk               Startet die Simulation mit sofort aktivem Gehzyklus
  --sim-only               Startet nur die 3D-Simulation ohne lasius-pilot
  -h, --help               Zeigt diese Hilfe an

Gamepad-Steuerung (PS5 DualSense via USB-C):
  Linker Stick             Omnidirektionale Bewegung (Vor/Zurück, Seitwärts)
  Rechter Stick            Gier-Drehung (Turn Left/Right)
  Kreuz (X)                Tripod-Gangart (schnell, 3 Beine gleichzeitig)
  Viereck ([])             Ripple-Gangart (stabil, 2 Beine gleichzeitig)
  Dreieck (/\)             Wave-Gangart (kriechend, 1 Bein gleichzeitig)
  Kreis (O) / PS-Taste     Sofortiger Not-Aus (E-Stop)
  L1 / R1                  Schrittgeschwindigkeit -0.25x / +0.25x
  D-Pad Oben/Unten         Bodenfreiheit (Chassis-Höhe) +/- 5 mm

Tastatursteuerung im 3D-PyBullet-Fenster:
  Pfeiltasten              Vorwärts / Rückwärts / Seitwärts
  R / T                    Gier-Drehung Links / Rechts
  Leertaste                Stopp
  W                        Gangart durchschalten (Tripod -> Wave -> Ripple)
EOF
    exit 0
}

# ------------------------------------------------------------------------------
# CLI Arguments Parsing
# ------------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        -p|--profile)
            PROFILE="$2"
            shift 2
            ;;
        -d|--device)
            JOYSTICK_DEV="$2"
            shift 2
            ;;
        --port)
            WS_PORT="$2"
            shift 2
            ;;
        -w|--walk)
            START_WALK="--walk"
            shift
            ;;
        --sim-only)
            SIM_ONLY=1
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "❌ Unbekannte Option: $1"
            echo "Verwende './scripts/sim/sim_pilot.sh --help' für weitere Informationen."
            exit 1
            ;;
    esac
done

# ------------------------------------------------------------------------------
# Banner & Python Discovery
# ------------------------------------------------------------------------------
if [ -f "$ROOT_DIR/scripts/banner.txt" ]; then
    cat "$ROOT_DIR/scripts/banner.txt"
fi

if [ -x "$ROOT_DIR/.venv/bin/python3" ]; then
    PYTHON_CMD="$ROOT_DIR/.venv/bin/python3"
elif command -v uv >/dev/null 2>&1; then
    PYTHON_CMD="uv run python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
else
    echo "❌ Fehler: python3 nicht gefunden."
    exit 1
fi

echo "=========================================================="
echo "🤖 Lasius Hexapod: PyBullet Simulation & Teleoperation"
echo "=========================================================="
echo "Controller-Profil: $PROFILE"
echo "Joystick-Gerät:    $JOYSTICK_DEV"
echo "WebSocket-Stream:  ws://127.0.0.1:$WS_PORT"
echo "=========================================================="

# ------------------------------------------------------------------------------
# Gamepad Connection Check & Prompt
# ------------------------------------------------------------------------------
if [ "$SIM_ONLY" -eq 0 ] && [ ! -e "$JOYSTICK_DEV" ]; then
    echo ""
    echo "⚠️  Gamepad-Gerät '$JOYSTICK_DEV' wurde nicht gefunden!"
    echo "👉 Bitte verbinde deinen PS5 DualSense Controller per USB-C-Kabel mit dem Laptop."
    echo "   (Hinweis: Die USB-Verbindung überschreibt NICHT das PS5-Bluetooth-Binding.)"
    echo ""
    if [ -t 0 ]; then
        echo "Warte auf Controller-Anschluss (oder drücke ENTER für Simulation ohne Gamepad, Strg+C zum Abbrechen)..."
        while [ ! -e "$JOYSTICK_DEV" ]; do
            if read -t 1 -r; then
                echo "⏩ ENTER gedrückt. Starte Simulation ohne lasius-pilot..."
                SIM_ONLY=1
                break
            fi
        done
    else
        echo "⚠️ Nicht-interaktives Terminal: Starte Simulation im Standalone-Modus..."
        SIM_ONLY=1
    fi
fi

if [ -e "$JOYSTICK_DEV" ]; then
    echo "✔ Gamepad-Gerät erkannt unter $JOYSTICK_DEV"
fi

# ------------------------------------------------------------------------------
# Lifecycle & Signal Trapping
# ------------------------------------------------------------------------------
SIM_PID=""
PILOT_PID=""

cleanup() {
    trap - INT TERM EXIT
    echo ""
    echo "🛑 Fahre Lasius Simulation & Pilot herunter..."
    if [ -n "${PILOT_PID:-}" ] && kill -0 "$PILOT_PID" 2>/dev/null; then
        echo "  - Beende lasius-pilot (PID $PILOT_PID)..."
        kill -TERM "$PILOT_PID" 2>/dev/null || true
    fi
    if [ -n "${SIM_PID:-}" ] && kill -0 "$SIM_PID" 2>/dev/null; then
        echo "  - Beende PyBullet Simulation (PID $SIM_PID)..."
        kill -TERM "$SIM_PID" 2>/dev/null || true
    fi
    wait 2>/dev/null || true
    echo "✔ Alle Prozesse sauber beendet."
}
trap cleanup INT TERM EXIT

# ------------------------------------------------------------------------------
# 1. Start PyBullet Simulation in Background
# ------------------------------------------------------------------------------
echo ""
echo "🚀 Starte PyBullet 3D-Simulation mit WebSocket-Server..."
SIM_ARGS=(--gui --ws --ws-port "$WS_PORT")
if [ -n "$START_WALK" ]; then
    SIM_ARGS+=("$START_WALK")
fi

$PYTHON_CMD "$ROOT_DIR/scripts/sim/run_simulation.py" "${SIM_ARGS[@]}" &
SIM_PID=$!

# ------------------------------------------------------------------------------
# 2. Wait for WebSocket Server Readiness
# ------------------------------------------------------------------------------
echo "⏳ Warte auf Bereitstellung des WebSocket-Servers auf Port $WS_PORT..."
MAX_WAIT_SECONDS=15
WAIT_ITERATIONS=$((MAX_WAIT_SECONDS * 4))
COUNT=0
SERVER_READY=0

while [ $COUNT -lt $WAIT_ITERATIONS ]; do
    if ! kill -0 "$SIM_PID" 2>/dev/null; then
        echo "❌ Fehler: PyBullet Simulation wurde vorzeitig beendet."
        exit 1
    fi

    if $PYTHON_CMD -c "import socket; s = socket.socket(); s.connect(('127.0.0.1', $WS_PORT)); s.close()" 2>/dev/null; then
        SERVER_READY=1
        break
    fi

    sleep 0.25
    COUNT=$((COUNT + 1))
done

if [ $SERVER_READY -ne 1 ]; then
    echo "❌ Fehler: WebSocket-Server antwortet nicht nach $MAX_WAIT_SECONDS Sekunden."
    exit 1
fi
echo "✔ WebSocket-Server ist aktiv und empfangsbereit!"

# ------------------------------------------------------------------------------
# 3. Start lasius-pilot Teleoperation Client
# ------------------------------------------------------------------------------
if [ "$SIM_ONLY" -eq 0 ]; then
    echo ""
    echo "🎮 Starte lasius-pilot ($PROFILE auf $JOYSTICK_DEV)..."
    $PYTHON_CMD "$ROOT_DIR/software/lasius-pilot/cli.py" \
        --host "127.0.0.1" \
        --port "$WS_PORT" \
        --device "$JOYSTICK_DEV" \
        --profile "$PROFILE" &
    PILOT_PID=$!

    echo "=========================================================="
    echo "✨ Simulation und Teleoperation laufen aktiv!"
    echo "Drücke Strg+C (oder schließe das PyBullet-Fenster), um beide zu beenden."
    echo "=========================================================="

    # Wait until either PyBullet or lasius-pilot terminates
    wait -n "$SIM_PID" "$PILOT_PID" 2>/dev/null || true
else
    echo "=========================================================="
    echo "✨ Simulation läuft im Standalone-Modus!"
    echo "Steuerung über Tastatur im PyBullet-Fenster."
    echo "Drücke Strg+C (oder schließe das PyBullet-Fenster) zum Beenden."
    echo "=========================================================="
    wait "$SIM_PID" 2>/dev/null || true
fi
