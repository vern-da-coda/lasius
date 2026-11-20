# Lasius CAD Generation v2 – Models & Mechanics Backlog

---

[Project Index](../../../../../README.md) | [Mechanics Documentation](../../../README.md) | [Closed Loop Plan](../../../../../docs/hardware/closed_loop_plan.md) |<br>
[Femur Script](../../../scripts/v2/generate_femur.py) | [Coxa Script](../../../scripts/v2/generate_coxa.py) | [Tibia Script](../../../scripts/v2/generate_tibia.py)

---

Dieser Backlog führt alle offenen Aufgaben, konstruktiven Erweiterungen und Verifikationsschritte für die **Generation v2** der Lasius-Mechanik (`hardware/mechanics/models/custom/v2/`).

---

## 1. Femur (`parts/femur/femur.FCStd`)

- [x] **Befestigung des AD-Wandlers (ADS1115) via Option C (Zentrierstifte + Deckel-Niederhalter):**  
  * **Status:** Erfolgreich implementiert in [`generate_femur.py`](../../../scripts/v2/generate_femur.py).
  * **Konstruktion:**
    * Auf den beiden Stand-off-Sockeln am Kammerboden ($Z = -4.80\,\text{mm}$) sind zwei vertikale **Zentrierstifte ($\varnothing 2.15\,\text{mm}$)** mit Konus-Fase integriert, die formschlüssig in die beiden $\varnothing 2.35\,\text{mm}$ Bohrungen der Platine greifen ($X = 39.90 / 60.10\,\text{mm},\; Y = Y_{\text{mid}} + 5.30\,\text{mm}$).
    * An der Unterseite der transluzenten Haube ([`Femur_Canopy`](../../../scripts/v2/generate_femur.py)) steigen zwei integrierte **Niederhalter-Hülsen mit Pin-Bohrung** bis auf $Z = -3.05\,\text{mm}$ herab.
    * Beim Verschrauben des Rahmens ([`Femur_Cover_Frame`](../../../scripts/v2/generate_femur.py)) wird die ADS1115-Platine vibrationsfrei und schraubenlos auf die Sockel geklemmt.
- [x] **Transluzenter Mini-Canopy Servicedeckel (Vorschlag 2):**  
  * **Status:** Erfolgreich implementiert und in allen Assemblies synchronisiert.
  * **Architektur:**
    * Zweiteiliger Aufbau:
      1. `Femur_Cover_Frame`: Graphitschwarz PETG, bündig zur Oberschalen-Taillierung, 4× M2-Senkkopfverschraubung, $1.5\,\text{mm}$ Dichtlippen-Ring, zentrale Haltefassung.
      2. `Femur_Canopy`: Eisblau-Transluzent (55 % Alpha) Acryl-/Plexiglas-Optik, aerodynamisch doppelt gekrümmter Loft analog [`chassis_canopy.FCStd`](parts/chassis/chassis_canopy.FCStd), 3 bionische $45^\circ$-Chevron-Kühlschlitze (`>>>`).
    * Fertigungsexporte: `femur_cover_frame.stl`, `femur_canopy.stl`, `femur_cover.stl`, `femur.step`.
- [ ] **Kantenverrundung an den Kabeldurchführungen:**  
  * Ein- und Auslässe der beiden horizontalen Kabeltunnels ($14 \times 7\,\text{mm}$) zu den Hüft- und Knie-U-Mäulern mit vergrößerten Einlauffasen/Fillets ($R \ge 1.0\,\text{mm}$) versehen, um Scheuern der Servolitzen im Dauerbetrieb zu verhindern.
- [ ] **Servohorn-Integration / Einlassen in die Femur-Wange:**  
  * **Fragestellung:** Prüfen, ob die Metall-Servohörner (25T Standard) an den beiden U-Mäulern (Hüft- und Kniegelenk) formschlüssig in die innere Femur-Wange eingelassen (versenkt) werden sollten.
  * **Vorteile:**
    * Formschlüssige Drehmomentübertragung entlastet die M2-Befestigungsschrauben von Scherkräften.
    * Bündiger Abschluss ohne zusätzlichen axialen Bauraumbedarf in Y-Richtung ($Y = 29.30\,\text{mm}$ Anlageebene).
  * **Zu prüfen:** Verbleibende Restwandstärke der vorderen Wange ($Y_{\text{front\_seat}} = 33.30\,\text{mm}$ bis $Y_{\text{front\_out}} = 35.30\,\text{mm}$) bei z. B. $1.5 - 2.0\,\text{mm}$ Einlasstiefe für das Horn.
  * **Betroffener Code:** [`generate_femur.py`](../../../scripts/v2/generate_femur.py) (Abschnitt `Cut the Two U-Openings`).
- [ ] **Deckelpassung (`Femur_Cover`):**  
  * Reale Spaltmaße nach Testdruck verifizieren; Passung der 4× M2-Senkkopfschrauben mit Senkung im Deckel und Pilotlöchern im Gehäuse prüfen.

---

## 2. Coxa (`parts/coxa/coxa.FCStd`)

- [x] **Monolithisches Coxa-Gelenksegment & 45°-A-Truss-Fachwerk (Konzept 1):**  
  * **Status:** Erfolgreich implementiert gemäß [`STYLE_GUIDE.md`](../../../STYLE_GUIDE.md).
  * **Umsetzung:**
    * Monolithische Wangen mit $G^1$-stetigen S-Kurven und 100 % spiegelbildlichem Profil um $Z = 9{,}00\,\text{mm}$.
    * 45°-Flankenfenster über Servohorn und Gegenlager sowie 45°-A-Truss (Chevron-Fachwerk) in der Zentralbrücke mit durchgehendem Firststeg ($w = 2{,}50\,\text{mm}$, $R = 1{,}40\,\text{mm}$).
    * Reine $\varnothing 3{,}20\,\text{mm}$ Durchgangsbohrung für die M3-Schraubenachse (Kugellager sitzt in der Bodenplatte).
    * Gewichtsersparnis: $42{,}3\,\text{cm}^3$ / $53{,}7\,\text{g}$ PETG ($-9{,}6\,\text{g}$ Delta).
  * **Betroffener Code:** [`generate_coxa.py`](../../../scripts/v2/generate_coxa.py).
- [ ] **DIN 439 M4 Flachmutter-Sitz (Gegenlager Femur-Achse):**  
  * Maßhaltigkeit der verpressten M4-Sechskanttasche für die flache DIN 439 Mutter nach Testdruck prüfen (Sitz $SW = 7.10\,\text{mm}$, Tiefe $2.40\,\text{mm}$).
