# Hexapod:Lasius – 3D-Druckanleitung & Fertigungs-Teileliste (Bambu Lab & DfAM)

---

[Index](../../README.md) | [Software](../../software/README.md) | [Hardware](../../hardware/README.md) | [Docs](../../docs/README.md) |<br>
[Mechanics README](README.md) | [Style-Guide](STYLE_GUIDE.md) | [Femur FEA Report](../../docs/hardware/femur_topology_optimization_report.md) | [Wiring Harness Spec](../electronics/WIRING_HARNESS_SPEC.md)

---

Dieses Dokument enthält die verbindliche **3D-Druckanleitung** für die Fertigung aller mechanischen Eigenkonstruktionen der **Generation v2** auf **Bambu Lab 3D-Druckern** (X1-Carbon / X-Serie / P1S / A1 mit $256 \times 256 \times 256\,\text{mm}$ Bauraum) sowie die vollständige **Teileliste (Bill of Materials / BOM)** aller 3D-Druckteile, Zukauf- und Normteile für den schlüsselfertigen Aufbau des 18-DOF-Hexapods **Hexapod:Lasius**.

> [!IMPORTANT]
> **Chassis-Platten-Invariante (Hardware-Freeze):**  
> Die beiden $2{,}0\,\text{mm}$ Carbonfaser-Platten ([`body_bottom.FCStd`](models/custom/v1/parts/body_bottom.FCStd) und [`body_top.FCStd`](models/custom/v1/parts/body_top.FCStd)) **existieren bereits als physische, fertig gefräste Hardware** und werden **nicht 3D-gedruckt**! Sämtliche v2-3D-Druckkomponenten (Monocoque-Zentralkern, Belly Pan, Canopy, Montageblöcke) passen sich exakt an das bestehende Kontur- und Bohrungsraster dieser Carbonplatten an.

---

## 1. Vollständige Teileliste (Bill of Materials / BOM)

### 1.1 Eigene 3D-Druckteile (Custom Parts v2)

Alle Teile sind parametrisch in FreeCAD konstruiert und für FDM-Drucker mit $256 \times 256\,\text{mm}$ Druckbett optimiert.

