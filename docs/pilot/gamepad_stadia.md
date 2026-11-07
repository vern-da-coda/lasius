# Lasius Hexapod – Google Stadia Controller & Code-Anpassungen

> **Stand:** Oktober 2026  
> **Betroffene Pakete:** `lasius-pilot`, `lasius-core`, `lasius-dashboard`

Dieses Dokument beschreibt die Einrichtung und Tastenbelegung des **Google Stadia Controllers** (`lasius-pilot`) sowie alle durchgeführten Architektur- und Code-Quality-Anpassungen im Monorepo.

---

## 1. Google Stadia Controller – Kopplung & Einrichtung

Der Google Stadia Controller kann sowohl per **USB-C-Kabel** als auch kabellos per **Bluetooth Low Energy (BLE)** am Raspberry Pi 4 oder an einer Linux-Workstation betrieben werden. Er wird unter Linux nativ als `/dev/input/js0` bereitgestellt.

### 1.1 Bluetooth-Kopplung auf dem Raspberry Pi (einmalig)

1. **BlueZ Userspace-HID aktivieren (wichtig für Stadia BLE unter Linux):**
   In `/etc/bluetooth/input.conf` sicherstellen, dass folgende Option gesetzt ist:
   ```ini
   UserspaceHID=true
   ```
   Danach den Bluetooth-Dienst neu starten:
   ```bash
   sudo systemctl restart bluetooth
   ```

2. **Pairing-Modus am Stadia Controller starten:**
   - Halte **`Y` + `Stadia-Taste`** gleichzeitig für **2 Sekunden** gedrückt, bis der Lichtring um die Stadia-Taste **orange blinkt**.

3. **In `bluetoothctl` verbinden:**
   ```bash
   bluetoothctl
   [bluetooth]# scan on
   # Warten bis "StadiaXXXX-..." angezeigt wird
   [bluetooth]# pair <MAC-ADRESSE>
   [bluetooth]# trust <MAC-ADRESSE>
   [bluetooth]# connect <MAC-ADRESSE>
   [bluetooth]# exit
   ```

4. **Prüfen, ob `/dev/input/js0` angelegt wurde:**
   ```bash
   ls -l /dev/input/js*
   cat /sys/class/input/js0/device/name
   ```

---

## 2. Tasten- & Achsenbelegung (`lasius-pilot`)

[`GamepadController`](lasius-pilot/src/lasius/pilot/gamepad.py) erkennt den Google Stadia Controller anhand von `/sys/class/input/js0/device/name` automatisch (`active_profile == "stadia"`) oder kann explizit mit `--profile stadia` gestartet werden.

### 2.1 Analog-Sticks & Steuerkreuz (D-Pad)

| Bedienelement | Linux-Achse (`/dev/input/js0`) | WebSocket-Befehl | Funktion am Lasius Hexapod |
| :--- | :---: | :--- | :--- |
| **Linker Stick (Links / Rechts)** | `Axis 0` (`ABS_X`) | `set_velocity` (`walk_x`) | **Seitwärts laufen (Strafe)** (`-1.0` Links .. `+1.0` Rechts) |
| **Linker Stick (Vor / Zurück)** | `Axis 1` (`ABS_Y`) | `set_velocity` (`walk_y`) | **Vorwärts / Rückwärts laufen** (`+1.0` Vor .. `-1.0` Zurück) |
| **Rechter Stick (Links / Rechts)** | `Axis 2` (`ABS_Z`) | `set_velocity` (`turn_z`) | **Auf der Stelle drehen (Yaw)** (`+1.0` Links .. `-1.0` Rechts; `Axis 3` vertikal wird ignoriert) |
| **D-Pad Oben / Unten** | `Axis 7` (`ABS_HAT0Y`) | `set_height` | **Körperhöhe stufenweise ändern** (`±5 mm` pro Druck, Bereich `-40 mm` bis `-120 mm`) |

### 2.2 Aktionstasten & Sicherheit

| Taste am Stadia Controller | Linux-Button | WebSocket-Befehl | Funktion am Lasius Hexapod |
| :--- | :---: | :--- | :--- |
| **Taste `A`** (Unten) | `Button 0` | `set_gait_type: "tripod"` | Wechsel auf **Tripod-Gait** (schnell, 3 Beine am Boden) |
| **Taste `X`** (Links) | `Button 2` | `set_gait_type: "ripple"` | Wechsel auf **Ripple-Gait** (flüssig, 4 Beine am Boden) |
| **Taste `Y`** (Oben) | `Button 3` | `set_gait_type: "wave"` | Wechsel auf **Wave-Gait** (maximale Kraft/Stabilität, 5 Beine am Boden) |
| **Taste `B`** (Rechts) | `Button 1` | `emergency_stop` | **⛔ EMERGENCY STOP** (sofortiger Stopp & alle 18 Servos stromlos) |
| **Stadia-Taste** (Zentrum) | `Button 8` | `emergency_stop` | **⛔ EMERGENCY STOP** (sofortiger Stopp & alle 18 Servos stromlos) |
| **Schultertaste `L1`** | `Button 4` | `set_speed` | **Geschwindigkeit verringern** (`-0.25x`, Minimum `0.25x`) |
| **Schultertaste `R1`** | `Button 5` | `set_speed` | **Geschwindigkeit erhöhen** (`+0.25x`, Maximum `3.00x`) |
| **Options-Taste (`...`)** | `Button 6` | `reset_pose` | **Körperpose zurücksetzen** (`-80 mm` Höhe, `0°` Roll, `0°` Pitch) |
| **Menü-Taste (`≡`)** | `Button 7` | `toggle_pause` | **Pause / Fortsetzen** umschalten |

### 2.3 Startbefehl

