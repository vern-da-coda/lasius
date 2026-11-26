# Lasius Software Backlog & Biomimetische Architektur-Roadmap

---

[Project Index](../README.md) | [Software Documentation](README.md) | [Roadmap](../docs/roadmap.md) | [lasius-core](lasius-core/README.md) | [lasius-dashboard](lasius-dashboard/README.md) | [lasius-pilot](lasius-pilot/README.md)

---

Dieses Dokument enthält das Software-Backlog sowie die architektonischen Leitlinien für die Weiterentwicklung des Hexapod:Lasius Steuerungs-Stacks (`lasius-core`, `lasius-pilot`, `lasius-dashboard`).

Im Fokus steht die **biomimetische Übertragung von Insekten-Steuerungsprinzipien** (dezentrale Ganglien, Subsumption-Architektur, lokale Reflexschleifen) auf die Software.

> [!IMPORTANT]
> **Aktueller Hardware-Fokus (Testbench `bkhexapod` & Ausbau):**
> * **Verifiziert (Stufe 1–3):** Hauptbus Daisy-Chain (`Pi 4 → Controller [0x40] → Multiplexer [0x71]`), erster **Wandler** (`ADS1115 V280`, `0x48` auf `CH0/LF`, `SCL` vor `SDA`, linksbündig 12-Bit / `2,0 mV`) sowie erster Closed-Loop-Sweep (`R² = 0,999876`, `+7,530 mV/°`).
> * **Nächste Schritte:** Zentrale `3,3 V / GND`-Verteilerschiene & vollständiges Testbein `LF` (`A0–A3` inkl. Fußschalter) gemäß [`hardware/electronics/TODO.md`](../hardware/electronics/TODO.md), danach Dashboard-Slider-Indikator (**AP 5**) und `lasius-core` Ist-Wert-Pipeline (**AP 6**).
> * **Detaillierter Status & Leitfaden:** [`docs/hardware/testbench_bringup_status.md`](../docs/hardware/testbench_bringup_status.md)
> * **Diagnose-Tool:** `python3 scripts/bench/test_electronics.py --scan`

---

## 1. Biomimetisches Leitprinzip: Insekten-Neurologie

> [!NOTE]
> **Biologisches Vorbild (*Lasius niger* / Stabheuschrecken / *Walknet*):**  
> Insekten verfügen über kein großes, rechenstarkes Gehirn, das zu jedem Zeitpunkt die Gelenkwinkel aller 18 Gelenke analytisch im Voraus berechnet. Stattdessen basiert ihre Fortbewegung auf einer **strikten hierarchischen und dezentralen Dekomposition**:
> 1. **Kopfhirn (Supraösophageales Ganglion):** Gibt lediglich übergeordnete Absichten (*Intentions / Locomotion Goals*) vor (z. B. *"Vorwärts mit Geschwindigkeit $v$ in Richtung $\phi$"*, *"Drehen"*, *"Ausweichen"*, *"Anhalten"*). Das Gehirn kennt keine Gelenkwinkel.
> 2. **Thorakale Ganglien (Lokale Bein-Zentren / CPGs):** Jedes Bein besitzt ein eigenes, semi-autonomes Nervenzentrum (Central Pattern Generator / Bein-Controller). Die Beine koordinieren sich horizontal über lokale Nachbarschaftsregeln (Cruse-Regeln).
> 3. **Lokale Reflexschleifen (Sensorisch-motorische Rückkopplung):** Unmittelbare Reaktionen auf Hindernisse, Geländestufen und Bodenhaftung werden lokal im Bein geregelt, ohne das Gehirn zu belasten.

---

## 2. Ist-Analyse in `lasius-core` (Was ist bereits da?)

- [x] **Oberste Schnittstelle denkt bereits in Geh-Vektoren (nicht in Gelenkwinkeln):**  
  * **Status:** Die bestehende API (`/api/v1/orders`), der `OrderDispatcher` und `lasius-pilot` (Gamepad) steuern den Roboter bereits primär über holonome Geschwindigkeitsvektoren (`SET_VELOCITY` mit $v_x, v_y, \omega_z$), Schrittweiten (`SET_WALK`), Rumpfhöhen (`SET_HEIGHT`) und Posen (`SET_ROLL`, `SET_PITCH`).
  * Einzelne Gelenkwinkel-Befehle (`SET_JOINT_ANGLE`) sind strikt auf isolierte Kalibrierungs- und Diagnose-Modi (`locomotion_active = False`) beschränkt.
- [x] **Entkoppelte 4-Schichten-Architektur:**  
  * Hardware Abstraction Layer (HAL) $\rightarrow$ Motion & Kinematik $\rightarrow$ Order-Pipeline/Arbitrierung $\rightarrow$ Server & Telemetrie.