| Baugruppe | Bauteil / CAD-Modell | Stk. | Material | Farbe ([Style-Guide](STYLE_GUIDE.md)) | Slicer-Ausrichtung / Bemerkung |
| :--- | :--- | :---: | :--- | :--- | :--- |
| **Bein (6×)** | [**`coxa.FCStd`**](models/custom/v2/parts/coxa/coxa.FCStd) | 6 | **PETG** / **PETG-CF** | Anthrazit / Slate Grey | Flach auf Seitenwange; integrierte $45^\circ$-Fachwerkfenster drucken stützfrei. |
| **Bein (6×)** | [**`femur.FCStd`**](models/custom/v2/parts/femur/femur.FCStd) | 6 | **PETG** / **PETG-CF** | Anthrazit / Slate Grey | Flach auf ebene Seitenwange ($Y = -28\,\text{mm}$); nur lokale Tree-Supports für Lagersitze. |
| **Bein (6×)** | [**`femur_cover.FCStd`**](models/custom/v2/parts/femur/femur_cover.FCStd) | 6 | **PETG** | Graphitschwarz | Flach auf Oberseite; $45^\circ$-Chevron-Kühlschlitze. |
| **Bein (6×)** | [**`tibia.FCStd`**](models/custom/v2/parts/tibia/tibia.FCStd) | 6 | **PETG** / **PETG-CF** | Anthrazit / Slate Grey | Flach auf Seitenfläche; Zug-/Biegekräfte verlaufen in Schichtebene (XY). |
| **Bein (6×)** | [**`tibia_cover.FCStd`**](models/custom/v2/parts/tibia/tibia_cover.FCStd) | 6 | **PETG** | Graphitschwarz | Flach auf Druckbett; Formschluss-Bajonettlaschen. |
| **Bein (6×)** | [**`tarsus.FCStd`**](models/custom/v2/parts/tarsus/tarsus.FCStd) | 6 | **PETG** / **PETG-CF** | Anthrazit / Slate Grey | Flach auf die Seite legen; federgelagerter Schaft für Fußschalter. |
| **Bein (6×)** | [**`tarsus_shoe.FCStd`**](models/custom/v2/parts/tarsus/tarsus_shoe.FCStd) | 6 | **TPU 95A** | Schwarz | Aufrecht / Sohle flach; 100 % Infill für elastische Stoßabsorption. |
| **Chassis** | [**`chassis_core_lower.FCStd`**](models/custom/v2/parts/chassis/chassis_core_lower.FCStd) | 1 | **PETG** / **PA-CF** | Anthrazit / Slate Grey | Ebene 1 ($Z = 0{,}02\dots 23{,}99\,\text{mm}$, `45,2 cm³` / `57,4 g` massiv): Akkufach, Boden-Plug & Formschluss-Zentrierkragen; 0 % Innenraum-Support! |
| **Chassis** | [**`chassis_core_upper.FCStd`**](models/custom/v2/parts/chassis/chassis_core_upper.FCStd) | 1 | **PETG** / **PA-CF** | Anthrazit / Slate Grey | Ebene 2 ($Z = 24{,}01\dots 53{,}28\,\text{mm}$, `51,4 cm³` / `65,3 g` massiv): Plan auf Zwischenboden — **100 % stützfrei**! |
| **Chassis** | [**`chassis_belly_pan.FCStd`**](models/custom/v2/parts/chassis/chassis_belly_pan.FCStd) | 1 | **PETG** | Anthrazit / Slate Grey | Flach auf Innenboden; $45^\circ$-Fase für ToF-Sensoröffnung. |
| **Chassis** | [**`chassis_battery_hatch.FCStd`**](models/custom/v2/parts/chassis/chassis_battery_hatch.FCStd) | 1 | **PETG** | Graphitschwarz | Flach auf Druckbett. Werkzeuglose Akkuverriegelung. |
| **Chassis** | [**`chassis_rpi_mount.FCStd`**](models/custom/v2/parts/chassis/chassis_rpi_mount.FCStd) | 1 | **PETG** | Technisches Blau / Schwarz | Flach auf untere Trägerplatte. |
| **Chassis** | [**`chassis_canopy.FCStd`**](models/custom/v2/parts/chassis/chassis_canopy.FCStd) | 1 | **PETG Transluzent** / PMMA | Eisblau-Transluzent / Anthrazit | Einteiliges Magnet-Canopy mit integrierten RPi-Chevrons, UBEC-Abluftschlitzen & offenen Heck-Schalterbögen; diagonal auf $256 \times 256\,\text{mm}$ Druckbett platzieren. |

---

### 1.2 Mechanische Kauf-, Norm- & Verbindungsteile (COTS)