- [ ] **Kabelauslass-Führung:**  
  * Freigang für die 4-adrige Servozuleitung des Coxa-Servos entlang des Versteifungs-Gussets prüfen.

---

## 3. Tibia & Tarsus (`parts/tibia/tibia.FCStd` & `parts/tarsus/tarsus.FCStd`)

- [x] **Bionischer Zwillings-Servokäfig, SVG-Tropfenfenster & Bajonett-Servicedeckel (Option 2c-V2):**  
  * **Status:** Vollständig implementiert in [`generate_tibia.py`](../../../scripts/v2/generate_tibia.py), [`generate_tibia_assembly.py`](../../../scripts/v2/generate_tibia_assembly.py) und [`generate_tarsus_assembly.py`](../../../scripts/v2/generate_tarsus_assembly.py).
  * **Konstruktion:**
    * **Zwillings-Servokäfig (Twin Servo Cage):** Vollständig analog zu Coxas Femur-Servokäfig ausgeführt ($w = 2{,}50\,\text{mm}$, $R = 1{,}40\,\text{mm}$ Warren-Truss-Fachwerkfenster, DIN 439 M4 Flachmutter-Gegenlagertasche).
    * **Organisches SVG-Tropfenfenster:** Monolithisch in `Tibia_Body` platziert ($X \in [38{,}5, 75{,}4]\,\text{mm}, Y \in [29{,}4, 45{,}4]\,\text{mm}$); obere linke Deckelschraube entfällt zugunsten von 2 integrierten Formschluss-Bajonettlaschen + 2× M2 DIN 7991 Senkschrauben am konturierten `Tibia_Cover`.
    * **Lastfreie Mikroschalter-Auslösung & Staub-Labyrinth:** Horizontaler $0^\circ$-Omron D2FC-F-K NC-Mikroschalter; breite flache Deckenanschläge oberhalb der Feder und zwischen Schalter & Achse nehmen 100 % der Federkraft auf (Mikroschalter-Auslösung als reiner Nebeneffekt), konzentrische Labyrinth-Dichtung über der Nabe, $90^\circ$-eckig geöffneter distaler Unterrand bis zur Unterkante.
    * **Verstärkter Bionischer Tarsus & Schlanker Kufenschuh:** Gerader, ab der Pivot-Achse um $+20\,\%$ verstärkter Schaft ($6{,}68\,\text{g}$ PETG, $5{,}60\,\text{mm}$ flach druckbar), kompakter nach außen gekrümmter Kufenfuß mit schlankem Formschluss-Schuh (`tarsus_shoe.FCStd`, $8{,}60\,\text{mm}$ breit, $1{,}52\,\text{g}$), integrierter gefaster Federführungsstift ($\varnothing 2{,}90 \times 3{,}20\,\text{mm}$), effektive Knie-Sohlen-Länge $152{,}6\,\text{mm}$.
    * **Verifikation:** $0{,}0000\,\text{mm}^3$ Kollisionen über alle Baugruppen und den gesamten $0{,}0^\circ\text{--}+5{,}0^\circ$ Hub-Sweep; 2nd-Order `C3D10` CalculiX-FEA bestanden (Tibia $S \ge 3{,}58$ selbst bei $25\,\text{N}$ Querstoß / Tropfenfenster $S = 25{,}0$ im Tripod; Tarsus $S = 4{,}57$ im Tripod-Stoß, $S_{\text{Schaft}} = 2{,}24$ bei $35\,\text{N}$ Extremstoß).
- [x] **Fußsensor-Integration (Omron D2FC-F-K Mikroschalter):**  
  * Vollständig parametrisiert und im kinematischen Hub-Sweep ($0{,}0^\circ$ bis $+5{,}0^\circ$) ohne Kollisionen verifiziert.
- [x] **Kabelkanal Fußsensor $\rightarrow$ Kniegelenk:**  
  * Interner $C^2$-glatter B-Spline-Kabelkanal ($\varnothing 2{,}40\,\text{mm}$ auf $Z = 8{,}20\,\text{mm}$) führt geschützt oberhalb des Tropfenfensters zum Knie-U-Ausschnitt.

---

## 4. Assemblies (`leg_assembly.FCStd` & `body_assembly.FCStd`)

- [ ] **Validierung der Gegenlager-Umkehrung (Option A: Invertiertes Gegenlager):**  
  * **Fragestellung:** Überprüfen, ob das Umkehren der Gegenlagerpositionierung in der Praxis erfolgreich sein wird.
  * **Konzept Option A:**
    * Die M4-Mutter (flache DIN 439) sitzt innenliegend in einer Sechskanttasche der Coxa Bracket.
    * Das Kugellager (684ZZ, $\varnothing 8 \times 3\,\text{mm}$) wird von außen in die hintere Femur-Wange eingepresst.
    * Die M4-Senkkopfschraube wird von außen durch das Lager eingedreht.
  * **Prüfpunkte beim ersten Montage- und Belastungstest:**
    * *Radiale Montage:* Lässt sich der Femur mit aufgepresstem Servohorn ohne axiales Spreizen der Gabel reibungslos in die Coxa-Halterung einschieben?
    * *Drehmomentsicherung:* Hält die gedruckte SW 7.10 mm Sechskanttasche die DIN 439 Flachmutter beim Festziehen der M4-Schraube verdrehsicher fest?
    * *Axiales Lagerspiel & Freilauf:* Gewährleistet der Bundkragen ($R = 3.30\,\text{mm}$) und die 0.3 mm Passscheibe, dass nur der Innenring des Kugellagers geklemmt wird und das Gelenk leichtgängig dreht?
    * *Biegesteifigkeit unter Last:* Verzieht sich die Gegenlagerlasche bei dynamischer Gehbelastung, oder nimmt das 45°-Gusset die Axial- und Biegemomente steif auf?
