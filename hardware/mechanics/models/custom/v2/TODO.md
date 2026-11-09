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

- [ ] **Elektronik-Basisplatte (Zentrales Montage-Deck / Tray):**  
  * **Status:** Zentrales Trägerdeck im Chassis-Kern.
  * **Funktion:** Aufgeräumte, vibrationsgedämpfte Aufnahme aller Kern-Elektronik-Komponenten:
    * 1× Raspberry Pi 4 (Montagebohrungen M2.5)
    * 2× PCA9685 16-Kanal Servo-Controller (`0x40` Links, `0x42` Rechts)
    * 1× TCA9548A 8-Kanal I2C-Multiplexer (`0x71`)
    * Integrierte Kabelführungsschächte zwischen oberem und unterem Chassis-Deck.
- [ ] **Chassis-Abdeckung / Exoskelett-Haube (Top Cover):**  
  * **Status:** Schutz- und Designelement über der Basisplatte.
  * **Funktion:**
    * Mechanischer Schutz der Platinen und Flachbandkabel vor Staub, Stürzen und Berührung.
    * Prägendes Design- und Stilelement der Lasius v2 (organische Insektenpanzerung / Chitinpanzer-Ästhetik).
    * Belüftungsschlitze / Chevron-Louvers für passive Kühlung von Pi 4 SoC und Spannungsreglern.
- [ ] **Unterboden-Abdeckung (Chassis Belly Pan / Skid Plate):**  
  * **Status:** Mechanischer Schutz der Chassis-Unterseite.
  * **Funktion & Konstruktion:**
    * Glatter Unterbodenschutz gegen Aufsitzen und Hängenbleiben im unebenen Gelände.
    * Schutz der unteren Servoverkabelung, Akkuhalterung und Durchführungen gegen mechanische Beschädigung von unten.
    * **Integrierte Aufnahme für 9-Feld-Bodenscanning-Sensor:**
      * Dedizierte Montageaufnahme und optischer Durchbruch (Sichtfenster) für den nach unten gerichteten Multi-Zonen-Sensor ($3 \times 3$ / 9-Zonen-Matrix, z. B. VL53L5CX/VL53L7CX) zur Höhenprofilerfassung des Geländes direkt unter dem Chassis.
      * Schutzkragen / versenkte Optikblende, um die Sensorlinsen bei Bodenkontakt vor Zerkratzen und Verschmutzung zu bewahren.