| Baugruppe | Komponente | Spezifikation / Norm | Stk. | Funktion / Einsatzort |
| :--- | :--- | :--- | :---: | :--- |
| **Gelenklager** | Miniatur-Rillenkugellager | **684ZZ** ($\varnothing 8{,}0 \times 4{,}0 \times 3{,}0\,\text{mm}$) | **18×** | 6× Chassis Pivot, 6× Femur-Gegenlager, 6× Knie-Gegenlager |
| **Gegenlager** | Flache Sechskantmutter | **DIN 439 M4** ($SW = 7{,}1\,\text{mm}, H = 2{,}2\,\text{mm}$) | **18×** | Festsitz in Sechskanttaschen der Coxa- & Tibia-Gegenlager |
| **Gelenkachsen** | Senkkopfschrauben | **DIN 7991 M4 × 20 mm** (A2 Edelstahl) | **18×** | Drehachsen für Chassis-Lager, Hüft- und Kniegelenk |
| **Passscheiben** | Distanzscheiben | **DIN 988 $\varnothing 8 \times \varnothing 4 \times 0{,}5\,\text{mm}$** | **18×** | Freilauf zwischen Kugellager-Innenring und Gelenkgabel |
| **Gewindeeinsätze** | Ruthex Heat-Set Inserts | **Ruthex M2** ($L = 4{,}0\,\text{mm}, \varnothing_{\text{Bohr}} = 3{,}2\,\text{mm}$) | **36×** | 24× Femur-Deckel (4/Bein), 12× Tibia-Deckel (2/Bein) |
| **Gewindeeinsätze** | Ruthex Heat-Set Inserts | **Ruthex M2.5** ($L = 5{,}7\,\text{mm}, \varnothing_{\text{Bohr}} = 4{,}0\,\text{mm}$) | **10×** | 2× Sensor-Hub Carrier Board, 4× RPi-Mount, 4× Servos |
| **Kern-Zuganker** | Rund-Distanzhülse / Gewindemuffe | **M3 × 50 mm** ($\varnothing 5{,}0\,\text{mm}$ Alu / Messing, Innengewinde) | **4×** | Durchgehende Zuganker in den 4 `Chassis_Core`-Eckpfeilern `(±45, ±30 mm)` (`standoff_m3x50_round.FCStd`); ersetzt 8× Ruthex M3 & spannt `Lower` + `Upper` spielfrei zwischen `Body_Bottom` & `Body_Top` |
| **Deckelschrauben** | Senkkopfschrauben (Innensechskant) | **DIN 7991 M2 × 6 mm** (A2 Edelstahl, SW 1,3) | **36×** | Einheitliche Befestigung für alle 12 Service-Deckel in Ruthex M2 Einsätzen (`24× femur_cover` + `12× tibia_cover`) |
| **Servohorn** | Linsenkopfschrauben (Innensechskant) | **ISO 7380 M2 × 5 mm** (A2 Edelstahl, $H = 1{,}15\,\text{mm}$) | **72×** | Befestigung aller 18× 25T-Metall-Servohörner ($\varnothing 16\,\text{mm}$ Lochkreis): 24× Coxa-Hörner auf `Body_Top` (flacher Kopf hält $\ge 0{,}57\,\text{mm}$ Abstand zum Canopy) + 48× Hüft-/Knie-Hörner im `Femur` (versenkt in $\varnothing 4{,}3 \times 1{,}5\,\text{mm}$ Taschen) |
| **Chassis** | Senkkopfschrauben | **DIN 7991 M3 × 8 mm / 12 mm** | **16×** | Verschraubung Belly Pan & Canopy an Chassis Core |
| **Tarsus-Feder** | Zylindrische Druckfeder | $\varnothing_{\text{a}} = 3{,}5\,\text{mm}, d = 0{,}5\,\text{mm}, L_0 = 10\dots 12\,\text{mm}$ | **6×** | Rückstellfeder für 3D-Exoskelett-Tarsus |
| **Tarsus-Pivot** | Zylinderstift / Achse (COTS) | [**`dowel_pin_3x12.FCStd`**](models/cots/dowel_pin_3x12.FCStd) — **DIN 7 / ISO 2338 $\varnothing 3{,}0 \times 12{,}0\,\text{mm}$** (A2 Edelstahl, beidseitig angefast) | **6×** | Drehachse des Tarsus im Tibia-Gabelkopf (wartungsfreie Gleitlagerung) |
| **Canopy-Magnete** | Neodym-Scheibenmagnet | **$\varnothing 5{,}0 \times 2{,}0\,\text{mm}$** (N52) | **8×** | 4× in `chassis_rpi_mount`-Pfeilern + 4× in `chassis_canopy`-Zentrierbechern (`±48, ±36 mm`, geringes Streufeld zum BNO085) |
| **IMU-Befestigung** | Nylon- / Messing-Schrauben | **M2.5 × 5 mm** (nichtmagnetisch!) | **4×** | Befestigung des Adafruit BNO085 auf dem Front-Deck von `chassis_rpi_mount` |

---

### 1.3 Elektronik-, Aktuator- & Sensorkomponenten