- [x] **Bewegungsraum- und Kollisionsprüfung:**  
  * **Verifiziert via [`check_workspace_collisions.py`](../../../../../scripts/dev/check_workspace_collisions.py)** im echten 3D-B-Rep über die komplette Kinematikkette:
    * **Hüfte (Femur Pitch):** Kollisionsfrei über `[-95°, +95°]`.
    * **Knie (Tibia Bend):** Kollisionsfrei über `[+19°, +122°]` (`103°` Hub; Software-Limits in [`config.yaml`](../../../../../software/lasius-core/src/lasius/core/config.yaml) mit `3°` Sicherheitsabstand auf `[-68°, +29°]` abgesichert).
    * **Coxa-Yaw vs. Chassis (Canopy, Belly Pan, Core, Carbonplatten):** `FL [-61°, +65°]`, `ML/RL [-65°, +65°]` über Stance, HighLift (`+50°`) und LowReach (`-30°`).
    * **Nachbarbeine (`FL↔ML`, `ML↔RL`):** Kollisionsfrei bis `±26°` gleichzeitig gegenläufig (`52°` Relativwinkel) → Coxa-Softlimits auf `-25°..+25°` (`FL/FR` `+35°` nach vorn für `WAVE_HELLO`) abgesichert.
- [ ] **Generations-Vererbung & Link-Integrität (Chassis-Platten-Invariante):**  
  * **Hardware-Freeze:** Die beiden $2{,}0\,\text{mm}$ CFK-Carbonplatten ([`body_bottom.FCStd`](../../custom/v1/parts/body_bottom.FCStd) und [`body_top.FCStd`](../../custom/v1/parts/body_top.FCStd)) **existieren bereits als physische, fertig gefräste Hardware** und sind das **einzige Bauteil, das unverändert aus Generation `v1` in `v2` übernommen wird**.
  * Alle anderen v1-Eigenkonstruktionen (v1-Beine, v1-Spacers) sind obsolet und werden durch v2-Monolithe ersetzt.
  * Sämtliche Neukonstruktionen (Monocoque-Kern, Belly Pan, Canopy, Montageblöcke) müssen sich zwingend an das bestehende Kontur- und Bohrungsraster der physischen Carbonplatten anpassen (`check_links.py` und FreeCAD XLink-Check).

---

## 5. Nomenklatur & Refactoring

- [x] ~~**Umbenennung `hardware/` $\rightarrow$ `cots/` (Beseitigung der Pfad-Verdopplung):**~~ **[ERLEDIGT]**  
  * **Umgesetzt:** `hardware/mechanics/models/hardware/` wurde zu `hardware/mechanics/models/cots/` umbenannt (harmonisches Begriffspaar `cots/` vs. `custom/`).
  * **Zielstruktur verifiziert:**
    * CAD-Modelle: `hardware/mechanics/models/cots/`
    * Fertigungsexporte: `hardware/mechanics/export/{step,stl}/cots/`
  * **Erfolgreich migriert:**
    * CAD-Generatoren in `hardware/mechanics/scripts/{v1,v2}/`: `hw_dir = .../cots`
    * Re-Generierung aller v1- und v2-Assemblies (`leg_assembly.FCStd`, `body_assembly.FCStd`) mit aktualisierten internen `App::Link`-Pfaden und Neu-Export aller STEP/STL-Dateien.
    * Dokumentation und Richtlinien aktualisiert: [`hardware/mechanics/README.md`](../../../../mechanics/README.md) und [`AGENTS.md`](../../../../../AGENTS.md).

---

## 6. Biomimetische Module & Aktuatoren (Kopf & Hinterleib – Lynxmotion A-Pod Adaption)

- [x] ~~**A-Pod Gaster modellieren (Platten-Sandwich-Hinterleib & 2-DoF Gimbal):**~~ **[ERLEDIGT]**  
  * **Modelle & Generatoren:** [`apod_tail_mount.FCStd`](parts/gaster/apod_tail_mount.FCStd), [`apod_tail_bracket.FCStd`](parts/gaster/apod_tail_bracket.FCStd), [`apod_gaster.FCStd`](parts/gaster/apod_gaster.FCStd) und [`gaster_assembly.FCStd`](gaster_assembly.FCStd) generiert via [`generate_gaster_assembly.py`](../../../scripts/v2/generate_gaster_assembly.py).
  * **Status:** Vollständig umgesetzt im originalgetreuen Lynxmotion A-Pod Kit-Design (Kåre Halvorsen / *Zenta*) als 2-DoF Platten-Sandwich-Hinterleib (Länge $117{,}0\,\text{mm}$, Breite $96{,}0\,\text{mm}$, $X \in [-148{,}0, -265{,}0\,\text{mm}]$).
  * **Chassis-Interface über Spacer-Bohrungen:**
    * Montageblock ([`apod_tail_mount.FCStd`](parts/gaster/apod_tail_mount.FCStd)) überbrückt den $51{,}30\,\text{mm}$ Chassis-Spalt und verankert starr über die beiden hinteren M3-Bohrungen auf der Längsachse ($X = -90{,}0\,\text{mm}$ und $X = -120{,}0\,\text{mm}$).
    * 2-DoF SES-Gimbal ([`apod_tail_bracket.FCStd`](parts/gaster/apod_tail_bracket.FCStd)) mit Standard-Servos (Hitec HS-645MG / Torcster NR-645): Pan (Gieren links/rechts $\pm 45^\circ$) und Tilt (Nicken heben/senken $\pm 35^\circ$).
    * Konturierte Ober- und Unterplatten ($2{,}5\,\text{mm}$ Carbon) mit 4× Distanzbolzen und T-Schubstegen (großzügiger Innenraum für Zusatzakku oder Telemetrie).
  * **Integration:** Eingebunden in die erweiterte Master-Assembly [`lasius_assembly.FCStd`](lasius_assembly.FCStd).

