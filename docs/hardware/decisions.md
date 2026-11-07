# Lasius Hexapod – Finale Hardware-, Sensorik- & CAD-Entscheidungen

> **Quelle:** *GitHub Lasius Project Assistance.pdf* (Konzept-, Elektronik- & Mechanik-Spezifikation)  
> **Stand:** Oktober 2026

Dieses Dokument fasst alle finalen Architekturentscheidungen aus der Projekt-Spezifikation für das Hardware-Upgrade, die Sensor-Integration (STEMMA QT / I2C) und die 3D-Druck-Neukonstruktion (PETG) zusammen.

---

## 1. Gesamtkonzept & Entwicklungs-Roadmap

1. **Modulare 6-Arm-Sensor-Plattform („Underbody Sensor Tray“):**
   - Alle Sensoren am Torso werden auf einer **einzigen, abnehmbaren Trägerplatte** unter der unteren Chassis-Platte zusammengefasst.
   - Im Zentrum sitzen Multiplexer (TCA9548A), IMU (BNO085), Stromsensoren (INA228), GPIO-Expander (MCP23017) und die 6 ADS1115 Bein-ADC-Module; vorn der ToF-Distanzsensor.
   - **Vorteil:** Komplette Vorverdrahtung außerhalb des Roboters am Schreibtisch; bei Wartung über einen einzigen zentralen I2C-Uplink vom Raspberry Pi 4 trennbar.
2. **Entkopplung durch ein „Single-Leg Docking Test-Rig“:**
   - Ein 3D-gedruckter **Einzelbein-Prüfstand (Docking-Station)** nimmt exakt *ein* Bein samt zugehörigem ADS1115-Modul, INA228 und Fußtaster auf und kann direkt an den I2C-Multiplexer des Roboters oder einen Test-Pi angedockt werden.
   - Damit lassen sich **CAD-Passform, Poti-Kalibrierung, Tibia-Federung und Kraft-/Stromabschaltung** an einem einzelnen Bein entwickeln, bevor alle 6 Beine montiert werden.
   - *(Hinweis: Die frühere Idee externer AS5600-Magnet-Encoder an den Coxa-Achsen wurde vollständig verworfen – das interne Potentiometer-Feedback liefert native 18-DOF-Telemetrie für alle 18 Gelenke ohne mechanische Luftspalt-Justage).*
3. **100 % Lötfreies Sensor-Ökosystem (Adafruit STEMMA QT / Qwiic):**
   - Sämtliche I2C-Sensoren nutzen 4-polige JST-SH-Steckverbinder (3,3 V Logikpegel vom Raspberry Pi). Keine eigenen Platinen oder Lötbrücken für Pull-Up-Widerstände nötig.

---

## 2. Aktuatorik & Stromversorgung (Bestand & Spezifikation)

| Komponente | Finale Auswahl / Spezifikation | Technische Eckdaten & Hinweise |
| :--- | :--- | :--- |
| **Servomotoren (18×)** | **Reely NR-645 MG BB** (Analog-Standardservo, 59 g) | Metallgetriebe, doppelt kugelgelagert, **25T-Spline (Futaba/Savöx-kompatibel)**, Maße $40{,}7 \times 20{,}5 \times 39{,}5\text{ mm}$, Stellkraft ~9,6–11 kg·cm @ 6,0 V, Blockierstrom ~1,8–2,5 A pro Servo. |
| **PWM-Treiber (2×)** | **PCA9685 16-Kanal I2C** | Board 1 (Links): **`0x40`**, Board 2 (Rechts): **`0x42`** (A1 gebrückt). *Wichtig:* `ALLCALL` (`0x70`) im Treiber deaktiviert, damit keine Adresskollision mit dem PCA9548-Multiplexer auftritt. |
| **Leistungs-UBECs (2×)** | **2× 5V/6V Hochstrom-UBEC (je 10–15 A)** | **Strikte Dual-Rail-Trennung:** UBEC 1 versorgt ausschließlich Board `0x40` (linke 9 Servos), UBEC 2 ausschließlich Board `0x42` (rechte 9 Servos). |
| **Logik-Versorgung** | **Separater 5V / 3A Buck-Converter** | Versorgt nur den Raspberry Pi 4 (verhindert Brownouts/Reboots bei Servo-Lastspitzen). Gemeinsamer Massepunkt (Star-Ground). |
| **Hauptstrom-Eingang** | **Amass XT60BE-M** (Einbaustecker mit Flansch) | Fest im Heck des Chassis verschraubt (Zugentlastung für Labornetzteil-Kabel bzw. 2S/3S LiPo). |

