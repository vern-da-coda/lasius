# Lasius Software Backlog & Biomimetische Architektur-Roadmap

---

[Project Index](../README.md) | [Software Documentation](README.md) | [Roadmap](../docs/roadmap.md) | [lasius-core](lasius-core/README.md) | [lasius-dashboard](lasius-dashboard/README.md) | [lasius-pilot](lasius-pilot/README.md)

---

Dieses Dokument enthält das Software-Backlog sowie die architektonischen Leitlinien für die Weiterentwicklung des Hexapod:Lasius Steuerungs-Stacks (`lasius-core`, `lasius-pilot`, `lasius-dashboard`).

Im Fokus steht die **biomimetische Übertragung von Insekten-Steuerungsprinzipien** (dezentrale Ganglien, Subsumption-Architektur, lokale Reflexschleifen) auf die Software.

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