- [x] ~~**A-Pod Kopf- & Mandibeln-Baugruppe (5-DoF Bionik-Kopf & massive 3D-Sandwich-Mandibeln):**~~ **[ERLEDIGT]**  
  * **Modelle & Generatoren:** [`apod_head_mount.FCStd`](parts/head/apod_head_mount.FCStd), [`apod_neck_bracket.FCStd`](parts/head/apod_neck_bracket.FCStd), [`apod_head_platform.FCStd`](parts/head/apod_head_platform.FCStd), [`apod_mandible_left.FCStd`](parts/head/apod_mandible_left.FCStd), [`apod_mandible_right.FCStd`](parts/head/apod_mandible_right.FCStd) und [`head_assembly.FCStd`](head_assembly.FCStd) generiert via [`generate_head_assembly.py`](../../../scripts/v2/generate_head_assembly.py).
  * **Status:** Vollständig umgesetzt in der originalgetreuen Lynxmotion/Zenta A-Pod 5-DoF Architektur mit 5 Standard-Servos (HS-645MG):
    * 3-DoF Hals: Pan (Gieren Z), Tilt (Nicken Y) und Roll (Rollen X).
    * Kopf-Plattform ([`apod_head_platform.FCStd`](parts/head/apod_head_platform.FCStd)): Bionisches Kopfchassis mit getrennter Aufnahme für linkes und rechtes Mandibel-Servo (`cMandLeftPin`, `cMandRightPin`) sowie Facettenaugen-Ports.
    * Massive 3D-Sandwich-Mandibeln ([`apod_mandible_left.FCStd`](parts/head/apod_mandible_left.FCStd), [`apod_mandible_right.FCStd`](parts/head/apod_mandible_right.FCStd)): $134\,\text{mm}$ Länge, $120\,\text{mm}$ Ausladung vor Drehpunkt, $Y = \pm 68\,\text{mm}$ Spannweite, 4 gezahnte Greifspitzen, Carbon-Doppelplatten mit 4 Distanzbolzen und Weather-Stripping-Führung.
  * **Chassis-Interface über Spacer-Bohrungen:**
    * Montageblock ([`apod_head_mount.FCStd`](parts/head/apod_head_mount.FCStd)) überbrückt den $51{,}30\,\text{mm}$ Spalt und verankert starr über die beiden vorderen M3-Bohrungen ($X = 128{,}0\,\text{mm}, Y = \pm 12{,}0\,\text{mm}$) mit Tasche für das Pan-Servo.
  * **Integration:** Eingebunden in die Master-Assembly [`lasius_assembly.FCStd`](lasius_assembly.FCStd).

---

## 7. Chassis & Elektronik-Integration

- [x] ~~**Elektronik-Basisplatte (Zentrales Montage-Deck / Tray):**~~ **[ERLEDIGT]**  
  * **Modell & Generator:** [`electronics_tray.FCStd`](parts/electronics_tray/electronics_tray.FCStd) generiert via [`generate_electronics_tray.py`](../../../scripts/v2/generate_electronics_tray.py).
  * **Status:** Zentrales Trägerdeck im Chassis-Kern auf $Z = 18{,}0\,\text{mm}$ (gehalten von 4 Standoff-Kragenbuchsen $\varnothing 14{,}2\,\text{mm}$ an den Spacern bei $X = \pm 45, Y = \pm 30$).
  * **Funktion & Integration:**
    * 2× PCA9685 16-Kanal Servo-Controller ($56 \times 19\,\text{mm}$ Lochbild links bei $Y = +14{,}5\,\text{mm}$, rechts bei $Y = -14{,}5\,\text{mm}$ auf $3{,}0\,\text{mm}$ Sockeln; 90°-Stiftleisten zeigen seitlich nach außen zu den Beinen mit $2{,}0\,\text{mm}$ Sicherheitsabstand zu den Coxa-Servos).
    * 1× TCA9548A 8-Kanal I2C-Multiplexer ($26\,\text{mm}$ Lochbild auf der Mittelachse bei $X = -52, Y = 0$).
    * 4× Kabelbinder-Ösen und frontseitiges Verkabelungs- und Akkufenster.
    * Vollständig kollisionsfrei mit Spacern, Beinen und Coxa-Servos.
    * Eingebunden in Subassembly [`electronics_tray_assembly.FCStd`](electronics_tray_assembly.FCStd) und Master-Assembly [`body_assembly.FCStd`](body_assembly.FCStd).
- [x] ~~**Chassis-Abdeckung / Exoskelett-Haube (Top Cover):**~~ **[ERLEDIGT]**  
  * **Modell & Generator:** [`chassis_top_cover.FCStd`](parts/chassis/chassis_top_cover.FCStd) generiert via [`generate_chassis_top_cover.py`](../../../scripts/v2/generate_chassis_top_cover.py).
  * **Status:** Aerodynamische Chitinpanzer-Haube auf der oberen Carbonplatte ($Z = 55{,}3\,\text{mm}$ bis $76{,}0\,\text{mm}$, Gesamthöhe $20{,}7\,\text{mm}$ mit $18{,}5\,\text{mm}$ Innenraum-Freiraum), verschraubt über die 4 zentralen M3-Standoff-Pfeiler bei $X = \pm 45, Y = \pm 30$ mit gesenkten Taschen.
  * **Funktion & Konstruktion:**
    * Mechanischer Schutz für den auf der oberen Chassis-Platte montierten Raspberry Pi 4 Model B, GPIO-Leitungen und interne Elektronik mit vollständiger Kollisionsfreiheit.
    * **Chevron-Louvers:** 5× $45^\circ$ nach vorn gepfeilte Lüftungsschlitze bei $X \in [25{,}0\dots 55{,}0\,\text{mm}]$ direkt über dem Pi 4 SoC zur passiven Kamin-Konvektionskühlung.
    * **Kamera-Kabeldurchbruch:** $20 \times 3{,}2\,\text{mm}$ Frontschlitz an der Schnauze ($X \in [82\dots 94\,\text{mm}]$) zur direkten Durchführung des CSI-Kamerakabels zum Kopfmodul.
    * Vollständig eingebunden in Master-Assembly [`body_assembly.FCStd`](body_assembly.FCStd).
- [x] ~~**Unterboden-Abdeckung (Chassis Belly Pan / Skid Plate):**~~ **[ERLEDIGT]**  
  * **Modell & Generator:** [`chassis_belly_pan.FCStd`](parts/chassis/chassis_belly_pan.FCStd) generiert via [`generate_chassis_belly_pan.py`](../../../scripts/v2/generate_chassis_belly_pan.py).
  * **Status:** Schutz- und Gleitwanne an der Chassis-Unterseite ($Z \le 0{,}0\,\text{mm}$), verschraubt über die 4 zentralen M3-Standoff-Pfeiler bei $X = \pm 45, Y = \pm 30$ mit 90°-Senkungen nach DIN 7991.
  * **Funktion & Konstruktion:**
    * Glatte Bootsrumpf-Kontur mit 30°-Anlaufschrägen an Front und Heck sowie Längskufen für widerstandsloses Gleiten über Hindernisse.
    * $7{,}6\,\text{mm}$ tiefe Innenwanne zur Aufnahme von Akkuleitungen und Sensorverkabelung unterhalb der unteren Carbonplatte.
    * **Integrierte Aufnahme für 9-Feld-Bodenscanning-Sensor:**
      * Dedizierte Montageaufnahme und $10 \times 8\,\text{mm}$ optischer Durchbruch mit $45^\circ$-FoV-Fase für den nach unten blickenden Multi-Zonen-Sensor ($3 \times 3$ ToF, VL53L5CX/VL53L7CX) bei $X = 0, Y = 0$.
      * $1{,}5\,\text{mm}$ tiefer Schutzkragen an der Unterseite gegen Verkratzen der Optik.
      * 4× M2 Schraubsockel ($21 \times 13\,\text{mm}$ Lochbild) und Kabeldurchführungsschacht ins Chassis.
    * Vollständig eingebunden in Master-Assembly [`body_assembly.FCStd`](body_assembly.FCStd).