---

## 3. Sensorik & I2C-Bus-Architektur

### 3.1 I2C-Adressplan & Multiplexing

Um die 6 Bein-ADC-Boards (**ADS1115**) zu isolieren und den I2C-Bus übersichtlich zu strukturieren, wird ein **8-Kanal-Multiplexer (TCA9548A)** eingesetzt:

- **Haupt-I2C-Bus (`/dev/i2c-1` am Raspberry Pi):**
  - `0x40`: PCA9685 Servo-Board Links (PWM-Steuerung)
  - `0x42`: PCA9685 Servo-Board Rechts (PWM-Steuerung)
  - `0x71`: **TCA9548A 8-Channel I2C Multiplexer** (Lötbrücke A0 geschlossen $\rightarrow$ Adresse `0x71`, eliminiert Boot-Konflikt mit PCA9685 `0x70`)
  - `0x20`: **Adafruit MCP23017 I2C GPIO Expander** (16 digitale I/Os mit internen Pull-Ups)
  - `0x4A`: **Adafruit BNO085 9-DOF Orientation IMU** (Quaternionen, Gravity-Vektor, Linearbeschleunigung)
- **Multiplexer-Kanäle (`TCA9548A @ 0x71`):**
  - `CH0`: **ADS1115 #1 (Left Front: Coxa, Femur, Tibia, Fuß)** (`0x48`)
  - `CH1`: **ADS1115 #2 (Left Middle: Coxa, Femur, Tibia, Fuß)** (`0x48`)
  - `CH2`: **ADS1115 #3 (Left Rear: Coxa, Femur, Tibia, Fuß)** (`0x48`)
  - `CH3`: **ADS1115 #4 (Right Front: Coxa, Femur, Tibia, Fuß)** (`0x48`)
  - `CH4`: **ADS1115 #5 (Right Middle: Coxa, Femur, Tibia, Fuß)** (`0x48`)
  - `CH5`: **ADS1115 #6 (Right Rear: Coxa, Femur, Tibia, Fuß)** (`0x48`)
  - `CH6`: **2× INA228** (Strom-/Spannungsmessung Dual Servo-Rails, A0/A1 gebrückt)
  - `CH7`: **1× VL53L4CD Time-of-Flight (ToF) Distanzsensor (`0x29`)** in der Frontschürze (1 mm – 1300 mm Messbereich)

*(Hinweis: Die frühere Planung mit externen magnetischen AS5600-Encodern an der Coxa entfällt vollständig. Das interne Potentiometer-Feedback erfasst alle 18 Gelenke direkt und lückenlos).*

### 3.2 Taktile Bodenkontakt-Erkennung & Akustisches Feedback

- **Fußkontakt-Taster (6×):** **Omron D2F-L** Subminiatur-Mikroschalter mit Hebelarm (Made in Japan, extrem niedrige Betätigungskraft von ~0,75 N, sodass das Eigengewicht des Roboters den Schalter sicher auslöst).
- **Auswertung:** Alle 6 Mikroschalter werden zweipolig (`COM` auf `GND`, `NO` auf `GPA0`–`GPA5`) an den **MCP23017 (`0x20`)** angeschlossen (interne Pull-Up-Widerstände per Software aktiviert).
- **Akustischer Status-/Warnsummer:** **Passiver Piezo-Buzzer** direkt an **GPIO 13 (`PWM1`, Pin 33)** und `GND` (Pin 34) des Raspberry Pi 4 für mehrstimmige Status-Melodien (Boot-Chime, Kalibrier-Bestätigung, Stall-/Unterspannungswarnung).

### 3.3 18-DOF Analoges Closed-Loop Servo-Feedback (Reely NR-645 MG BB)