```bash
# Lokal auf dem Raspberry Pi:
python3 lasius-pilot/cli.py --profile stadia

# Von der Workstation über WLAN zum Raspberry Pi:
python3 lasius-pilot/cli.py --host 192.168.0.123 --port 8765 --profile stadia
```

---

## 3. Durchgeführte Code- & Architektur-Anpassungen

### 3.1 `lasius-core` (Backend, HAL, Kinematik & Server)
- **Verdrahtung von `OmniGait` & `locomotion_active`-Zustandsmaschine ([`run_server.py`](lasius-core/run_server.py), [`robot.py`](lasius-core/src/lasius/core/robot.py), [`dispatcher.py`](lasius-core/src/lasius/core/control/dispatcher.py), [`app.py`](lasius-core/src/lasius/core/server/app.py)):**
  - Beim Start des Server-Daemons wird `OmniGait` im entkoppelten Sicherheitszustand (`engage=False`, `walk_x=0.0`, `walk_y=0.0`, `turn_z=0.0`) initialisiert und `robot.relax_all()` ausgeführt, sodass beim Booten kein einziger Servo bestromt wird.
  - Lauf- und Pose-Befehle (`SET_VELOCITY`, `SET_WALK`, `SET_TURN`, `SET_POSE`, `SET_HEIGHT`, `SET_ROLL`, `SET_PITCH`, `RESET_POSE`, `RESUME`) synchronisieren `LasiusServer` und `OmniGait` und aktivieren die 50-Hz-Schleife (`locomotion_active = True`).
  - Einzelgelenk- und Einzelbein-Befehle (`SET_JOINT_ANGLE`, `SET_LEG_JOINTS`, `RELAX_LEG`, `RELAX_ALL`, `EMERGENCY_STOP`) sowie asynchrone Testsequenzen (`TEST_LEG`, `STANCE_LEG`, `SWEEP_JOINT`) setzen `locomotion_active = False`, damit Einzelbein-Kalibrierungen niemals vom Gait-Loop überschrieben werden.
- **I2C-Thread-Safety & `0x70`-Adressschutz ([`driver.py`](lasius-core/src/lasius/core/hardware/driver.py)):**
  - Alle `RealPCA9685Driver`-Instanzen auf demselben I2C-Bus teilen sich einen `threading.RLock`, um Race Conditions zwischen dem 50-Hz-Main-Loop und dem `OrderDispatcher`-Worker-Thread zu verhindern.
  - Das `_ALLCALL`-Bit (`0x70`) im `MODE1`-Register des PCA9685 wurde deaktiviert, um Adresskollisionen mit dem geplanten **Adafruit PCA9548 I2C-Multiplexer (`0x70`)** auszuschließen.
- **I2C-Board-2-Adresse (`0x42`) in [`check_hardware.py`](lasius-core/check_hardware.py):**
  - Ersetzt die veraltete hartcodierte Adresse `0x41` durch die dynamische Ermittlung aller `board_address`-Werte aus [`config.yaml`](lasius-core/src/lasius/core/config.yaml) (`0x40` und `0x42`).
- **Geometrie-Konfiguration statt Magic Numbers ([`config.py`](lasius-core/src/lasius/core/config.py), [`config.yaml`](lasius-core/src/lasius/core/config.yaml), [`dispatcher.py`](lasius-core/src/lasius/core/control/dispatcher.py), [`calibrate.py`](lasius-core/calibrate.py)):**
  - `DefaultStanceConfig` um `default_x: 160.0` erweitert; `OrderDispatcher` und `calibrate.py` lesen `default_x` und `ground_clearance` direkt aus `config.geometry.default_stance`.
- **Packaging & Bereinigung:**
  - CLI-Entry-Point `lasius-server` (`lasius.core.server.app:main`) implementiert.
  - Veraltetes Duplikat `servos.yaml` entfernt und `laisus-rest-control-api.http` in [`lasius-rest-control-api.http`](lasius-core/lasius-rest-control-api.http) umbenannt.

### 3.2 `lasius-dashboard` (Vue 3 + TypeScript + Three.js Digital Twin)
- **Zuverlässiger Stopp beim Loslassen der Tastatur ([`App.vue`](lasius-dashboard/src/App.vue)):**
  - `handleKeyUp` ruft beim Loslassen der letzten Bewegungstaste (`WASD`, `QE`, Pfeiltasten) sofort `store.dpadStop()` auf; Key-Repeat-Events (`e.repeat`) werden gefiltert.
- **50-Hz-WebGL-Speicheroptimierung ([`lasiusGraphics.ts`](lasius-dashboard/src/engine/lasiusGraphics.ts)):**
  - `updateFanGeometry()` aktualisiert bestehende `Float32BufferAttribute`-Arrays in-place (`needsUpdate = true`), statt 50× pro Sekunde neue GPU-Buffer zu allokieren.
  - `disposeObject3D()` gibt Geometrien und Materialien beim Szenen-Rebuild sauber frei.

### 3.3 `lasius-pilot` (Gamepad-Teleoperation)
- **Atomare Geschwindigkeitsübertragung & Stadia-Profil ([`gamepad.py`](lasius-pilot/src/lasius/pilot/gamepad.py), [`cli.py`](lasius-pilot/src/lasius/pilot/cli.py)):**
  - Nutzt `action: "set_velocity"` für atomare Updates von `walk_x`, `walk_y` und `turn_z` (behebt das Weiterdrehen beim Loslassen des rechten Sticks auf `0.0`).
  - Unterstützt das Achsen- und Button-Layout des Google Stadia Controllers (`Axis 2` für `turn_z` sowie Action-Buttons für E-Stop, Gait-Wechsel, Speed, Körperhöhe und Pose-Reset).