- [x] ~~**COTS Elektronik- & Platinenmodelle (Solid-CAD in `models/cots/`):**~~ **[ERLEDIGT]**  
  * **Modelle & Generator:** Parametrische B-Rep Modelle generiert via [`generate_electronics_cots.py`](../../../scripts/cots/generate_electronics_cots.py):
    * [`rpi4_model_b.FCStd`](../../cots/rpi4_model_b.FCStd): Raspberry Pi 4 Model B mit BCM2711 SoC, USB/Ethernet-Ports, 40-Pin GPIO-Leiste und MicroSD-Slot (Signalgrün).
    * [`pca9685_board.FCStd`](../../cots/pca9685_board.FCStd): 16-Kanal PWM Servo-Controller mit Klemmenblock, Elko, aufrechten I2C-Headern und $90^\circ$-gewinkelten 3×16 Servo-Stiftleisten nach Referenzfoto (Adafruit-Blau).
    * [`tca9548a_board.FCStd`](../../cots/tca9548a_board.FCStd): TCA9548A 8-Kanal I2C-Multiplexer Breakout mit Dual-Stiftleisten (Signalviolett).
    * [`vl53l5cx_board.FCStd`](../../cots/vl53l5cx_board.FCStd): VL53L5CX 9-Zonen ToF Distanzsensor mit optischem Linsengehäuse und I2C-Header (SparkFun-Rot).
    * [`battery_lipo_2s.FCStd`](../../cots/battery_lipo_2s.FCStd): 2S 7.4V LiPo Flat-Pack ($88 \times 35 \times 14\,\text{mm}$) mit 12AWG Silikonleitungen, XT60-Stecker und JST-XH Balancer-Stecker (Signalgold/Gelb).
    * [`ads1115_board.FCStd`](../../cots/ads1115_board.FCStd): ADS1115 16-Bit 4-Kanal I2C AD-Wandler Breakout (Adafruit-Blau).
  * **Digital Fabrication Exporte:** Synchronisierte STEP- und STL-Dateien in `hardware/mechanics/export/{step,stl}/cots/`.
- [x] ~~**Elektronik- & Akku-Zwischenbaugruppe (Subassembly `electronics_tray_assembly.FCStd`):**~~ **[ERLEDIGT]**  
  * **Modell & Generator:** [`electronics_tray_assembly.FCStd`](electronics_tray_assembly.FCStd) generiert via [`generate_electronics_tray_assembly.py`](../../../scripts/v2/generate_electronics_tray_assembly.py).
  * **Status:** Modulare Innenraum-Baugruppe auf $Z = 18{,}0\,\text{mm}$ zur Entlastung des Master Body Assemblys.
  * **Farbkodierung zur visuellen Unterscheidbarkeit:**
    * **Tray-Grundkörper:** Technisches Blau `(0.12, 0.35, 0.65)`
    * **PCA9685 PWM Controller (links & rechts):** Signalblau `(0.04, 0.38, 0.88)`
    * **TCA9548A I2C-Multiplexer:** Signalviolett `(0.58, 0.15, 0.75)`
    * **2S LiPo-Akku:** Signalgold / Gelb `(0.95, 0.75, 0.10)` im Untergeschoss unter dem Tray-Deck ($Z = 3{,}0\dots 17{,}0\,\text{mm}$ World).
  * **Integration in Master Body Assembly v2:** Als einheitliche Baugruppe via `App::Link` in [`body_assembly.FCStd`](body_assembly.FCStd) referenziert. Raspberry Pi 4 sitzt auf dem Oberdeck bei $Z = 55{,}3\,\text{mm}$ unter der Chitin-Haube. STEP- und STL-Exporte synchronisiert.