- **Konzept:** Direkter Abgriff der Schleiferspannung aller 18 internen Servopotentiometer für lückenlose Ist-Winkel-Erfassung, Blockadeerkennung und taktile Fußkontakt-Erkennung.
- **Empirische Modellparameter:** $R^2 = 0{,}99959$ ($99{,}96\,\%$ Linearität), Empfindlichkeit $+7{,}589\,\text{mV}/^\circ$, Nullpunkt $1{,}5633\,\text{V}$ bei $0^\circ$ (1500 µs), Formel: $\theta(V) = (V - 1{,}5633) \cdot 131{,}772^\circ$.
- **Architektur & Bus-Design (100 % Python auf dem Raspberry Pi 4):**
  - **TCA9548A 8-Kanal I2C-Multiplexer (`0x71` durch geschlossene Lötbrücke A0):** Verhindert Adresskollisionen mit dem PCA9685 `ALLCALL`-Default (`0x70`) beim Bootvorgang.
  - **6× ADS1115 (16-Bit 4-Kanal ADCs, je `0x48`):** Symmetrisches **1-Board-pro-Bein** Design an den Mux-Kanälen `CH0` bis `CH5`. Jeder ADS1115 liest `A0` (Coxa), `A1` (Femur), `A2` (Tibia) und `A3` (Reserve / analoger Fußtaster).
  - **Entstörung:** 18× (bzw. 24×) **100 nF 50V MLCC Keramikkondensatoren** direkt auf die Unterseite jedes ADS1115 zwischen Eingang und GND gelötet ($f_c \approx 636\,\text{Hz}$, filtert PWM- und Bürstenrauschen ab).
  - **Vollständige Schaltungs-Dokumentation:** Siehe [`closed_loop_plan.md`](closed_loop_plan.md).

---

## 4. Finale Stückliste (BOM – Einkaufsliste)

### 4.1 Sensorik- & Elektronik-Warenkorb

| Anz. | Bauteil / Bezeichnung | Funktion im Lasius Hexapod |
| :---: | :--- | :--- |
| **6×** | **ADS1115 16-Bit 4-Kanal I2C ADC Breakouts** | 1 Board pro Bein: Liest Coxa, Femur & Tibia Poti-Spannungen + Fußkontakt (`0x48` an Mux CH0–CH5) |
| **2×** | **TCA9548A 8-Channel I2C Multiplexer Breakouts** | Zentraler Sensor-Hub auf `0x71` (1x Torso, 1x Single-Leg Test-Rig). Isoliert alle 6 Bein-Boards |
| **100×**| **100 nF 50V MLCC Vielschicht-Keramikkondensatoren** | Tiefpass-Entstörfilter direkt auf die Unterseite der ADS1115-Boards gelötet ($f_c \approx 636\,\text{Hz}$) |
| **1×** | **Adafruit VL53L4CD Time of Flight Distance Sensor** (`5396`) | Präziser Nahbereichs-Laser-Abstandssensor (1–1300 mm) in der vorderen Chassis-Nase (Mux CH7) |
| **2×** | **Adafruit INA228 I2C 85V 20-Bit Power Monitor** (`5832`) | Echtzeit-Strom- (A), Spannungs- (V) und Leistungsmessung (W) getrennt für linke & rechte Servo-Bank (Mux CH6) |
| **1×** | **Adafruit 9-DOF Orientation IMU Fusion Breakout – BNO085** (`4754`) | On-Chip Sensor-Fusion (Roll/Pitch/Yaw) zur aktiven Horizontierung am Haupt-I2C-Bus (`0x4A`) |
| **1×** | **Adafruit MCP23017 I2C GPIO Expander Breakout** (`5346`) | Liest optionale digitale Fuß-Mikroschalter über den Haupt-I2C-Bus (`0x20`) aus |
| **8×** | `4210` | **STEMMA QT / Qwiic JST SH 4-Pin Cable – 100mm** | Kurze I2C-Verbindungen im Zentrum des Sensor-Trays |
| **6×** | `4401` | **STEMMA QT / Qwiic JST SH 4-Pin Cable – 200mm** | Zuleitungen vom Multiplexer in die 6 Sensor-Arme zu den Coxa-Encodern |
| **1×** | `5385` | **STEMMA QT / Qwiic JST SH 4-Pin Cable – 300mm** | Langer Uplink-Strang für das externe Single-Leg Docking Test-Rig |
| **2×** | `4397` | **STEMMA QT to Female Socket Jumper Cable (150mm)** | Haupt-I2C-Brücke zwischen Raspberry Pi GPIO-Header (3.3V, GND, SDA, SCL) und Sensor-Tray |

### 4.2 Mechanik-, Schalter- & Befestigungs-Ergänzungen

- **6–10× Omron D2F-L** Subminiatur-Mikroschalter mit Hebelarm (Befestigung mit **M2 × 10 mm** Schrauben/Muttern in der Tibia)
- **2× Amass XT60BE-M** Einbaustecker mit Montageflansch + **1× XT60H-F** Buchse für das Netzteilkabel
- **1× Passiver Piezo-Buzzer** (5 V / 3,3 V PWM-fähig, Rastermaß 7,6 mm / 12 mm Durchmesser mit 2-Pin Dupont-Stecker)
- **Schraubensortiment (Edelstahl A2, Innensechskant DIN 912):**
  - **M2 × 8 mm / 10 mm / 12 mm** (für STEMMA-QT-Breakouts, Omron D2F-L und Servo-Hörner)
  - **M3 × 8 mm / 12 mm / 16 mm / 20 mm** + selbstsichernde Muttern DIN 985 (für C-Bügel, Clamshell-Tibia und Chassis-Steher)
