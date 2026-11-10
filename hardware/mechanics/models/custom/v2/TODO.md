# Lasius CAD Generation v2 – Models & Mechanics Backlog

---

[Project Index](../../../../../README.md) | [Mechanics Documentation](../../../README.md) | [Closed Loop Plan](../../../../../docs/hardware/closed_loop_plan.md) |<br>
[Femur Script](../../../scripts/v2/generate_femur.py) | [Coxa Bracket Script](../../../scripts/v2/generate_coxa_bracket.py) | [Tibia Script](../../../scripts/v2/generate_tibia.py)

---

Dieser Backlog führt alle offenen Aufgaben, konstruktiven Erweiterungen und Verifikationsschritte für die **Generation v2** der Lasius-Mechanik (`hardware/mechanics/models/custom/v2/`).

---

## 1. Femur (`parts/femur.FCStd`)

- [ ] **Befestigung des AD-Wandlers (ADS1115) via Option C (Zentrierstifte + Deckel-Niederhalter):**  
  * **Status:** Beschlossenes Befestigungskonzept für die Femur-Kammer.
  * **Konstruktion:**
    * Auf den beiden Stand-off-Sockeln am Kammerboden ($Z = -4.80\,\text{mm}$) werden zwei vertikale **Zentrierstifte ($\varnothing 2.15\,\text{mm}$)** angedruckt, die formschlüssig in die beiden $\varnothing 2.35\,\text{mm}$ Bohrungen der Platine greifen und sie in $X$- und $Y$-Richtung spielfrei arretieren.
    * An der Unterseite des Deckels ([`Femur_Cover`](../../../scripts/v2/generate_femur.py)) werden zwei korrespondierende **Niederhalter-Rippen** (oder ein elastisches EPDM-/Moosgummi-Pad) integriert.
    * Beim Verschrauben des Deckels (4× M2 Senkkopf) wird die Platine von oben formschlüssig und vibrationsgedämpft auf die Sockel geklemmt.
  * **Vorteile:** Keine zusätzlichen M2-Schrauben in der engen Kammer, keine thermischen Gewindeeinsätze nötig, keine abbrechenden FDM-Schnappclips, werkzeuglose Platinenentnahme nach Abnehmen des Deckels.
  * **Verifizierte Koordinaten (anhand [`ads1115_reference.jpg`](../../../drawings/references/ads1115_reference.jpg)):**
    * Platinenabmessung: $28.0 \times 17.2\,\text{mm}$
    * Zentrierstift 1 (links): $X = 39.90\,\text{mm},\; Y = Y_{\text{mid}} + 5.30\,\text{mm}$
    * Zentrierstift 2 (rechts): $X = 60.10\,\text{mm},\; Y = Y_{\text{mid}} + 5.30\,\text{mm}$
    * Sockel-Auflageebene: $Z = -4.80\,\text{mm}$ (3.0 mm über Kammerboden $Z = -7.80\,\text{mm}$)
    * Stiftleiste liegt vorne im Freiraum-Kanal ($Y = Y_{\text{mid}} - 7.2\,\text{mm}$).
  * **Betroffener Code:** [`generate_femur.py`](../../../scripts/v2/generate_femur.py) (Abschnitte `Inner Hollow ADS1115 Chamber Pocket` & `Femur_Cover`).
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

## 2. Coxa Bracket (`parts/coxa_bracket.FCStd`)

- [ ] **Überarbeitung Seitenwangen & 45°-Stege nach Entwurfsvorgabe (Grüne Skizze):**  
  * **Status:** Die bisherigen Iterationen wichen stark von der Designvorgabe ab.
  * **Designreferenz:** [`femur_servo_wangen.svg`](../../../drawings/sketches/femur_servo_wangen.svg) (Grünes Designlayer `#55d400` über Femur-/Coxa-Zusammenbau; gerenderte Vorschau: [`femur_servo_wangen.png`](../../../drawings/sketches/femur_servo_wangen.png)).
  * **To-Do:** Vollständiger Neuentwurf der Seitenwangen und 45°-Fachwerkstreben:
    * Organischer, fließender Konturverlauf der Wangen zwischen Coxa-Servogehäuse und Femur-Gegenlager.
    * Saubere 45°-Fachwerkfenster (Truss-Windows) mit konsistenten Stegbreiten und verrundeten Ecken exakt gemäß der Vektorgeometrie der grünen Skizze.
    * Beseitigung aller unharmonischen Knicke und Kanten auf den Außenflächen.
  * **Betroffener Code:** [`generate_coxa_bracket.py`](../../../scripts/v2/generate_coxa_bracket.py).