- [x] **Analytische 3-DOF Inverse Kinematik (IK):**  
  * Fußkoordinaten im Raum $(x, y, z)$ werden exakt geschlossen-trigonometrisch in Winkel $(\theta_{\text{coxa}}, \theta_{\text{femur}}, \theta_{\text{tibia}})$ aufgelöst.

### Identifizierte Gaps zum biologischen Vorbild:
1. **Zentrale statt dezentrale Taktung:**  
   Die aktuelle `OmniGait`-Engine (`gait.py`) generiert Schritte noch über eine **zentrale mathematische Phasenfunktion** (globaler Cosinus-Generator für alle 6 Beine gleichzeitig).
2. **Fehlende lokale Reflexe (Open-Loop Fußtrajektorien):**  
   Fällt ein Fuß ins Leere oder stößt er gegen ein Hindernis, fährt das Bein starr seine vorberechnete Raumkurve ab.
3. **Starres Gangart-Umschalten:**  
   Tripod-, Ripple- und Wave-Gaits sind feste Modi, statt dass sich die Gangart emergent aus der Fortbewegungsgeschwindigkeit und den Lastverhältnissen ergibt.

---

## 3. Software-Backlog: Biomimetische Architektur-Module

### AP 1: Dezentrale Ganglien-Architektur & Cruse-Kopplungsregeln (Walknet-Ansatz)
- [x] **Semi-autonome Bein-Controller (`LegGanglion` / `WalknetGait` in [`walknet.py`](lasius-core/src/lasius/core/motion/walknet.py)):**  
  * Kapselung jedes Beins in eine eigene Zustandsmaschine mit lokalen Phasen:
    * `STANCE` (Stützphase / Kraftübertragung auf den Boden)
    * `SWING` (Schwingphase / Vorholen des Beins)
    * `SEARCH` (Suchbewegung nach festem Bodenkontakt)
    * `RECOVERY` (Ausweich-/Hebereflex bei Kollision)
- [x] **Lokale Koordinationsregeln (Cruse-Regeln 1–4) & Support-Polygon-Invariante:**  
  * *Regel 1 (Inhibierung):* Ipsilaterales Nachbarbein inhibiert Abheben solange Vorgänger nicht trägt (`min_stance_legs >= 3`).
  * *Regel 2 (Erleichterung):* Aufsetzen des vorderen Nachbarn verschiebt die PEP-Schwelle nach vorn (emergente metachrone Welle / Ripple / Tripod je nach Geschwindigkeit).
  * *Regel 3 (Positionstransfer):* Folgebein blendet den AEP-Zielpunkt anteilig auf den realen Aufsetzpunkt des Vorderbeins.
  * *Regel 4 (Lastverteilung):* Hohe Last (`load_estimate`) an benachbarten Stützbeinen verzögert das Abheben.

---

### AP 2: Lokale sensorische Reflexschleifen (Closed-Loop Telemetrie)
- [x] **Elevator-Reflex (Hindernis-Ausweichreflex in der Schwingphase — [`walknet.py`](lasius-core/src/lasius/core/motion/walknet.py)):**  
  * *Trigger:* `is_stalled` oder Schleppfehler `|tracking_error_deg| >= 8,0°` während `SWING`.
  * *Reaktion:* Sofortiger Wechsel in `RECOVERY`, kurzes Zurückziehen und Anheben um `+22 mm` über das Hindernis.
- [x] **Searching Reflex (Bodensuch-Reflex in der Landephase — [`walknet.py`](lasius-core/src/lasius/core/motion/walknet.py)):**  
  * *Trigger:* Erreichen des Schwing-Endes ohne geschlossenen Fuß-Mikroschalter (`use_foot_switches=True`).
  * *Reaktion:* Sondierung in `-Z` (`65 mm/s` bis `max_search_z_mm = -122 mm`) bis Bodenkontakt erkannt und als lokales `stance_z` übernommen wird.
- [x] **Stance-Load Compliance (Aktive Lastanpassung):**  
  * Automatische Z-Nachgiebigkeit unter hoher Stützlast + sanfte Rückführung Richtung Nominalhöhe; in [`Hexapod.tick()`](lasius-core/src/lasius/core/robot.py) automatisch an die geschlossene Telemetrie gekoppelt.

---

### AP 3: Kognitive Entkopplung der oberen Ebene (High-Level Intentions)
- [ ] **Subsumption- / Behavior-Tree-Schicht über `OrderDispatcher`:**  
  * Die oberste Steuerebene (KI, Autonomie oder Gamepad-Pilot) sendet ausschließlich High-Level-Intentionen:
    * `LOCOMOTE(direction, speed)`
    * `CLIMB_STEP(obstacle_height)`
    * `CROUCH_SCAN(terrain)`
    * `REST_LOW_POWER()`
  * Alle Details (Kinematik, Fußkoordinaten, Bodenanpassung, Reflexe) werden vollständig von den darunterliegenden Schichten absorbiert.