- **Filament:** **PETG (Schwarz & Signal-Akzentfarbe)** – zwingend statt sprödem PLA für alle lasttragenden Gelenkteile (Schichthaftung und Schlagzähigkeit unter Biegung).

---

## 5. Mechanische Neukonstruktion (CAD / 3D-Druck)

### 5.1 Verstärkter Coxa-Bügel (Schwachstellen-Eliminierung)
- **Ursache der bisherigen Brüche:** Zu dünne Wandstärken am Übergang zwischen Servohorn-Aufnahme und unterem Gegenlagerzapfen sowie Kerbwirkung bei PLA.
- **Neues Design:**
  - Verstärkte C-Klammer-Geometrie aus **PETG** (4–5 Wandlinien, 40–50 % Gyroid-Infill, liegend gedruckt für optimalen Faserverlauf entlang der Zug-/Biegekräfte).
  - **Mechanischer Vorteil durch Poti-Feedback:** Da keine externen AS5600-Magnete mehr benötigt werden, entfällt die Schwächung durch die Magnet-Tasche. Der untere Gegenlagerzapfen wird als **massiver Vollzylinder** ausgeführt, was die Biegefestigkeit im Lagerpunkt drastisch erhöht.

### 5.2 Modulare Underbody Sensor-Trägerplatte
- Wird von unten an den vorhandenen Chassis-Abstandsbolzen montiert.
- Dient als zentrale, vibrationsgedämpfte Trägerplattform für den TCA9548A Multiplexer, die 6 ADS1115 Bein-Module, die BNO085 IMU und Stromsensoren.
- **Wegfall der Luftspalt-Justage:** Es müssen keine filigranen Trägerarme mit $1{,}0\text{–}1{,}5\text{ mm}$ Magnet-Luftspalt unter die Drehachsen ragen.
- Integrierte **Kabelkanäle mit Zugentlastung** führen die 4-poligen Bein-Zuleitungen (PWM + Poti) geschützt ins Zentrum.

### 5.3 Zweischalige „Clamshell“-Tibia mit gedruckter Mäander-Federung & Rocker-Tarsus
- **Zweischaliger Aufbau (Left/Right Clamshell):** Zwei symmetrische Halbschalen werden flach auf dem Druckbett gedruckt (maximale Festigkeit in Längsrichtung, null Stützstruktur im Inneren) und mit M3-Schrauben verschraubt.
- **Integrierte Nachgiebigkeit (Compliant Mechanism):**
  - Eine **PETG-Mäander-Blattfeder (S-Spring)** im unteren Drittel der Tibia dämpft Stöße beim Aufsetzen des Fußes um ca. $2\text{–}3\text{ mm}$ ab und schützt die Servogetriebe.
- **Wippen-Fußspitze („Rocker-Tarsus“):**
  - Die Fußspitze ist über einen M3-Drehpunkt als kurze Wippe gelagert.
  - Sobald der Fuß den Boden berührt, kippt der Rocker-Tarsus um ca. $1{,}5\text{ mm}$ gegen die Mäander-Feder nach oben und betätigt über einen definierten **mechanischen Endanschlag (Hard-Stop)** den **Omron D2F-L Mikroschalter** (bzw. analogen Drucksensor an Pin `A3` des Bein-ADS1115).
  - **Überlastschutz:** Die Bodenreaktionskraft wird vom gedruckten Hard-Stop im Gehäuse aufgenommen – der Schalter selbst wird niemals durch das Robotergewicht zerdrückt.
- **Versteckte Kabelführung:** Die zwei Litzen des Mikroschalters laufen vollständig unsichtbar in einem internen Kanal zwischen den beiden Tibia-Halbschalen nach oben.

### 5.4 Single-Leg Docking Test-Rig
- Hohler, standfester Tisch-Prüfsockel mit identischer Geometrie wie ein einzelnes Chassis-Ecksegment.
- Ausgestattet mit dem 2. TCA9548A-Multiplexer und einem ADS1115-Breakout zum isolierten Testen und Kalibrieren einzelner Beine auf der Werkbank.