- [x] ~~**Service-Abdeckung mit '>>>' Chevrons & Raspberry Pi 4 Montageplatte im Canopy:**~~ **[ERLEDIGT]**  
  * **Modelle & Generatoren:**
    * Raspberry Pi 4 Montageplatte: [`chassis_rpi_mount.FCStd`](parts/chassis/chassis_rpi_mount.FCStd) generiert via [`generate_chassis_rpi_mount.py`](../../../scripts/v2/generate_chassis_rpi_mount.py).
    * Service-Abdeckung: [`chassis_service_cover.FCStd`](parts/chassis/chassis_service_cover.FCStd) generiert via [`generate_chassis_service_cover.py`](../../../scripts/v2/generate_chassis_service_cover.py).
    * Erhöhtes Plexiglas-Canopy mit Service-Ausschnitt: [`chassis_canopy.FCStd`](parts/chassis/chassis_canopy.FCStd) generiert via [`generate_chassis_canopy.py`](../../../scripts/v2/generate_chassis_canopy.py).
  * **Funktion & Konstruktion (Zentrierte Ausrichtung zwischen den 4 mittleren Bohrungen):**
    * **1. Raspberry Pi 4 Positionierung & Montageplatte (`chassis_rpi_mount.FCStd`):**
      * Der Raspberry Pi 4 Model B sitzt symmetrisch zentriert bei $X = 0{,}0\,\text{mm}, Y = 0{,}0\,\text{mm}, Z = 59{,}80\,\text{mm}$ exakt zwischen den 4 zentralen Chassis-Bohrungen bei $(\pm 45{,}0, \pm 30{,}0\,\text{mm})$.
      * 4× M3 Senkschrauben bei $X = \pm 45{,}0\,\text{mm}, Y = \pm 30{,}0\,\text{mm}$ verankern die Trägerplatte starr im Zentralkern (`chassis_core`).
      * 4× integrierte Sockeldome ($\varnothing 6{,}4\,\text{mm}$, Höhe $2{,}5\,\text{mm}$) im $58 \times 49\,\text{mm}$ Lochbild ($X = \pm 29{,}0, Y = \pm 24{,}5\,\text{mm}$) mit M2.5-Gewindeeinsatztaschen.
      * Unterseitige Kabeltasche ($44 \times 36\,\text{mm}$) für Flachbandkabel (CSI-Kamera, DSI) und Kühlluftzirkulation aus dem Chassis-Innenraum.
    * **2. Zentrierte Service-Abdeckung (`chassis_service_cover.FCStd`):**
      * Abnehmbarer Wartungsdeckel direkt über dem Raspberry Pi 4 in gleicher Länge ($89{,}0\,\text{mm}$, $X \in [-43{,}5, +45{,}5\,\text{mm}]$) und Breite ($57{,}0\,\text{mm}$, $Y \in [-28{,}5, +28{,}5\,\text{mm}]$).
      * Schließt bündig an die Kappenkontur an ($Z_{\text{rebate}} = 80{,}20\,\text{mm}$ bis $Z_{\text{apex}} = 85{,}00\,\text{mm}$).
      * **Bionische abgerundete '>>>' Chevron-Kaminbelüftung:** 5× $45^\circ$ nach vorn gepfeilte Lamellenschlitze mit verrundeten Pillen-/Kapselenden identisch zur Konstruktion im Femur-Deckel ([`generate_femur.py`](../../../scripts/v2/generate_femur.py)) über dem BCM2711 Quad-Core SoC zur passiven Kamin-Konvektionskühlung ($X \in [-15{,}0, +15{,}0\,\text{mm}]$).
      * $6{,}3\,\text{mm}$ vertikale Kopffreiheit über den höchsten Pi 4 USB/Ethernet-Ports ($Z = 77{,}20\,\text{mm}$).
    * **3. Erhöhtes Plexiglas-Canopy mit zentrierter Service-Öffnung (`chassis_canopy.FCStd`):**
      * Loft-Apex bei **$Z = 81{,}50\,\text{mm}$**, symmetrisch zentriert um $X = 0, Y = 0$.
      * Zentrierter Durchbruch ($X \in [-41{,}8, +43{,}8\,\text{mm}], Y \in [-26{,}8, +26{,}8\,\text{mm}]$) und Stufenfalz ($X \in [-43{,}8, +45{,}8\,\text{mm}], Z \ge 80{,}20\,\text{mm}$) mit $0{,}2\,\text{mm}$ Fügespiel für die Service-Abdeckung.
      * Kollisionsprüfung mit Montageplatte, Pi 4 und Service-Deckel: Exakt $0{,}0000\,\text{mm}^3$ Schnittvolumen across all parts.
  * **Integration:** Vollständig eingebunden via `App::Link` in [`body_assembly.FCStd`](body_assembly.FCStd) und [`lasius_assembly.FCStd`](lasius_assembly.FCStd).

- [x] ~~**Organische Neugestaltung der oberen Chassis-Abdeckung & Plexiglas-Canopy:**~~ **[ERLEDIGT]**  
  * **Modelle & Generatoren:**
    * Innere Elektronikhaube: [`chassis_top_cover.FCStd`](parts/chassis/chassis_top_cover.FCStd) generiert via [`generate_chassis_top_cover.py`](../../../scripts/v2/generate_chassis_top_cover.py).
    * Drapierte Plexiglas-Haube (Revision 1): [`chassis_canopy.FCStd`](parts/chassis/chassis_canopy.FCStd) generiert via [`generate_chassis_canopy.py`](../../../scripts/v2/generate_chassis_canopy.py).
  * **Status:** 2-teilige Thorax-Abdeckung bestehend aus innerem Elektronikgehäuse und äußerer transparenter Tiefziehkappe (Revision 1):
  * **1. Chassis Canopy (`chassis_canopy.FCStd` – Drapierte Acrylhaube Revision 1):**
    * **Organische Doppelkrümmung:** Stufen- und knickfreie Loft-Oberfläche von $Z = 76{,}00\,\text{mm}$ (Apex) herab auf $Z = 55{,}30\,\text{mm}$, die sich wie eine warm geformte $1{,}50\,\text{mm}$ Plexiglasplatte harmonisch über das zentrale Top Cover schmiegt.
    * **Randbeschnitt:** 100 % bündig mit der 24-Kanten-Außenkontur von [`body_top.FCStd`](../../custom/v1/parts/body_top.FCStd) ($X \in [-132{,}0, +135{,}0]\,\text{mm}$, $Y \in [-88{,}5, +88{,}5]\,\text{mm}$).
    * **Lochbild:** 4× M3 Zentralkern ($X = \pm 45, Y = \pm 30$), 1× Heck ($X = -90, Y = 0$), 2× Front ($X = 128, Y = \pm 12$).
    * **Optik:** 55 % Transparenz mit zartem Eisblau-Glanz (`(0.85, 0.92, 0.98)`).
  * **2. Chassis Top Cover (`chassis_top_cover.FCStd` – Inneres Strukturgehäuse):**
    * Kompaktes anthrazitfarbenes 3D-Druck-Gehäuse ($X \in [-88{,}0, 92{,}0]\,\text{mm}$, $Y \in [-35{,}0, 35{,}0]\,\text{mm}$, $Z \in [55{,}30, 74{,}50]\,\text{mm}$) unter der Plexiglashaube.
    * 4 integrierte Montage-Sockeldome ($\varnothing 6{,}0\,\text{mm}$) für Raspberry Pi 4 im $58 \times 49\,\text{mm}$ Lochbild.
    * 5× $45^\circ$ nach vorn gepfeilte Chevron-Kaminbelüftungsschlitze über dem SoC.
    * 4× M3 Senkschrauben bei $X = \pm 45, Y = \pm 30\,\text{mm}$ (in den Zentralkern).
  * **Integration:** Beide Teile als separate Komponenten via `App::Link` in [`body_assembly.FCStd`](body_assembly.FCStd) und [`lasius_assembly.FCStd`](lasius_assembly.FCStd) eingebunden.