- [x] **Terrain-Adaptive Fahrwerkhöhe (`set_belly_tof_distance_m()` in [`walknet.py`](lasius-core/src/lasius/core/motion/walknet.py) + [`SimulatedToFSensor`](lasius-core/src/lasius/core/hardware/sensors.py)):**  
  * Automatische Anhebung der Rumpf-Bodenfreiheit bei Hindernissen unterhalb des Bauch-ToF-Schwellwerts (`0,085 m`, bis `+30 mm` Boost) ohne Eingriff des Piloten.

---

### AP 4: Simulations- & Verifikationsumgebung
- [x] **PyBullet Rigid-Body-Physikmodell, Walknet-Sim & Pure-NumPy Sim-to-Real RL-Deployment:**  
  * Prozedurale unebene Terrains (`terrain.py`: rough/slopes/steps/mixed), realistische NR-645 Servodynamik (`actuator.py`), Walknet-Option in [`run_simulation.py`](../scripts/sim/run_simulation.py) (`--gait-engine walknet`) und leichtgewichtige Pure-NumPy-Inferenz ([`policy.py`](lasius-core/src/lasius/core/sim/policy.py), [`export_policy.py`](../scripts/sim/export_policy.py)) mit Adaptive Terrain Gate (`Δ = +6,2` über 7 Szenarien vs. analytischer Baseline).

---

### AP 5: Dashboard & Closed-Loop-Visualisierung (`lasius-dashboard`)
- [x] **Ist- und Soll-Position direkt im Servo-Slider visualisieren ([`JointCard.vue`](lasius-dashboard/src/components/sidebar/JointCard.vue)):**  
  * **Ausgangslage:** Der *Live Angle*-Slider (`#slider-joint-${jointType}`) und das Wert-Badge (`#val-joint-${jointType}`) stellten zuvor ausschließlich `store.jointAngles` ([`dashboardStore.ts`](lasius-dashboard/src/stores/dashboardStore.ts)) dar – also die angeforderte **Soll-Position** (`setJointAngle` bzw. berechnete Zielwinkel aus `lasius-core` oder der Browser-Simulation).
  * **Umsetzung im UI ([`JointCard.vue`](lasius-dashboard/src/components/sidebar/JointCard.vue) & [`style.css`](lasius-dashboard/src/styles/style.css)):**
    * **Soll-Position:** Bleibt über den interaktiven Slider-Regler (Thumb) vorgebbar und eindeutig als Zielwinkel (`#val-joint-${jointType}`) ablesbar.
    * **Ist-Position:** Überlagerter Track-Container (`.joint-slider-track-container`) mit pixelgenau auf die `15 px`-Thumb-Mitte ausgerichtetem Ist-Marker (`#marker-actual-${jointType}`) und dynamischem Differenzbalken (`#delta-bar-${jointType}`) zwischen Soll- und Ist-Winkel innerhalb `[minLimit, maxLimit]`.
    * **Soll-/Ist-Vergleich & Open-Loop-Fallback:** Gleichzeitige Badges für Soll (`#val-joint-${jointType}`), Ist (`#val-actual-${jointType}`) und Schleppfehler/Abweichung (`#val-delta-${jointType}`, inkl. gelber Warnstufe ab `|Δ| >= 5°` und pulsierendem `⚠ STALL`-Alarm bei Blockade); automatischer Fallback auf gedimmtes `Open-Loop`-Badge und ausgeblendeten Track-Marker, solange `actual_valid == false` ist.
  * **Datenfluss & Telemetrie (`lasius-core` → `lasius-dashboard`):**
    * WebSocket-Broadcast `{"type": "telemetry", "data": ...}` in [`app.py`](lasius-core/src/lasius/core/server/app.py) sowie REST-Endpunkt `GET /api/v1/telemetry` in [`handlers.py`](lasius-core/src/lasius/core/server/handlers.py).
    * Reaktiver Closed-Loop-State (`actualJointAngles`, `actualJointValid`, `jointTrackingErrors`, `jointStalled`, `footContacts`) in [`dashboardStore.ts`](lasius-dashboard/src/stores/dashboardStore.ts) & [`types/index.ts`](lasius-dashboard/src/types/index.ts) sowie physikalischer Verzögerungs-Follower 1. Ordnung ($\tau = 75\,\text{ms}$, $\omega_{\max} = 350^\circ/\text{s}$) im Browser-Demomodus ([`useDemoSimulation.ts`](lasius-dashboard/src/demo/useDemoSimulation.ts)).

---