- [ ] **DIN 439 M4 Flachmutter-Sitz (Gegenlager Femur-Achse):**  
  * Maßhaltigkeit der verpressten M4-Sechskanttasche für die flache DIN 439 Mutter nach Testdruck prüfen (Sitz $SW = 7.10\,\text{mm}$, Tiefe $2.40\,\text{mm}$).
- [ ] **Kabelauslass-Führung:**  
  * Freigang für die 4-adrige Servozuleitung des Coxa-Servos entlang des Versteifungs-Gussets prüfen.

---

## 3. Tibia (`parts/tibia.FCStd`)

- [ ] **Fußsensor-Integration (Omron D2F-L Mikroschalter):**  
  * Aufnahme und Anschlaggeometrie in der Tibia-Fußspitze für den taktilen Schalter präzisieren.
- [ ] **Kabelkanal Fußsensor $\rightarrow$ Femur:**  
  * Führung für das 2-adrige Sensorkabel von der Fußspitze über das Kniegelenk bis in die Femur-ADC-Kammer (Pin `A3`) festlegen.

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
- [ ] **Bewegungsraum- und Kollisionsprüfung:**  
  * Kinematischen Freigang der v2-Beinbaugruppe über den vollen Arbeitsbereich ($\pm 60^\circ$ Coxa, $\pm 60^\circ$ Femur, $\pm 60^\circ$ Tibia) auf Kollisionen zwischen Kabelbaum, Deckel und Chassis prüfen.
- [ ] **Generations-Vererbung & Link-Integrität:**  
  * Sicherstellen, dass alle Zukaufteile sauber aus `models/cots/` und unveränderte Chassis-Teile aus `custom/v1/` referenziert bleiben (`check_links.py` und FreeCAD XLink-Check).

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

## 6. Biomimetische Module & Aktuatoren (Kopf & Hinterleib)

- [ ] **Gaster modellieren (Ameisen-Hinterleib / Abdomen):**  
  * **Status:** Neues Modul am Heck des Roboters.
  * **Zweck & Funktion:**
    * Primär: Statischer und dynamischer Gewichtsausgleich (*Counterweight*) für die vorderen Kopfkomponenten (Kameraturm und Mandibeln).
    * Sekundär (zu evaluieren): Bauraum für Zusatzakku (z. B. 2S/3S LiPo), Power-Distribution-Board oder Heck-Sensorik.
  * **Überlegung Artikulation / Beweglichkeit:**
    * *Sollte sich der Gaster bewegen können?*
    * 1- bis 2-Achs-Gelenk (Servo am Petiolus / Stielchenglied) ermöglicht aktive dynamische Schwerpunktverlagerung (*Center of Gravity Shifting*) beim Klettern oder Laufen auf Steigungen sowie lebensechte biomimetische Gesten.
  * **Konstruktion:** Organisch geschwungener Hinterleib, passend zur Designsprache der Lasius-Beinsegmente.
- [ ] **Integrierte Kopf-Baugruppe (`head_assembly.FCStd` – Mandibeln & Kameraturm vereinen):**  
  * **Konzept:** Zusammenfassung von Mandibeln und Kamerasystem zu einem einheitlichen Kopfmodul an der Roboterfront:
    * *Augen / Sensorik:* Kameraturm (2-Achs Pan/Tilt Kopf mit 2× Micro-Servos und Pi Camera Module 3).
    * *Mundwerkzeuge:* Aktive Mandibeln (Greifzangen) darunter, gesteuert über einen Servo mit Kniehebel-/Zahnradgetriebe.
    * *Vorteil der Zusammenführung:* Biologisch stimmige Anatomie, geteilter Bauraum und gemeinsame Leitungsführung durch den "Hals" ins Chassis.