| Komponente | Typ / Modell | Stk. | Bemerkung |
| :--- | :--- | :---: | :--- |
| **Servo-Aktuatoren** | **Torcster / Reely NR-645 MG BB** | **18×** | Metallgetriebe, kugelgelagert; 150 mm weiße Poti-Litze herausgeführt |
| **Bein-Wandler** | **ADS1115 (V280)** Breakout | **6×** | 16-Bit I²C ADC Modul im Femur (`SCL` vor `SDA`, Adresse `0x48`) |
| **Filterkondensatoren** | **100 nF MLCC Keramikkondensator** (50V, Code 104) | **24×** | Je 4× pro Wandler direkt an Stiftleiste gelötet (A0..A3 nach GND) |
| **Pull-Up-Widerstand** | **10 kΩ** Metallschicht 0,25W | **6×** | Je 1× pro Wandler zwischen A3 und VDD (Fußschalter) |
| **Fußsensor** | **Omron D2FC-F-K** oder **D2F-L** | **6×** | Subminiatur-Mikroschalter in der Tibia-Kralle |
| **Hauptrechner** | **Raspberry Pi 4 Model B** (4GB / 8GB) | **1×** | Linux Hauptsteuerung via I²C Master |
| **PWM-Servotreiber** | **PCA9685** 16-Kanal I²C Breakout | **2×** | Daisy-Chain: Links `0x40`, Rechts `0x42` |
| **I²C-Multiplexer** | **TCA9548A / PW548A** (violett) | **1×** | Adresse `0x71` (`A0 → 3,3V`), trennt alle 6 Bein-Wandler |
| **Zentralplatine** | [**Sensor-Hub Carrier PCB**](../electronics/pcb/sensor_hub/README.md) | **1×** | Maßgeschneidertes KiCad-Board ($54 \times 22\,\text{mm}$) auf Zwischenboden |
| **Bodensensor** | **VL53L5CX** Time-of-Flight Distanzsensor | **1×** | 9-Zonen Laser-Terrain-Scanner in der geschlossenen Heck-Brücke der Belly Pan ($X = -58{,}5\,\text{mm}$) |
| **Lagesensor (IMU)** | **Adafruit BNO085** 9-DOF IMU (PID 4754) | **1×** | Front-Deck von `chassis_rpi_mount.FCStd` ($X = +75{,}0, Y = 0{,}0, Z = 58{,}32\,\text{mm}$); nichtmagnetische M2.5-Schrauben |
| **Spannungsversorgung** | **2× Hobbywing BEC 10A V2-Car (`HW30603003`, 6,0 V)** + 5,1 V Pi-Buck (`ubec_3a`) | **2× + 1×** | Alle 3 UBECs thermisch isoliert auf `Body_Top` / `chassis_rpi_mount.FCStd` (2× Hobbywing Heck-Deck `X = -79,5, Y = ±21,5`, `ubec_3a` portfreie `+Y`-Flanke `X = 0, Y = +39,5`) oder alternativ im 2-DoF Power-Gaster (`gaster_power_assembly.FCStd`, Option G2) |
| **Bedienfeld & Schutz** | **Interner Akku-XT60** + **25 A Mini-ATM Sicherung** + **2× Mini-Schiebeschalter** | **1× / 1× / 2×** | Komplettes Heck-Bedienfeld auf `chassis_rpi_mount.FCStd` (`2×` Schalter in 45°-Fasen bei `X = -116, Y = ±14,5`, `25 A` Sicherung mittig dazwischen bei `X = -105, Y = 0` durch Canopy-Öffnung ziehbar; über Heck-Spacer verschraubt) + XT60 unter Akkuklappe; Option G2: Power-Gaster-Flanken |

---

## 2. Bambu Lab Slicer- & Fertigungsrichtlinien

### 2.1 Druckbett & Haftung
* **Platte:** **Textured PEI Plate** (strukturiertes PEI-Federstahlblech).
* **Betttemperatur:**
  * **PETG / PETG-CF:** $75\text{--}80\,^\circ\text{C}$
  * **TPU 95A:** $35\text{--}45\,^\circ\text{C}$ (auf strukturierter PEI-Platte kein Kleber nötig; Bauteil vor dem Abnehmen vollständig abkühlen lassen!).
  * **PA-CF:** $100\,^\circ\text{C}$ (geschlossener Bauraum zwingend).

