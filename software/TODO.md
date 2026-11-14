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
- [ ] **Semi-autonome Bein-Controller (`LegController` / Ganglion-Klasse):**  
  * Kapselung jedes Beins in eine eigene Zustandsmaschine mit lokalen Phasen:
    * `STANCE` (Stützphase / Kraftübertragung auf den Boden)
    * `SWING` (Schwingphase / Vorholen des Beins)
    * `SEARCH` (Suchbewegung nach festem Bodenkontakt)
    * `RECOVERY` (Ausweich-/Hebereflex bei Kollision)
- [ ] **Lokale Koordinationsregeln (Cruse-Regeln 1–6):**  
  * *Regel 1 (Inhibierung):* Ein Bein beginnt die Schwingphase erst, wenn das davor liegende Bein sicheren Bodenkontakt hat.
  * *Regel 2 (Erleichterung):* Setzt ein vorderes Bein auf, regt dies das nachfolgende Bein zum Abheben an (metachrone Welle / Wave Gait bei langsamer Gangart).
  * *Regel 3 (Positionstransfer):* Der Aufsetzpunkt eines Vorderbeins dient dem Folgebein als sicherer Ziel-Trittpunkt.
  * *Regel 4 (Lastverteilung):* Höhere Gegenkraft an einem Stützbein verzögert das Abheben anderer Beine (automatische Stabilitätsreserve).

---

### AP 2: Lokale sensorische Reflexschleifen (Closed-Loop Telemetrie)
- [ ] **Elevator-Reflex (Hindernis-Ausweichreflex in der Schwingphase):**  
  * *Trigger:* Unerwarteter Widerstand an Tibia oder Femur während `SWING` (Erkennung über Schleppfehler zwischen Soll-PWM und ADC-Potentiometerwert am ADS1115).
  * *Reaktion:* Sofortiger lokaler Abbruch der Vorwärtsbewegung, Anheben des Kniegelenks (Femur hoch) um $15\text{--}25\,\text{mm}$ und erneutes Vorschwingen über das Hindernis hinweg.
- [ ] **Searching Reflex (Bodensuch-Reflex in der Landephase):**  
  * *Trigger:* Erreichen der Soll-Touchdown-Position ohne geschlossenen Fuß-Mikroschalter (oder ohne sprunghaften Kraftanstieg).
  * *Reaktion:* Verlängerung der Landephase nach unten ($Z$-Richtung) mit verringerter Geschwindigkeit, bis fester Kontakt gemeldet wird oder der maximale mechanische Hub erreicht ist.
- [ ] **Stance-Load Balancing (Aktive Lastanpassung):**  
  * Drehmoment-Unterstützung an unebenen Kanten basierend auf Rückmeldung der analogen Servopotentiometer.

---

### AP 3: Kognitive Entkopplung der oberen Ebene (High-Level Intentions)
- [ ] **Subsumption- / Behavior-Tree-Schicht über `OrderDispatcher`:**  
  * Die oberste Steuerebene (KI, Autonomie oder Gamepad-Pilot) sendet ausschließlich High-Level-Intentionen:
    * `LOCOMOTE(direction, speed)`
    * `CLIMB_STEP(obstacle_height)`
    * `CROUCH_SCAN(terrain)`
    * `REST_LOW_POWER()`
  * Alle Details (Kinematik, Fußkoordinaten, Bodenanpassung, Reflexe) werden vollständig von den darunterliegenden Schichten absorbiert.
- [ ] **Terrain-Adaptive Fahrwerkhöhe:**  
  * Automatische Koppelung des 9-Feld ToF-Bodensensors (Unterboden-Matrix) mit der Soll-Bodenfreiheit (`ground_clearance`): Erkennt der Bauchsensor ein Hindernis unter dem Rumpf, hebt die Ganglien-Ebene das Chassis automatisch an, ohne dass der Pilot eingreifen muss.

---

### AP 4: Simulations- & Verifikationsumgebung
- [ ] **MuJoCo / PyBullet Rigid-Body-Physikmodell:**  
  * Physikalischer Test der dezentralen Cruse-Regeln und Reflexe in einer unebenen 3D-Simulationsumgebung (Hindernisse, Treppenstufen, Schotter), bevor der Code auf dem physikalischen Roboter aktiviert wird.

---