### AP 6: Ist-Wert-Verarbeitung & Closed-Loop-Pipeline (`lasius-core`)
- [x] **Akquisition, Trennung & Kalibrierung von Soll- und Ist-Winkeln ([`adc.py`](lasius-core/src/lasius/core/hardware/adc.py), [`servo.py`](lasius-core/src/lasius/core/hardware/servo.py), [`robot.py`](lasius-core/src/lasius/core/robot.py)):**  
  * **Soll vs. Ist sauber getrennt:** Neben `current_angle` (`target_angle`) führt [`Servo`](lasius-core/src/lasius/core/hardware/servo.py) eigene Attribute `measured_angle`, `measured_voltage`, `actual_valid`, `expected_angle`, `tracking_error` und `is_stalled`.
  * **Start-Validität („Vor dem 1. PWM-Puls“) abgefangen:** Spannungen außerhalb `[pot_v_min_valid, pot_v_max_valid]` (Standard `[0.50 V, 3.10 V]`, inkl. des empirischen Reely-NR-645-Ruhewerts `0.2660 V` vor dem 1. gültigen 50-Hz-PWM-Impuls) werden strikt als `actual_valid = False` / `measured_angle = None` verworfen.
  * **Pro-Servo-Regression & Rauschfilter:** Lineare Kalibrierung (`pot_v_zero = 1.5633 V`, `pot_v_slope = 0.007589 V/°` in [`config.py`](lasius-core/src/lasius/core/config.py) & [`config.yaml`](lasius-core/src/lasius/core/config.yaml), überschreibbar via `calibration.json`-Overlay) unter Berücksichtigung von `orientation` (`+1/-1`) und `center_offset_pulse` sowie EMA-Glättung (`ema_alpha = 0.45`).
  * **Shared I²C Bus-Lock & Non-Blocking Polling:** [`RealADS1115MuxDriver`](lasius-core/src/lasius/core/hardware/adc.py) nutzt denselben `_BUS_LOCKS[id(bus)]` (`threading.RLock`) wie `RealPCA9685Driver`, gibt den Lock während der `~1.4 ms` langen 860-SPS-Wandlungszeit frei und pollt in einem entkoppelten Hintergrund-Thread (`ClosedLoopTelemetryWorker`), sodass der 50-Hz-PWM-Takt niemals blockiert. Enthält [`SimulatedADCDriver`](lasius-core/src/lasius/core/hardware/adc.py) für Offline-Tests und Simulation.
- [x] **Mathematisches Vergleichsmodell (kein naiver äußerer PID!):**  
  * **Regelgrenze eingehalten:** Keine äußere Winkel-PID-Schleife auf die Soll-PWM.
  * **Dynamischer Schleppfehler (`Soll(t − τ)` vs. `Ist(t)`):** Ratenbegrenztes Verzögerungsmodell 1. Ordnung (`tau_lag_s = 0.075 s`, `max_speed_deg_s = 350.0 °/s`) berechnet `expected_angle(t)`, sodass normaler Nachlauf bei schnellen Sweeps (`~13°`) keinen Falsch-Alarm auslöst, während reale Blockaden (`|measured_angle - expected_angle| >= 8.0°` für `>= 0.35 s`) zuverlässig `is_stalled = True` setzen.
- [x] **Konkrete Nutzung des Ist-Werts im Steuerungs-Stack:**  
  * **1. Vorwärtskinematik & Telemetrie:** [`calculate_leg_fk`](lasius-core/src/lasius/core/motion/kinematics.py) und [`Leg.get_actual_tip_position()`](lasius-core/src/lasius/core/motion/leg.py) berechnen die reale 3D-Fußspitzenposition `(x, y, z)` aus den gemessenen Ist-Winkeln (`Hexapod.get_actual_foot_positions()`).
  * **2. Stall- & Kollisionsschutz:** Persistente Schleppfehler-Überwachung (`is_stalled`) pro Gelenk + Fußkontakt-Auswertung auf ADS1115-Kanal `A3` (`foot_contacts`).
  * **3. Sanfter Wiederanlauf nach `relax()`:** [`Servo.get_effective_start_angle()`](lasius-core/src/lasius/core/hardware/servo.py) startet Kosinus-Rampen in [`OrderDispatcher`](lasius-core/src/lasius/core/control/dispatcher.py) (`test_leg`, `stance_leg`, `sweep_joint`, `wave_hello`) ruckfrei direkt am aktuell gemessenen Poti-Ist-Winkel.
  * **4. Vorbereitet für AP 1–3 & Sim-to-Real:** Ist-Winkel, Schleppfehler und `A3`-Fußkontakt stehen über `Hexapod.poll_telemetry()` / `get_telemetry_state()` für die dezentralen Cruse-Reflexe (`AP 1`/`AP 2`) und den RL-Observation-Space (`AP 3`) bereit.