### 2.2 Nozzle & Wandstärken-Profile
* **Nozzle-Typ:** **$0{,}4\,\text{mm}$ gehärteter Stahl (Hardened Steel)**.  
  *Wichtig:* Bei abrasiven Filamenten wie PETG-CF oder PA-CF verschleißen Edelstahl- und Messingdüsen innerhalb weniger hundert Gramm.
* **Wandlinien (Perimeter):** **5 bis 6 Wandlinien** einstellen (Wandstärke $\ge 2{,}0\text{--}2{,}4\,\text{mm}$).
  * *Konstruktiver Grund:* Die FEA-Belastungsanalysen zeigen, dass 90 % der dynamischen Biegemomente von den Außenkonturen aufgenommen werden. Mit 5 Wandlinien werden alle bionischen Fachwerkstreben ($w = 2{,}50\,\text{mm}$) als **100 % massives Volllaminat** gedruckt.
* **Top- / Bottom-Shells:** Mindestens **5 Deck- und 5 Bodenschichten** (min. $1{,}0\text{--}1{,}2\,\text{mm}$).

### 2.3 Infill-Strategie
* **Infill-Muster:** **Gyroid** oder **3D-Wabe (3D-Honeycomb)**.
* **Infill-Dichte:** **35 % bis 45 %**.
* *Warnung vor 'Grid'-Infill:* Niemals klassisches *Grid*- oder *Triangles*-Infill verwenden! Bei den hohen Verfahrgeschwindigkeiten der Bambu Lab Drucker schlägt die Düse an den Schnittpunkten derselben Schicht an, was bei PETG zu Schichtversatz und Rissbildung führen kann. Gyroid kreuzt sich nicht auf derselben Ebene.

### 2.4 Kühlung & Geschwindigkeiten (Maximale Schichtverschweißung)
* **Außenwand-Geschwindigkeit:** Auf **$80\text{--}120\,\text{mm/s}$** begrenzen (Standard-Profile sind mit $> 200\,\text{mm/s}$ zu schnell für maximale Zugfestigkeit).
* **Volumetric Speed Limit:** Max. **$12\text{--}14\,\text{mm}^3/\text{s}$** für Standard-PETG; $14\text{--}16\,\text{mm}^3/\text{s}$ für High-Speed-PETG.
* **Bauteillüfter:** Max. **30–50 %**. Zu starke Kühlung kühlt das abgelegte PETG schockartig ab und schwächt die inter-layer Bindung um bis zu 40 %.
* **Bauraum-Lüftung:** Bei reinem PETG den oberen Glasdeckel oder die Fronttür einen Fingerbreit geöffnet lassen (Bauraum $< 38\,^\circ\text{C}$), um Heat-Creep im Extruder zu verhindern.

### 2.5 Multi-Material-Support-Trick mit dem AMS
Falls ein **Bambu AMS** vorhanden ist:
* **PLA als Stütz-Grenzschicht (Support Interface) für PETG:**
  * PLA und PETG haften molekular **nicht** aneinander.
  * Im Slicer das Bauteil aus PETG drucken, als Stützmaterial ebenfalls PETG wählen, aber für **Support Interface (Kontaktfläche)** normales PLA zuweisen.
  * **Top Z-Distance (Z-Abstand):** Auf exakt **$0{,}00\,\text{mm}$** setzen!
  * *Ergebnis:* Die Stützstrukturen brechen nach dem Druck vollkommen rückstandsfrei wie Glas ab; Kugellagerkragen und Überhänge werden spiegelglatt wie auf dem Druckbett.
* **TPU 95A Handling:** TPU **niemals über das AMS** zuführen (Gefahr des Verhedderns in den Rollen). Immer direkt von der externen Spulenhalterung an der Rückseite des Druckers zuführen.

---

## 3. Detaillierte Druck- & Slicing-Anleitung je Bauteil