- [x] ~~**Konzeptstudie & Realisierung: Monolithischer Chassis-Kern / Kapselung als Ersatz der 4 mittleren Spacer:**~~ **[ERLEDIGT]**  
  * **Modelle & Generatoren:** [`chassis_core.FCStd`](parts/chassis/chassis_core.FCStd) und [`chassis_core_assembly.FCStd`](chassis_core_assembly.FCStd) generiert via [`generate_chassis_core.py`](../../../scripts/v2/generate_chassis_core.py).
  * **Status:** Vollständig umgesetzter 3D-Druck-Sandwich-Stützkern ($51{,}3\,\text{mm}$ Bauhöhe zwischen $Z = 2{,}0$ und $53{,}3\,\text{mm}$), der die 4 mittleren Kunststoff-Spacer bei $X = \pm 45, Y = \pm 30\,\text{mm}$ durch eine steife, vibrationsdämpfende Schubsteg-Monocoque-Struktur ersetzt.
  * **Integrierte Kapselung:**
    * Vertikale Führungsschienen für 2× PCA9685 PWM-Controller (Stiftleisten ragen kollisionsfrei nach oben $+Z$ in den Wartungsschacht).
    * LiPo-Akkutunnel im Untergeschoss ($Z \in [1{,}5\dots 16{,}5\,\text{mm}]$) für 2S Flat-Pack.
    * TCA9548A I2C-Multiplexer-Kammer im Heckbereich.
    * Formschluss-Zentrierfalze und horizontale M3 Ruthex-Schnittstellen zu Front (`chassis_neck`) und Heck (`chassis_tail`).
    * $16\,\text{mm}$ Taillierungs-Freigang zu den mittleren Coxa-Servos ML und MR.
  * **Integration:** Eingebunden in [`lasius_assembly.FCStd`](lasius_assembly.FCStd).

- [ ] **Chassis-Core-Monocoque Evolution: Vollständige Bodenabdeckung, flexibler Akkutunnel & Schwenkbereichs-Morphologie:**  
  * **Hintergrund & Motivation:**
    * Die Montageöffnung in der unteren Carbon-Bodenplatte ([`body_bottom.FCStd`](../../custom/v1/parts/body_bottom.FCStd)) misst $160{,}0 \times 50{,}0\,\text{mm}$ ($X \in [-80{,}0, +80{,}0]\,\text{mm}, Y \in [-25{,}0, +25{,}0]\,\text{mm}$). Der bisherige Kern ($X \in [-56{,}0, +54{,}0]\,\text{mm}$) deckt diesen Bereich nur teilweise ab.
    * Die endgültige Akku-Größe und -Zellchemie (z. B. 2S/3S LiPo Flat-Pack oder 18650/21700 Li-Ion Rundzellen) steht noch nicht final fest. Der Bauraum unterhalb der beiden vertikalen PCA9685-Controller muss daher maximal genutzt werden.
  * **Konstruktive Anforderungen:**
    1. **Vollständige Abdeckung der Bodenplatte:**
       * Das Monocoque wird an seiner Basis auf mindestens $X \in [-80{,}0, +80{,}0]\,\text{mm}$ und $Y \in [-25{,}0, +25{,}0]\,\text{mm}$ erweitert, sodass die gesamte $160 \times 50\,\text{mm}$ Öffnung in `Body_Bottom` staub- und schmutzdicht geschlossen wird.
       * Formschlüssiger Übergang zur Unterboden-Schutzwanne ([`chassis_belly_pan.FCStd`](parts/chassis/chassis_belly_pan.FCStd)).
    2. **Durchgehender, axial einschiebbarer Akkutunnel:**
       * Der Hohlraum unterhalb der beiden vertikalen PCA9685-Platinen wird zu einem durchgehenden Längstunnel ($L \ge 160\,\text{mm}$) ausgebaut.
       * Ermöglicht das axiale Einschieben variabler Akku-Packs von Front oder Heck mit integrierter Zugentlastung und Kabeldurchführung.
    3. **Verschiebung / Erweiterung der Kopf- und Gaster-Schnittstellen:**
       * Der Kernkörper wächst in X-Richtung nach vorn und hinten:
         * *Front:* Anbindung an den Hals-Montageblock ([`apod_head_mount.FCStd`](parts/head/apod_head_mount.FCStd)) wird strukturell nach vorn versetzt / integriert.
         * *Heck:* Anbindung an den Petiolus-Montageblock ([`apod_tail_mount.FCStd`](parts/gaster/apod_tail_mount.FCStd)) wird strukturell nach hinten versetzt / integriert.
    4. **Bionische Rumpf-Morphologie um die Coxa-Schwenkbereiche:**
       * Die Außenkontur des Monocoques folgt den realen Schwenkbereichen ($\pm 45^\circ\text{--}\pm 60^\circ$) aller 6 Coxa-Servos (FL, ML, RL, FR, MR, RR) unter Einhaltung eines Sicherheitsabstands ($\ge 2{,}5\text{--}3{,}0\,\text{mm}$).
       * Maximierung des Innenvolumens bei garantierter Kollisionsfreiheit ($0{,}0000\,\text{mm}^3$).
  * **Betroffener Code:** [`generate_chassis_core.py`](../../../scripts/v2/generate_chassis_core.py), [`generate_chassis_core_assembly.py`](../../../scripts/v2/generate_chassis_core.py), [`body_assembly.FCStd`](body_assembly.FCStd).

---

## 8. FEM-Strukturanalyse & Topologieoptimierung (Simulation-Driven Design)

- [x] ~~**FE-Lastfall-Definition & Automatisierte Baseline-FEA (CalculiX & Gmsh):**~~ **[ERLEDIGT]**  
  * **Status:** Erfolgreich implementiert via [`fea_femur_baseline.py`](../../../../../scripts/dev/fea_femur_baseline.py) und im FreeCAD-Headless-Runner über alle 3 Lastfälle berechnet.
  * **Lastfälle & Quantitative Baseline-Ergebnisse (Femur Solid $82{,}02\,\text{g}$ / $64{,}59\,\text{cm}^3$):**
    1. *LF1 (Tripod Gait Vertikalbiegung, $F_z = -15{,}0\,\text{N}$):* $\sigma_{\text{max}} = 1{,}38\,\text{MPa}$, $u_{\text{max}} = 0{,}198\,\text{mm}$, Sicherheitsfaktor $S = 32{,}58$, $100\,\%$ des Volumens unter $5\,\text{MPa}$.
    2. *LF2 (Knie-Servo Blockiermoment, $M_{\text{stall}} = 1{,}2\,\text{N}\cdot\text{m} \rightarrow F_t = 120\,\text{N}$):* $\sigma_{\text{max}} = 11{,}05\,\text{MPa}$, $u_{\text{max}} = 1{,}586\,\text{mm}$, Sicherheitsfaktor $S = 4{,}07$, $94{,}3\,\%$ des Volumens unter $5\,\text{MPa}$.
    3. *LF3 (Laterale Hangquerung, $F_y = +10{,}0\,\text{N}$):* $\sigma_{\text{max}} = 0{,}92\,\text{MPa}$, $u_{\text{max}} = 0{,}132\,\text{mm}$, Sicherheitsfaktor $S = 48{,}90$, $100\,\%$ des Volumens unter $5\,\text{MPa}$.
  * **Erkenntnis:** Überragendes Leichtbaupotenzial (Massenreduktion um $\ge 40\text{--}50\,\%$ von $82\,\text{g}$ auf $\sim 42\text{--}48\,\text{g}$ bei Beibehaltung von $S \ge 2{,}0$).
  * **Ergebnisdaten:** In-Tree FEA-Modelle und Netze abgelegt unter `hardware/mechanics/export/fea/femur_baseline/`.