---

## 7. Chassis & Elektronik-Integration

- [x] ~~**Elektronik-Basisplatte (Zentrales Montage-Deck / Tray):**~~ **[ERLEDIGT]**  
  * **Modell & Generator:** [`electronics_tray.FCStd`](parts/electronics_tray.FCStd) generiert via [`generate_electronics_tray.py`](../../../scripts/v2/generate_electronics_tray.py).
  * **Status:** Zentrales Trägerdeck im Chassis-Kern auf $Z = 18{,}0\,\text{mm}$ (gehalten von 4 Standoff-Kragenbuchsen $\varnothing 14{,}2\,\text{mm}$ an den Spacern bei $X = \pm 45, Y = \pm 30$).
  * **Funktion & Integration:**
    * 2× PCA9685 16-Kanal Servo-Controller ($56 \times 19\,\text{mm}$ Lochbild links bei $Y = +14{,}5\,\text{mm}$, rechts bei $Y = -14{,}5\,\text{mm}$ auf $3{,}0\,\text{mm}$ Sockeln; 90°-Stiftleisten zeigen seitlich nach außen zu den Beinen mit $2{,}0\,\text{mm}$ Sicherheitsabstand zu den Coxa-Servos).
    * 1× TCA9548A 8-Kanal I2C-Multiplexer ($26\,\text{mm}$ Lochbild auf der Mittelachse bei $X = -52, Y = 0$).
    * 4× Kabelbinder-Ösen und frontseitiges Verkabelungs- und Akkufenster.
    * Vollständig kollisionsfrei mit Spacern, Beinen und Coxa-Servos.
    * Eingebunden in Subassembly [`electronics_tray_assembly.FCStd`](electronics_tray_assembly.FCStd) und Master-Assembly [`body_assembly.FCStd`](body_assembly.FCStd).
- [x] ~~**Chassis-Abdeckung / Exoskelett-Haube (Top Cover):**~~ **[ERLEDIGT]**  
  * **Modell & Generator:** [`chassis_top_cover.FCStd`](parts/chassis_top_cover.FCStd) generiert via [`generate_chassis_top_cover.py`](../../../scripts/v2/generate_chassis_top_cover.py).
  * **Status:** Aerodynamische Chitinpanzer-Haube auf der oberen Carbonplatte ($Z = 55{,}3\,\text{mm}$ bis $76{,}0\,\text{mm}$, Gesamthöhe $20{,}7\,\text{mm}$ mit $18{,}5\,\text{mm}$ Innenraum-Freiraum), verschraubt über die 4 zentralen M3-Standoff-Pfeiler bei $X = \pm 45, Y = \pm 30$ mit gesenkten Taschen.
  * **Funktion & Konstruktion:**
    * Mechanischer Schutz für den auf der oberen Chassis-Platte montierten Raspberry Pi 4 Model B, GPIO-Leitungen und interne Elektronik mit vollständiger Kollisionsfreiheit.
    * **Chevron-Louvers:** 5× $45^\circ$ nach vorn gepfeilte Lüftungsschlitze bei $X \in [25{,}0\dots 55{,}0\,\text{mm}]$ direkt über dem Pi 4 SoC zur passiven Kamin-Konvektionskühlung.
    * **Kamera-Kabeldurchbruch:** $20 \times 3{,}2\,\text{mm}$ Frontschlitz an der Schnauze ($X \in [82\dots 94\,\text{mm}]$) zur direkten Durchführung des CSI-Kamerakabels zum Kopfmodul.
    * Vollständig eingebunden in Master-Assembly [`body_assembly.FCStd`](body_assembly.FCStd).
- [x] ~~**Unterboden-Abdeckung (Chassis Belly Pan / Skid Plate):**~~ **[ERLEDIGT]**  
  * **Modell & Generator:** [`chassis_belly_pan.FCStd`](parts/chassis_belly_pan.FCStd) generiert via [`generate_chassis_belly_pan.py`](../../../scripts/v2/generate_chassis_belly_pan.py).
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