```text
Bauteil-Druckbett-Belegung (Bambu Lab 256 x 256 mm):
┌────────────────────────────────────────────────────────┐
│  Platte 1: 6x Femur_Body (flach auf Seitenwange)       │
│  Platte 2: 6x Tibia_Body + 6x Tarsus (flach auf Seite) │
│  Platte 3: 6x Coxa (flach auf Seitenwange)             │
│  Platte 4: 1x Chassis_Core_Lower + 1x Chassis_Core_Upper│
│            + 1x Belly_Pan + 1x Battery_Hatch            │
│  Platte 5: 6x Femur_Cover + 6x Tibia_Cover + Covers    │
│  Platte 6: 6x Tarsus_Shoe (TPU 95A, externe Spule)     │
│  Platte 7: 1x Chassis_Canopy (diagonal auf Bett)       │
└────────────────────────────────────────────────────────┘
```

### 3.1 Femur ([`femur.FCStd`](models/custom/v2/parts/femur/femur.FCStd))
* **Druckausrichtung:** Auf die flache Außenwange legen ($Y = -28{,}00\,\text{mm}$ liegt plan auf dem Bett).
* **Stützstrukturen:**
  * Alle Warren-Fachwerkfenster besitzen $45^\circ$-Überhänge und drucken **ohne Stützen**.
  * **Support erzwingen (Tree Supports):** Nur an den beiden kreisrunden Absätzen der 684ZZ-Kugellagerbohrung und den M2-Senkungen an der Unterseite.
* **Druckparameter:** 5 Wandlinien, 40 % Gyroid, $0{,}16\text{--}0{,}20\,\text{mm}$ Schichthöhe.
* **Druckzeit:** ca. 2 h 40 min pro Femur (oder alle 6 Stück im Batch auf einer Platte in ca. 15 h).

### 3.2 Tibia ([`tibia.FCStd`](models/custom/v2/parts/tibia/tibia.FCStd)) & Tarsus ([`tarsus.FCStd`](models/custom/v2/parts/tarsus/tarsus.FCStd))
* **Druckausrichtung:** Flach auf die Seitenfläche legen.  
  *Vorteil:* Die Zug- und Biegekräfte der Kniekralle wirken parallel zu den Extrusionslinien der XY-Ebene.
* **Stützstrukturen:** Support für die untere Gegenlager-Tasche (DIN 439 Mutter-Sitz) und den Schacht des Tarsus-Führungszapfens.
* **Druckparameter:** 6 Wandlinien, 45 % Gyroid, $0{,}16\,\text{mm}$ Schichthöhe.

### 3.3 Coxa ([`coxa.FCStd`](models/custom/v2/parts/coxa/coxa.FCStd))
* **Druckausrichtung:** Flach auf die ebene Gegenlager-Seitenwange legen.
* **Stützstrukturen:** Minimal; der Zwillingsservokäfig überbrückt stützfrei oder mit leichten Baumstützen im Servoschacht.
* **Druckparameter:** 5 Wandlinien, 40 % Gyroid.

### 3.4 Tarsus-Schuh ([`tarsus_shoe.FCStd`](models/custom/v2/parts/tarsus/tarsus_shoe.FCStd))
* **Material:** **TPU 95A** (z. B. Bambu TPU 95A HF).
* **Druckausrichtung:** Aufrecht, Sohlenfläche flach auf dem Bett.
* **Druckparameter:** **100 % Infill (Solid)** oder 6 Wandlinien.
* **Druckgeschwindigkeit:** Max. $30\text{--}40\,\text{mm/s}$ (langsam drucken für perfekte Verschweißung).