### AP 5: Dashboard & Closed-Loop-Visualisierung (`lasius-dashboard`)
- [ ] **Ist- und Soll-Position direkt im Servo-Slider visualisieren ([`JointCard.vue`](lasius-dashboard/src/components/sidebar/JointCard.vue)):**  
  * **Ausgangslage:** Der *Live Angle*-Slider (`#slider-joint-${jointType}`) und das Wert-Badge (`#val-joint-${jointType}`) stellen aktuell ausschließlich `store.jointAngles` ([`dashboardStore.ts`](lasius-dashboard/src/stores/dashboardStore.ts)) dar – also die angeforderte **Soll-Position** (`setJointAngle` bzw. berechnete Zielwinkel aus `lasius-core` oder der Browser-Simulation).
  * **Ziel im UI (`JointCard.vue`):**
    * **Soll-Position:** Bleibt über den interaktiven Slider-Regler (Thumb) vorgebbar und eindeutig als Zielwinkel ablesbar.
    * **Ist-Position:** Zusätzlicher visueller Indikator direkt auf dem Slider-Track (analog zum überlagerten Track-/Overlay-Aufbau beim Trim- und Dual-Range-Slider in [`JointCard.vue`](lasius-dashboard/src/components/sidebar/JointCard.vue)), der den tatsächlich gemessenen Gelenkwinkel innerhalb `[minLimit, maxLimit]` anzeigt.
    * **Soll-/Ist-Vergleich:** Beide Werte (Soll und Ist in `°`) sowie die Abweichung / der Schleppfehler (z. B. farbliche Markierung bei mechanischer Blockade oder Nachlauf) klar ersichtlich darstellen; sauberer Fallback (gedimmter/ausgeblendeter Indikator), solange für ein Gelenk noch kein reales Poti-Feedback vorliegt (Open-Loop).
  * **Datenfluss & Telemetrie (`lasius-core` → `lasius-dashboard`):**
    * WebSocket-Telemetrie in [`app.py`](lasius-core/src/lasius/core/server/app.py) sauber zwischen Soll- und Ist-Winkeln trennen (z. B. separates Feld `actual_angles` neben `angles`), gespeist aus der kalibrierten **Multiplexer + Wandler**-Rückmeldung (siehe [`hardware/electronics/TODO.md`](../hardware/electronics/TODO.md), AP 4).
    * Reaktiven State (z. B. `actualJointAngles`) und Typdefinitionen ([`types/index.ts`](lasius-dashboard/src/types/index.ts)) in `lasius-dashboard` ergänzen sowie optional ein träges/physikalisches Folgeverhalten für den Demo-/Simulationsmodus (`useDemoSimulation.ts`) vorsehen.

---

### AP 6: Ist-Wert-Verarbeitung & Closed-Loop-Pipeline (`lasius-core`)
- [ ] **Akquisition, Trennung & Kalibrierung von Soll- und Ist-Winkeln ([`servo.py`](lasius-core/src/lasius/core/hardware/servo.py), [`driver.py`](lasius-core/src/lasius/core/hardware/driver.py), [`robot.py`](lasius-core/src/lasius/core/robot.py)):**  
  * **Soll vs. Ist sauber trennen:** Neben `target_angle` (`Servo.current_angle` / `angles`) einen eigenen `measured_angle` + `actual_valid`-Status führen (Hardware-Basis: **Multiplexer + Wandler**, siehe [`hardware/electronics/TODO.md`](../hardware/electronics/TODO.md) AP 4).
  * **Start-Validität („Vor dem 1. PWM-Puls“) abfangen:** Reely NR-645 MG BB liefert vor dem ersten gültigen 50-Hz-PWM-Impuls noch keine belastbare Poti-Spannung (Testbench-Befund: `0,2660 V` vor Puls vs. stabiler Wert auch nach `relax()`); Werte außerhalb des Plausibilitätsfensters (z. B. `< 0,5 V`) explizit als `invalid/uninitialized` behandeln.
  * **Pro-Servo-Regression & Rauschfilter:** Individuelle `slope`- / `V0`-Werte pro Servo laden (`V280` 12-Bit `2,0 mV ≈ 0,26°`, Standrauschen `~1 mV`) und Messwerte leicht glätten.
  * **Shared I²C Bus-Lock & Non-Blocking Polling:** Den bestehenden `_BUS_LOCKS` in [`driver.py`](lasius-core/src/lasius/core/hardware/driver.py) für **Multiplexer (`0x71`) + Wandler (`0x48`)** mitbenutzen und Sensor-Abfragen entkoppelt/gestaffelt planen, damit die `50 Hz`-PWM-Ausgabe in `Hexapod.tick()` niemals blockiert.
- [ ] **Mathematisches Vergleichsmodell (kein naiver äußerer PID!):**  
  * **Regelgrenze einhalten:** Keine schnelle äußere Winkel-PID-Schleife auf die Soll-PWM aufschlagen, da jedes Servo bereits eine schnelle interne Analogregelung besitzt (Gefahr von Aufschwingen/Jitter).
  * **Dynamischer Schleppfehler (`Soll(t − τ)` vs. `Ist(t)`):** Zeitversatz / Geschwindigkeitsmodell $\tau$ berücksichtigen, damit normale Motorträgheit während schneller Bewegungen (Testbench: bis `~99,5 mV` im Vollsweep) keinen Falsch-Alarm auslöst.
- [ ] **Konkrete Nutzung des Ist-Werts im Steuerungs-Stack:**  
  * **1. Vorwärtskinematik & Telemetrie:** `calculate_leg_fk` in [`kinematics.py`](lasius-core/src/lasius/core/motion/kinematics.py) aus Ist-Winkeln berechnen (reale Fußposition für **AP 5** / Dashboard & Diagnostik).
  * **2. Stall- & Kollisionsschutz:** Dauerhaft hoher Schleppfehler außerhalb des Bewegungsfensters meldet mechanische Blockade/Anschlag → kontrolliertes Bremsen/`relax` bzw. Schutzreaktion.
  * **3. Biomimetische Reflexe & Lastschätzung (`AP 1` & `AP 2`):** Femur-/Tibia-Abweichung kombiniert mit Fußschalter `A3` als Trigger für *Elevator-Reflex*, *Searching Reflex* und *Cruse*-Lastverteilung.
  * **4. Sanfter Wiederanlauf & langsame Sag-Kompensation:** Bei bekanntem Ist-Wert (nach `relax()`) weiches Anfahren ohne Ruck; optional stark gedämpfte, eng begrenzte statische Lastkompensation nur in `STANCE`.
  * **5. Sim-to-Real / Residual RL ([`gym_env.py`](lasius-core/src/lasius/core/sim/gym_env.py)):** Reale Ist-Winkel ($\theta$) und abgeleitete Winkelgeschwindigkeiten ($\dot{\theta}$) für den 66-dim Observation-Space nutzbar machen.