- [x] ~~**Topologieoptimierung des Femur-Knochens (`femur.FCStd` – Pilot-Projekt):**~~ **[ERLEDIGT]**  
  * **Status:** Vollständig umgesetzt in [`generate_femur.py`](../../../scripts/v2/generate_femur.py), verifiziert via [`fea_femur_verification.py`](../../../../../scripts/dev/fea_femur_verification.py) und dokumentiert im [**Femur FEA-Topologieoptimierungsbericht**](../../../../../docs/hardware/femur_topology_optimization_report.md). In alle Master-Assemblies synchronisiert.
  * **Bionische Leichtbau-Architektur:**
    1. *Wangen-Fachwerkfenster:* Transformation der flachen $1{,}8\,\text{mm}$ Blindtaschen in lastpfadoptimierte, durchgehende $45^\circ$-Fachwerkfenster und Halbmond-Taschen hinter den Lagern ($w \ge 2{,}50\,\text{mm}$, $R = 1{,}80\,\text{mm}$); Gurte auf $Z = \pm 10{,}2\,\text{mm}$ verstärkt.
    2. *Flanken-Warren-Gitter:* 5-Feld-Warren-Fachwerk ($45^\circ$-Chevrons) in den massiven Flanken bei durchgehend gekapselter, staubdichter ADS1115-Kammerinnenwand ($1{,}35\text{--}2{,}0\,\text{mm}$ PETG-Wand).
    3. *Stirnwand-Taschen (Bulkheads):* $5{,}5\,\text{mm}$ tiefe bionische Entlastungstaschen an den Stirnwänden zu den U-Mäulern beiderseits der Kabeltunnels.
    4. *Unterboden-Aussparungen:* Bionische Waben- und Rillenstrukturen im massiven Bodenblock ($Z \le -10{,}0\,\text{mm}$) unter Beibehaltung eines durchgehenden $1{,}5\,\text{mm}$ Schutzbodens unter dem ADC.
  * **Quantitative FEA-Verifikationsergebnisse (CalculiX & Gmsh, 78.700 Tetraeder-Elemente):**
    * **Masse:** Reduktion von $82{,}02\,\text{g}$ auf **$64{,}08\,\text{g}$** ($50{,}46\,\text{cm}^3$, **$-17{,}94\,\text{g}$ / $-21{,}9\,\%$ Leichtbau-Delta**).
    * *LF1 (Tripod Gait, $F_z = -15\,\text{N}$):* $\sigma_{\text{max}} = 2{,}06\,\text{MPa}$, $u_{\text{max}} = 0{,}258\,\text{mm}$, Sicherheitsfaktor **$S = 21{,}89$**.
    * *LF2 (Servo Stall Torque $1{,}2\,\text{N}\cdot\text{m}$, $F_t = 120\,\text{N}$):* $\sigma_{\text{max}} = 16{,}53\,\text{MPa}$, $u_{\text{max}} = 2{,}060\,\text{mm}$, Sicherheitsfaktor **$S = 2{,}72$** (Soll $S \ge 2{,}0$ souverän übertroffen!).
    * *LF3 (Laterale Querlast, $F_y = +10\,\text{N}$):* $\sigma_{\text{max}} = 1{,}38\,\text{MPa}$, $u_{\text{max}} = 0{,}172\,\text{mm}$, Sicherheitsfaktor **$S = 32{,}59$**.
  * **Kollisions- & Schnittstellenprüfung:** 100 % kollisionsfrei ($0{,}0000\,\text{mm}^3$) in `leg_assembly.FCStd`, `leg_right_assembly.FCStd`, `body_assembly.FCStd` und `lasius_assembly.FCStd`. Alle 145 CAD-Links verifiziert.

- [x] **FEA-Strukturverifikation von Tibia v2 & verstärktem Tarsus v2 (`tibia.FCStd`, `tarsus.FCStd`):**  
  * **Verifiziert via [`fea_tibia_tarsus_verification.py`](../../../../../scripts/dev/fea_tibia_tarsus_verification.py)** (CalculiX 2nd-Order `C3D10`, Gmsh, automatisches `*CLOAD`-Audit):
    * **`tibia.FCStd` ($53{,}54\,\text{g}$, $58.500$ Knoten):** Tripod `56°` ($20\,\text{N}$ mit echter $2{,}71\times$ Hebelkraft) $\sigma_{\text{max}} = 6{,}27\,\text{MPa}$ ($S = 7{,}18$), Tropfenfenster-Stege nur $1{,}80\,\text{MPa}$ ($S = 25{,}0$); Knie-Stall $S = 11{,}39$; $25\,\text{N}$ Extremstoß & $12\,\text{N}$ Querlast $S = 3{,}58$ (ohne Deckel).
    * **`tarsus.FCStd` ($6{,}68\,\text{g}$, $+20\,\%$ Schaft, $13.911$ Knoten):** Tripod `56°` ($20\,\text{N}$) $\sigma_{\text{max}} = 9{,}85\,\text{MPa}$ ($S = 4{,}57$, Schaft $S = 5{,}95$); $35\,\text{N}$ Extremstoß ($4{,}5\times$ Stall) Schaft $S = 2{,}24$ / Peak $S = 1{,}71$; $12\,\text{N}$ Querlast $S_{\text{Schaft}} = 3{,}49$.

- [ ] **Topologieoptimierung weiterer Komponenten (`coxa.FCStd`, `chassis_core.FCStd`):**  
  * **Coxa-Gelenk:**
    * FEM-Optimierung des $45^\circ$-A-Truss-Gussets zur Reduktion von Kerbspannungen an der Krafteinleitung vom Servohorn ins Gegenlager.
  * **Chassis-Core-Monocoque (`chassis_core.FCStd`):**
    * Bionische Fachwerkfenster im Monocoque-Körper zwischen den 4 M3-Standoff-Pfeilern und den Seitenwänden.