### 3.5 Zweistufiger Monocoque-Chassis-Kern ([`chassis_core_lower.FCStd`](models/custom/v2/parts/chassis/chassis_core_lower.FCStd) & [`chassis_core_upper.FCStd`](models/custom/v2/parts/chassis/chassis_core_upper.FCStd))
Durch die horizontale Formschluss-Teilung bei `Z_SPLIT = 24,00 mm` entfällt **100 % des ehemaligen Innenraum-Supports**, und Änderungen am Akkufach erfordern nur den Neudruck der ~`40 g`-Unterwanne:
* **`chassis_core_lower.FCStd` (Ebene 1 — Akkufach, `45,2 cm³` / `57,4 g` massiv):** Aufrecht auf die untere `Body_Bottom`-Plugfläche (`Z = 0,02 mm`) legen. **0 % Support im Akkufach** ($45^\circ$-LiPo-Stopprippen, $45^\circ$-Bogen-Schott und $45^\circ$-Zungenrampen drucken komplett frei; nur lokaler `2 mm`-Rand-Support unter dem äußeren Eckpfeiler-/Schwalbenschwanz-Kragen).
* **`chassis_core_upper.FCStd` (Ebene 2 — Elektronikwanne, `51,4 cm³` / `65,3 g` massiv):** Plan auf die Unterseite des Zwischenbodens (`Z = 24,01 mm`) legen. **100 % stützfrei druckbar** (Pfeiler-Zentriersenkungen haben $45^\circ$-Innenkegel, Zungen-Nuten laufen durch den Zwischenboden, $0{,}35\,\text{mm}$-Außenfase verhindert Elefantenfuß).
* **Montage (Option 1):** Beide Hälften über die 4 Pfeiler-Zentrierkragen & 5 Innen-Führungszungen zusammenstecken, die **4× `M3 × 50 mm` Rund-Distanzhülsen (`Ø5,0 mm`)** in die durchgehenden `Ø5,25 mm` Pfeilerbohrungen einschieben und `Belly_Pan` (unten) sowie `RPi_Mount` (oben) mit den vorhandenen `M3 × 10/12 mm` Senkschrauben verspannen.
* **Druckparameter:** 5 Wandlinien, 40 % Gyroid, $0{,}20\,\text{mm}$ Schichthöhe.

### 3.6 Optionales Zubehör: Schreibtisch-Entwicklungsständer ([`desk_stand_assembly.FCStd`](models/custom/v2/desk_stand_assembly.FCStd) & angedockte Gesamtansicht [`desk_stand_docked_assembly.FCStd`](models/custom/v2/desk_stand_docked_assembly.FCStd), `22,1 mm` Tischplatte)
Modularer Klemm-Entwicklungsständer (`H = 235 mm` Bauchhöhe über der Tischplatte, $+8{,}3\dots +136{,}3\,\text{mm}$ Beinfreiheit bis zum extremsten Software-Limit, offener Mittelkanal für VL53L5CX-ToF & XT60-Labornetzteil, 4× $90^\circ$ drehbarer Flansch):

| Bauteil | Material | Druckausrichtung (Bambu Lab $256 \times 256\,\text{mm}$) | Stützen & Parameter |
| :--- | :--- | :--- | :--- |
| [**`desk_stand_clamp.FCStd`**](models/custom/v2/parts/stand/desk_stand_clamp.FCStd) | **PETG** (Anthrazit) | **Flach auf Seitenflanke** ($77 \times 60 \times 38\,\text{mm}$, ~`56 g`) — I-Träger-C-Rücken & verjüngte Wangen, durchgehende XY-Perimeter! | Stützfrei (bis auf lokalen Zentrierbund), 6 Wandlinien, 40 % Gyroid |
| [**`desk_stand_column.FCStd`**](models/custom/v2/parts/stand/desk_stand_column.FCStd) | **PETG** (Anthrazit) | **Aufrecht stehend** ($211{,}4 \times 36 \times 36\,\text{mm}$, **`69 g` massiv**) — hohler 4-seitiger Kran-Gittermast (`2,50 mm` Streben, 7 Rauten-Etagen, `45°`-Innengewölbe)! | 100 % stützfrei, 6 Wandlinien (Streben drucken 100 % voll), Lüfter `30–40 %` für optimale Z-Schichthaftung |
| [**`desk_stand_cradle.FCStd`**](models/custom/v2/parts/stand/desk_stand_cradle.FCStd) | **PETG** (Tech.-Blau) | Flach auf Unterseite ($129{,}0 \times 63{,}0 \times 21{,}6\,\text{mm}$, ~`24 g`) — kompakte H-Nabe mit 4 konischen PETG-Kerndornen (`(±58,0; ±26,55 mm)`) für das 4-Punkt-Klick-Docking | **100 % stützfrei**, 5 Wandlinien, 40 % Gyroid |
| [**`desk_stand_knob.FCStd`**](models/custom/v2/parts/stand/desk_stand_knob.FCStd) | **PETG** (Graphit) | Sterngriff + Druckteller plan auf Boden | Stützfrei, 5 Wandlinien, 40 % Gyroid |
| [**`desk_stand_pads.FCStd`**](models/custom/v2/parts/stand/desk_stand_pads.FCStd) | **TPU 95A** (Schwarz) | 2× Tisch-Antirutschpads flach + **4× elastische Klick-Rast-Hülsen** aufrecht auf Bodenflansch (externe Spule!) | Stützfrei, 100 % Infill / 4 Wandlinien |

* **Zusätzliche Normteile für den Ständer:** `1× DIN 933 M8 × 40 mm` Sechskantschraube, `1× DIN 934 M8` Mutter, `8× DIN 7991 M4 × 20 mm` Senkkopfschrauben, `8× DIN 934 M4` Sechskantmuttern (optional `2× 20 mm` Klettband für Hochdynamik-Tests).

---

## 4. Nachbearbeitung & Werkstatt-Montage

### 4.1 Einschmelzen der Ruthex Heat-Set Gewindeeinsätze
1. **Werkzeug:** Lötkolben mit spezieller planer Einschmelzspitze für M2 / M2.5 / M3 (z. B. Ruthex Lötspitzenset).
2. **Temperatur:** Lötkolben auf **$220\text{--}230\,^\circ\text{C}$** für PETG ($260\,^\circ\text{C}$ für PA-CF) einstellen.
3. **Durchführung:**
   * Gewindeeinsatz senkrecht in die gedruckte $8^\circ$-Einführschräge einsetzen.
   * Mit der warmen Lötspitze ohne seitlichen Druck leicht axial nach unten führen, bis der Rand des Inserts ca. **$0{,}1\text{--}0{,}2\,\text{mm}$ unter die Bauteiloberfläche** einsinkt.
   * Lötspitze zügig nach oben abziehen und den Kunststoff sofort 10 Sekunden lang mit einer planen Metallfläche (z. B. Rückseite einer Feile) andrücken, damit der Insert plan und fest sitzt.

### 4.2 Einpressen der Kugellager & Flachmuttern
1. **684ZZ Kugellager ($\varnothing 8 \times 3\,\text{mm}$):**
   * Die Lagersitze sind im CAD mit $\varnothing 8{,}05\,\text{mm}$ auf leichten Presssitz dimensioniert.
   * Bei Bedarf Bohrung mit einem Rundschaber säubern und das Lager mit einer M4-Schraube und zwei Beilagscheiben kontrolliert axial in den Sitz einziehen.
2. **DIN 439 M4 Muttern:**
   * In die $SW = 7{,}10\,\text{mm}$ Sechskanttaschen einlegen. Falls die Passung stramm ist, mit dem Lötkolben auf niedrigster Stufe ganz leicht erwärmen und flach bündig eindrücken.

### 4.3 Qualitätskontrolle vor dem Zusammenbau (QC Gate)
- [ ] Alle Bohrungen für Servohörner ($\varnothing 2{,}0\,\text{mm}$) frei von Stringing.
- [ ] M4-Gegenlagerachsen drehen sich ohne Spiel und ohne Klemmen leichtgängig im 684ZZ-Lager.
- [ ] Der Omron-Fußschalter klickt im Tarsus sauber, bevor der Tarsus an den harten Endanschlag anschlägt.
- [ ] Das ADS1115-Breakout liegt flach und wackelfrei auf den beiden Zentrierstiften der Femur-Kammer auf.