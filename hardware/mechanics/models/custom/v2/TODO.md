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
- [x] **Kantenverrundung an den Kabeldurchführungen:**  
  * **Umgesetzt in [`generate_femur.py`](../../../scripts/v2/generate_femur.py):** Alle 4 Stadion-Mündungen der horizontalen Kabeltunnels ($14 \times 7\,\text{mm}$ bei $X = 26{,}0 / 33{,}5$ und $66{,}5 / 74{,}0\,\text{mm}$, insgesamt 16 Kanten) sind mit **$R = 1{,}50\,\text{mm}$ Einlauffillets** verrundet; Kabelbinder-Sättel mittig in den $7{,}5\,\text{mm}$-Schotten zentriert ($\ge 1{,}70\,\text{mm}$ Abstand zu den Fillets).
- [x] **Servohorn-Integration / Einlassen in die Femur-Wange:**  
  * **Bereits umgesetzt & verifiziert in [`generate_femur.py`](../../../scripts/v2/generate_femur.py):** Beide vorderen U-Mäuler (Hüfte $X = 0$, Knie $X = 100$) besitzen formschlüssige $\varnothing 25{,}30\,\text{mm}$ Kreistaschen ($R = 12{,}65\,\text{mm}$, Einlasstiefe $2{,}30\,\text{mm}$ von $Y = 27{,}00$ bis $29{,}30\,\text{mm}$) mit massiver Restwandstärke von **$3{,}70\,\text{mm}$** ($2{,}20\,\text{mm}$ unter den M2-Senkungen) sowie $0{,}0000\,\text{mm}^3$ Kollision in `leg_assembly.FCStd` / `leg_right_assembly.FCStd`.
- [ ] **Deckelpassung (`Femur_Cover`):**  
  * Reale Spaltmaße nach Testdruck verifizieren; Passung der 4× M2-Senkkopfschrauben mit Senkung im Deckel und Pilotlöchern im Gehäuse prüfen.

---

## 2. Coxa (`parts/coxa/coxa.FCStd`)

- [x] **Monolithisches Coxa-Gelenksegment & 45°-A-Truss-Fachwerk (Konzept 1):**  
  * **Status:** Erfolgreich implementiert gemäß [`STYLE_GUIDE.md`](../../../STYLE_GUIDE.md) und 1:1 mit Tibia vereinheitlicht.
  * **Umsetzung:**
    * Monolithische Wangen mit $G^1$-stetigen S-Kurven ($R_{\text{FRONT}} = 4{,}50\,\text{mm}$, $Z \in [0;\, 18]\,\text{mm}$) und 100 % spiegelbildlichem 6-Fenster-$45^\circ$-A-Truss um $Z = 9{,}00\,\text{mm}$ ($Z \in [7{,}75;\, 10{,}25]$ Firststeg, $w = 2{,}50\,\text{mm}$, $R = 1{,}40\,\text{mm}$, sliver-freie Flankentrapeze $X \in [9{,}7;\, 21{,}7]$).
    * Exakt paralleles $45{,}0^\circ$-Rückwand-Fachwerk ($w = 2{,}50\,\text{mm}$), sauber nach innen versetzter Kabelbinder-Sattel ($X = 60{,}5 / 63{,}5\,\text{mm}$) und `--export`-Guard.
    * Reine $\varnothing 3{,}20\,\text{mm}$ Durchgangsbohrung für die M3-Schraubenachse (Kugellager sitzt in der Bodenplatte).
    * Gewichtsersparnis: $41{,}3\,\text{cm}^3$ / $52{,}4\,\text{g}$ PETG.
  * **Betroffener Code:** [`generate_coxa.py`](../../../scripts/v2/generate_coxa.py).
- [ ] **DIN 439 M4 Flachmutter-Sitz (Gegenlager Femur-Achse):**  
  * Maßhaltigkeit der verpressten M4-Sechskanttasche für die flache DIN 439 Mutter nach Testdruck prüfen (Sitz $SW = 7.10\,\text{mm}$, Tiefe $2.40\,\text{mm}$).
- [ ] **Kabelauslass-Führung:**  
  * Freigang für die 4-adrige Servozuleitung des Coxa-Servos entlang des Versteifungs-Gussets prüfen.
- [x] **Fortführung der bionischen Krallen-/Sichel-Geometrie der Tibia auf der Coxa (Design-Konsistenz & Versteifung):**  
  * **Status:** Vollständig implementiert in [`generate_coxa.py`](../../../scripts/v2/generate_coxa.py) und in alle Baugruppen (`leg_assembly`, `leg_right_assembly`, `body_assembly`, `lasius_assembly`) sowie URDF synchronisiert.
  * **Umsetzung:**
    * **Bionischer Dorsal-Sichelkamm (`build_bionic_dorsal_sickle_crest`):** Schwungvoller $G^2$-B-Spline-Sichelbogen analog zu Tibia `e_dorsal` auf der oberen Wange ($y_c = 31{,}70 \rightarrow 49{,}60\,\text{mm}$, $1{,}70\,\text{mm}$ unter `Body_Top`), mit abgerundetem nach hinten geschwungenem Krallenhorn ($x_c = 60{,}10\,\text{mm}$), konkaver U-Kehle um die Coxa-Servo-Befestigungslasche und konzentrischem bionischem Tropfenfenster.
    * **Strukturelle T-Steg-Versteifung & stützfreie DfAM-Geometrie:** $2{,}50\,\text{mm}$ bündiger Innensteg auf dem zentralen A-Truss-Firststeg ($z_c \in [7{,}75;\, 10{,}25]$) mit glatter $45{,}0^\circ$-Schräge auf den $6{,}50\,\text{mm}$ starken Dorsal-Sichelbogen ($z_c \in [5{,}75;\, 12{,}25]$) und beidseitigen Relief-Taschen; hintere Blockecken ($X = 115{,}0$) mit $R = 3{,}50\,\text{mm}$ verrundet.
    * **Verifikation:** $0{,}0000\,\text{mm}^3$ Kollision in `leg_assembly.FCStd` & `leg_right_assembly.FCStd`; Hüft-Nickbereich voll erhalten (`[-95°, +95°]`, Knie `[+19°, +122°]`); Gewicht $54{,}2\,\text{g}$ PETG.

---

## 3. Tibia & Tarsus (`parts/tibia/tibia.FCStd` & `parts/tarsus/tarsus.FCStd`)

- [x] **Bionischer Zwillings-Servokäfig, SVG-Tropfenfenster & Bajonett-Servicedeckel (Option 2c-V2):**  
  * **Status:** Vollständig implementiert in [`generate_tibia.py`](../../../scripts/v2/generate_tibia.py), [`generate_tibia_assembly.py`](../../../scripts/v2/generate_tibia_assembly.py) und [`generate_tarsus_assembly.py`](../../../scripts/v2/generate_tarsus_assembly.py).
  * **Konstruktion:**
    * **Zwillings-Servokäfig (Twin Servo Cage) & Harmonisierter Untersteg:** 1:1 mit Coxa v2 vereinheitlichtes 6-Fenster-$45^\circ$-A-Truss-Schema ($R_{\text{FRONT}} = 4{,}50\,\text{mm}$, $Z \in [0;\, 18]$, $w = 2{,}50\,\text{mm}$ First- & Diagonalstege, $R = 1{,}40\,\text{mm}$, DIN 439 M4 Flachmutter-Gegenlagertasche). Der untere Krallen-Steg unter dem Tropfenfenster verjüngt sich per $C^2$-Übergang exakt auf $2{,}50\,\text{mm}$ ($Z \in [7{,}75;\, 10{,}25]$) bündig zum Wangen-Mittelsteg, während der äußere Dorsal-Sichelbogen unverändert $7{,}00\,\text{mm}$ stark bleibt.
    * **Konzentrische SVG-Krallen-Sichel (Tropfenfenster):** Tief in die vertiefte SVG-Knie-Kralle ($X_{\text{Kehle}} = 13{,}9\,\text{mm}$) hineingezogen ($X \in [15{,}1;\, 76{,}2]\,\text{mm}, Y \in [25{,}7;\, 47{,}4]\,\text{mm}$, $453\,\text{mm}^2$, exakter $7{,}45\,\text{mm}$-Parallel-Offset zur Außenlinie); obere linke Deckelschraube entfällt zugunsten von 2 integrierten Formschluss-Bajonettlaschen + 2× M2 DIN 7991 Senkschrauben am konturierten `Tibia_Cover` (`Tibia_Body`: $48{,}05\,\text{g}$ PETG).
    * **Lastfreie Mikroschalter-Auslösung & Staub-Labyrinth:** Horizontaler $0^\circ$-Omron D2FC-F-K NC-Mikroschalter; breite flache Deckenanschläge oberhalb der Feder und zwischen Schalter & Achse nehmen 100 % der Federkraft auf (Mikroschalter-Auslösung als reiner Nebeneffekt), konzentrische Labyrinth-Dichtung über der Nabe, $90^\circ$-eckig geöffneter distaler Unterrand bis zur Unterkante.
    * **3D-Exoskelett-Tarsus & Schlanker Kufenschuh:** Nahtlose Fortführung der Tibia-Außenkontur in XY ($17{,}6 \rightarrow 8{,}3\,\text{mm}$) und Z ($10{,}44 \rightarrow 6{,}40\,\text{mm}$ $C^2$-Hermite-Verjüngung) über einen konzentrischen $1{,}00\,\text{mm}$ Chitin-Gelenkspalt ($R_{\text{Tibia}} = 17{,}50\,\text{mm}$, $R_{\text{Tarsus}} = 18{,}50\,\text{mm}$ um Pivot), FEA-optimierte aufgefächerte $14{,}1\,\text{mm}$-Innenzunge ($9{,}37\,\text{g}$ PETG), kompakter Kufenfuß mit schlankem Formschluss-Schuh (`tarsus_shoe.FCStd`, $9{,}40\,\text{mm}$ breit, $1{,}64\,\text{g}$), integrierter gefaster Federführungsstift ($\varnothing 2{,}90 \times 3{,}20\,\text{mm}$), effektive Knie-Sohlen-Länge unverändert $152{,}6\,\text{mm}$.
    * **Verifikation:** $0{,}0000\,\text{mm}^3$ Kollisionen über alle Baugruppen und den gesamten $0{,}0^\circ\text{--}+5{,}0^\circ$ Hub-Sweep (Knie-Arbeitsraum `[+19°, +122°]` unverändert); 2nd-Order `C3D10` CalculiX-FEA bestanden (Tibia $48{,}05\,\text{g}$: Tripod $S_{\text{Global}} = 6{,}61$ / Sichel-Steg $S = 10{,}34$, $25\,\text{N}$ Extremstoß $S = 3{,}40$ / Sichel $S = 5{,}19$, $12\,\text{N}$ Querlast $S = 2{,}94$ / Sichel $S = 3{,}63$ ohne Deckel; 3D-Exoskelett-Tarsus $u = 0{,}64\,\text{mm}$, $S_{\text{Peak}} = 4{,}71$ / $S_{\text{Schaft}} = 8{,}21$ im Tripod-Stoß, $S_{\text{Schaft}} = 2{,}80$ bei $35\,\text{N}$ Extremstoß, $S_{\text{Schaft}} = 4{,}22$ bei $12\,\text{N}$ Querlast).
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
- [x] **Servohorn-Verschraubung aller 18 Servos in den Assemblies (`72× ISO 7380 M2 × 5 mm`):**  
  * **COTS-Normteil:** [`screw_m2_button_head.FCStd`](../../cots/screw_m2_button_head.FCStd) (`M2_Linsenkopfschraube`, $\varnothing 3{,}50 \times 1{,}15\,\text{mm}$ Linsenkopf mit SW 1,3 Innensechskant, $\varnothing 1{,}92 \times 5{,}00\,\text{mm}$ Schaft; generiert via [`generate_electronics_cots.py`](../../../scripts/cots/generate_electronics_cots.py)).
  * **Integration & Ausrichtung:**
    * **24× Coxa-Servohörner (`chassis_assembly.FCStd` → `Coxa_Horn_Screws`):** Je 4× M2×5 auf $\varnothing 16{,}00\,\text{mm}$ Lochkreis um alle 6 Coxa-Ohren (`(±86, ±65)`, `(0, ±75)`) ab `Z = 55,32 mm` durch `Body_Top` in die 6 Coxa-Servohörner (flacher Linsenkopf kollisionsfrei zum darüberliegenden `Chassis_Canopy` bei `(0, ±83)`).
    * **48× Hüft- & Knie-Servohörner (`leg_assembly.FCStd` & `leg_right_assembly.FCStd` → `Hip_Horn_Screws`, `Knee_Horn_Screws`):** Je 4× M2×5 versenkt in den $\varnothing 4{,}30 \times 1{,}50\,\text{mm}$ Femur-Taschen (`Y = ±31,52 mm`); `Femur_Servo_Horn` und `Knee_Servo_Horn` separat vom `Servo_Body` um `±25°` / `±80°` getaktet für konzentrische Lochdeckung in Standard-Standpose.
    * **Verifikation:** **$0{,}0000\,\text{mm}^3$** Kollision in `chassis_assembly.FCStd`, `leg_assembly.FCStd`, `leg_right_assembly.FCStd` und `body_assembly.FCStd` (inkl. `Coxa_Horn_Screws ↔ 6× Leg_*.Coxa_Servo`, `Body_Top`, `Chassis_Canopy`); alle 206 CAD-Links in 15 Assemblies OK.
- [x] **Einheitliche COTS-Deckelverschraubung & Ruthex-M2-Einsätze für Femur & Tibia (`36× DIN 7991 M2 × 6 mm` + `36× Ruthex M2`):**  
  * **COTS-Normteile:** [`screw_m2_countersunk.FCStd`](../../cots/screw_m2_countersunk.FCStd) (`M2_Senkkopfschraube`, DIN 7991 M2×6 mit SW 1,3 Innensechskant) & [`insert_m2_ruthex.FCStd`](../../cots/insert_m2_ruthex.FCStd) (`Ruthex_M2_Insert`, Messing $\varnothing 3{,}16 \times 4{,}00\,\text{mm}$ CAD-Einbaumaß) via [`generate_electronics_cots.py`](../../../scripts/cots/generate_electronics_cots.py).
  * **Umsetzung:**
    * [`generate_femur.py`](../../../scripts/v2/generate_femur.py): Alle 4 Deckelbohrungen von $\varnothing 1{,}80\,\text{mm}$ Pilotloch auf echte $\varnothing 3{,}20 \times 4{,}30\,\text{mm}$ **Ruthex-M2-Aufnahmen** + $\varnothing 2{,}10\,\text{mm}$ Freiloch aktualisiert (1:1 konsistent zu `PRINTING_GUIDE.md` & `tibia.FCStd`).
    * [`femur_assembly.FCStd`](femur_assembly.FCStd), [`tibia_assembly.FCStd`](tibia_assembly.FCStd) & [`leg_right_assembly.FCStd`](leg_right_assembly.FCStd): Hartcodiertes Tibia-Schraubendummy entfernt; alle 36 Senkkopfschrauben und 36 Messing-Gewindeeinsätze per `App::Link` (rechts 100 % ungespiegelt) eingebunden.
    * **Verifikation:** **$0{,}0000\,\text{mm}^3$** Kollision in `femur_assembly`, `tibia_assembly` (inkl. Tarsus-Hub-Sweep `0°..+5°`), `leg_assembly` und `leg_right_assembly`.
- [x] **Bionischer Schreibtisch-Entwicklungsständer mit `22,1 mm` Tischklemme & 4-Dorn TPU-Klick-Docking ([`desk_stand_assembly.FCStd`](desk_stand_assembly.FCStd)):**  
  * **Generator & Einzelteile:** [`generate_desk_stand.py`](../../../scripts/v2/generate_desk_stand.py) erzeugt die 5 modularen Bambu-Lab-optimierten Teile unter `parts/stand/` (`desk_stand_clamp.FCStd`, `desk_stand_column.FCStd`, `desk_stand_cradle.FCStd`, `desk_stand_knob.FCStd`, `desk_stand_pads.FCStd`), die reine Ständer-Baugruppe [`desk_stand_assembly.FCStd`](desk_stand_assembly.FCStd) sowie die angedockte Kombinations-Baugruppe [`desk_stand_docked_assembly.FCStd`](desk_stand_docked_assembly.FCStd) (`25-DoF Lasius_Assembly` + `Desk_Stand_Assembly` + ausblendbare `22,1 mm` Referenz-Tischplatte); korrespondierende 4× staubdichte Klick-Buchsen in [`chassis_belly_pan.FCStd`](parts/chassis/chassis_belly_pan.FCStd) via [`generate_chassis_belly_pan.py`](../../../scripts/v2/generate_chassis_belly_pan.py).
  * **Architektur (Variante 1.1):** Topologieoptimierte Leichtbau-Kranmast-Version (`156,4 cm³` / ~`133 g` gedrucktes PETG, **−76 %** gegenüber Erstentwurf!): $H = 235\,\text{mm}$ Bauchhöhe über `22,1 mm` Tischplatte (`38 mm` breite I-Träger-C-Klemme `66,0 cm³` mit `15 mm` Fachwerkrücken, verjüngten Wangen, `34 mm` Maul, M8×40 Hybrid-Spindel + TPU-Pads), **innen 100 % hohler 4-seitiger Kran-Gittermast** (`36×36 → 27×27 → 34×34 mm`, `2,50 mm` Style-Guide-Streben, 7 Rauten-Stockwerke, `45°`-Innengewölbe, `54,3 cm³` / `69,0 g`, aufrecht stützfrei druckbar), symmetrischer $19 \times 19\,\text{mm}$ `4× M4`-Flansch ($0^\circ / 90^\circ / 180^\circ / 270^\circ$ drehbar), ultrakompakte **100 % stützfreie H-Wiege** (`129 × 63 mm`, `27,8 cm³` / ~`24 g`) mit **4-Punkt-TPU-95A-Klick-Docking** an `(±58,0; ±26,55 mm)` (4× steife konische PETG-Kerndorne mit Überwurf-TPU-95A-Rasthülsen `Ø5,96 mm` Wulst + `Ø8,90 mm` Dämpfungsflansch rasten spielfrei in 4× staubdichte `Ø5,30 / Ø6,10 mm` Hinterschnitt-Buchsen mit `45°`-Einführfase in `Chassis_Belly_Pan` ein) & offenem Zentralkanal für VL53L5CX-ToF & XT60-Labornetzteil.
  * **Verifikation:** **$0{,}0000\,\text{mm}^3$** intern (29 Komponenten), `Chassis_Belly_Pan ↔ Chassis_Battery_Hatch`, `chassis_assembly.FCStd`, angedockt an `body_assembly.FCStd` (`Chassis_Belly_Pan`, `Chassis_Battery_Hatch`, `Body_Bottom`, `Chassis_Core_Assembly`, alle 6 Beine) sowie über alle Extrem-Schwenks (`FL +35°`, `RL -25°`) und Extremposen (Gait Squat `+48,8 mm`, Deep Tuck `-60°/+119°` `+136,3 mm`, Extreme Down `-76°/+22°` `+8,3 mm`, Power-Off Drop `+38,7 mm`); **259 / 259 CAD-Links** über 16 Assemblies OK.
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
    * [`bno085_board.FCStd`](../../cots/bno085_board.FCStd): Adafruit BNO085 9-DOF Orientation IMU Breakout (PID 4754, $25{,}6 \times 22{,}7 \times 4{,}6\,\text{mm}$, $20{,}32 \times 17{,}78\,\text{mm}$ M2.5-Lochbild, Mattschwarz) mit dualen STEMMA-QT-Buchsen und `header_pin_1x6_ra.FCStd`-Referenz.
    * [`magnet_5x2.FCStd`](../../cots/magnet_5x2.FCStd): Neodym-Scheibenmagnet $\varnothing 5{,}0 \times 2{,}0\,\text{mm}$ (Nickel-Silber, $8\times$ in `chassis_assembly.FCStd` für die selbstzentrierende Canopy-Befestigung).
    * [`screw_m2_button_head.FCStd`](../../cots/screw_m2_button_head.FCStd): ISO 7380 M2 × 5 mm Linsenkopfschraube mit Innensechskant SW 1,3 ($72\times$ über `chassis_assembly.FCStd`, `leg_assembly.FCStd` & `leg_right_assembly.FCStd` für alle 18 Servo-Hörner).
    * [`screw_m2_countersunk.FCStd`](../../cots/screw_m2_countersunk.FCStd) & [`insert_m2_ruthex.FCStd`](../../cots/insert_m2_ruthex.FCStd): DIN 7991 M2 × 6 mm Senkkopfschraube (SW 1,3) & Ruthex M2 × 4,0 mm Messing-Gewindeeinsatz ($36\times$ über Femur- & Tibia-Serviceklappen).
    * [`screw_m4x20_countersunk.FCStd`](../../cots/screw_m4x20_countersunk.FCStd), [`bolt_m8x40_hex.FCStd`](../../cots/bolt_m8x40_hex.FCStd) & [`nut_m8_hex.FCStd`](../../cots/nut_m8_hex.FCStd): DIN 7991 M4×20 & DIN 933/934 M8×40 Normteile für [`desk_stand_assembly.FCStd`](desk_stand_assembly.FCStd).
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
    * Einteiliges Magnet-Canopy mit integrierten `'>>>'` Chevrons & UBEC-Abluftschlitzen: [`chassis_canopy.FCStd`](parts/chassis/chassis_canopy.FCStd) generiert via [`generate_chassis_canopy.py`](../../../scripts/v2/generate_chassis_canopy.py) (separates `chassis_service_cover` ersatzlos entfallen).
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

- [x] ~~**Konzeptstudie & Realisierung: Monolithischer Chassis-Kern / Kapselung als Ersatz der 4 mittleren Spacer:**~~ **[ERLEDIGT → 2-Ebenen-Segmentierung]**  
  * **Modelle & Generatoren:** [`chassis_core_lower.FCStd`](parts/chassis/chassis_core_lower.FCStd), [`chassis_core_upper.FCStd`](parts/chassis/chassis_core_upper.FCStd) und [`chassis_core_assembly.FCStd`](chassis_core_assembly.FCStd) generiert via [`generate_chassis_core.py`](../../../scripts/v2/generate_chassis_core.py) (+ 4× COTS [`standoff_m3x50_round.FCStd`](../../cots/standoff_m3x50_round.FCStd)).
  * **Status:** Vollständig umgesetzter 3D-Druck-Sandwich-Stützkern ($51{,}3\,\text{mm}$ Bauhöhe zwischen $Z = 2{,}0$ und $53{,}3\,\text{mm}$), der die 4 mittleren Kunststoff-Spacer bei $X = \pm 45, Y = \pm 30\,\text{mm}$ durch eine steife, vibrationsdämpfende Schubsteg-Monocoque-Struktur ersetzt.
  * **Integrierte Kapselung:**
    * Vertikale Führungsschienen für 2× PCA9685 PWM-Controller (Stiftleisten ragen kollisionsfrei nach oben $+Z$ in den Wartungsschacht).
    * LiPo-Akkutunnel im Untergeschoss ($Z \in [1{,}5\dots 16{,}5\,\text{mm}]$) für 2S Flat-Pack.
    * TCA9548A I2C-Multiplexer-Kammer im Heckbereich.
    * Formschluss-Zentrierfalze und horizontale M3 Ruthex-Schnittstellen zu Front (`chassis_neck`) und Heck (`chassis_tail`).
    * $16\,\text{mm}$ Taillierungs-Freigang zu den mittleren Coxa-Servos ML und MR.
  * **Integration:** Eingebunden in [`lasius_assembly.FCStd`](lasius_assembly.FCStd).

- [x] **Zentrale Sensor-Hub & 3,3 V / GND-Verteilerplatine (`sensor_hub_board.FCStd`):**  
  * **Modell & Generator:** [`sensor_hub_board.FCStd`](parts/chassis/sensor_hub_board.FCStd) generiert via [`generate_sensor_hub_board.py`](../../../scripts/v2/generate_sensor_hub_board.py).
  * **Status:** Vollständig konstruiert und als Subkomponente in [`chassis_core_assembly.FCStd`](chassis_core_assembly.FCStd) eingebunden.
  * **Architektur & Bauraum-Integration:**
    * **Platzierung:** Sitzt auf den beiden Zwischenboden-Domen bei $X = 0{,}0\,\text{mm}, Y = \pm 13{,}0\,\text{mm}, Z = 28{,}00\,\text{mm}$ im $24\,\text{mm}$-Spalt zwischen den beiden horizontalen PCA9685-Controllern.
    * **Abmessungen:** $54{,}0 \times 22{,}0 \times 1{,}60\,\text{mm}$ FR4-Substrat mit $R = 2{,}0\,\text{mm}$ Eckverrundungen.
    * **Steckbare TCA9548A-Aufnahme:** Duale 12-Pin Buchsenleisten ($h = 4{,}00\,\text{mm}$) als COTS-Referenz [`socket_header_1x12.FCStd`](../../cots/socket_header_1x12.FCStd) bei $X = \pm 8{,}77\,\text{mm}$, die das TCA9548A Breakout-Modul auf $Z = 33{,}60\,\text{mm}$ anheben.
    * **COTS-Header-Referenzen:** Sämtliche Stift- und Buchsenleisten sind als modulare COTS-Normteile (`header_pin_1x4.FCStd`, `header_pin_1x2.FCStd`, `socket_header_1x12.FCStd`) eingebunden – mit durchgängig tiefschwarzen Thermoplast-Sockeln (`(0.12, 0.12, 0.12)`) und diskreten vergoldeten Vierkant-Pins (`(0.85, 0.70, 0.20)`).
    * **6× 4-Pin Bein-Steckplätze (`3,3V · GND · SCx · SDx`):**
      * $+Y$-Bank (nach links zeigend): `LR` (CH2 Violett), `LM` (CH1 Grün), `LF` (CH0 Blau) sowie Pi-Haupteingangsheader (`3,3V, GND, SDA, SCL`) und 2-Pin PCA9685-Left-Logikversorgungsheader.
      * $-Y$-Bank (nach rechts zeigend): `RR` (CH5 Grau), `RM` (CH4 Weiß), `FR` (CH3 Orange) sowie 4-Pin Sensor-Erweiterungsheader (CH6/7) und 2-Pin PCA9685-Right-Logikversorgungsheader.
    * **Ergonomie:** Alle 6 Bein-Anschlüsse liegen außerhalb des TCA9548A-Footprints ($|Y| \ge 16{,}2\,\text{mm}$) mit $16{,}2\,\text{mm}$ Kopffreiheit zu `Body_Top` und sind bei abgenommenem Service-Deckel direkt von oben frei zugänglich.
    * **Kollisionsfreiheit:** Exakt **$0{,}0000\,\text{mm}^3$** Kollision zu Monocoque, PCA9685, TCA9548A und LiPo-Akku.

- [x] **Modulare COTS-Pinheader & Buchsenleisten-Bibliothek (`hardware/mechanics/models/cots/`):**
  * **Modelle & Generator:** Kanonische Normteil-Bibliothek generiert via [`generate_headers_cots.py`](../../../scripts/cots/generate_headers_cots.py):
    - [`header_pin_1x2.FCStd`](../../cots/header_pin_1x2.FCStd), [`header_pin_1x4.FCStd`](../../cots/header_pin_1x4.FCStd), [`header_pin_1x6.FCStd`](../../cots/header_pin_1x6.FCStd)
    - [`header_pin_1x10.FCStd`](../../cots/header_pin_1x10.FCStd), [`header_pin_1x12.FCStd`](../../cots/header_pin_1x12.FCStd), [`header_pin_2x20.FCStd`](../../cots/header_pin_2x20.FCStd)
    - [`header_pin_3x16_ra.FCStd`](../../cots/header_pin_3x16_ra.FCStd) (90° Winkel-Servoheader), [`header_pin_1x6_ra.FCStd`](../../cots/header_pin_1x6_ra.FCStd) (90° ToF-Header), [`socket_header_1x12.FCStd`](../../cots/socket_header_1x12.FCStd)
  * **Standards:** Thermoplastische Sockel/Kragen immer mattschwarz (`(0.12, 0.12, 0.12)`), Stifte immer diskrete $0{,}64 \times 0{,}64\,\text{mm}$ Vierkant-Pins aus Messing/Gold (`(0.85, 0.70, 0.20)`).
  * **Integration:** Alle Platinen ([`rpi4_model_b.FCStd`](../../cots/rpi4_model_b.FCStd), [`pca9685_board.FCStd`](../../cots/pca9685_board.FCStd), [`tca9548a_board.FCStd`](../../cots/tca9548a_board.FCStd), [`ads1115_board.FCStd`](../../cots/ads1115_board.FCStd), [`vl53l5cx_board.FCStd`](../../cots/vl53l5cx_board.FCStd), [`bno085_board.FCStd`](../../cots/bno085_board.FCStd) und [`sensor_hub_board.FCStd`](parts/chassis/sensor_hub_board.FCStd)) als modulare `App::Part`-Baugruppen mit `App::Link`-Referenzen umgesetzt. Material-Overrides in Assemblies aufgehoben für naturgetreue Farbtrennung.

- [x] ~~**Top-Deck Triple-UBEC & Heck-Power-Cockpit, Monolithisches Magnet-Canopy, CoG-balancierter Level 1 & Separates Power-Gaster (Option G2):**~~ **[ERLEDIGT]**  
  * **Oberdeck-Power-Träger ([`chassis_rpi_mount.FCStd`](parts/chassis/chassis_rpi_mount.FCStd), [`generate_chassis_rpi_mount.py`](../../../scripts/v2/generate_chassis_rpi_mount.py)):**
    1. **Raspberry Pi 4 zentriert (`0, 0, Z = 59,80 mm`):** 100 % freie Ports (`+X` USB/Eth, `-Y` USB-C/2× Micro-HDMI/Audio, `-X` MicroSD durch `20 mm` offenen Mittelkanal, `+Z` 40-Pin GPIO).
    2. **Alle 3 UBECs vereint auf `Body_Top`:** **2× Hobbywing BEC 10A V2-Car (`HW30603003`, `6,0 V`)** in symmetrischen Heck-Kühlwiegen bei **`X = -79,5, Y = ±21,5, Z = 56,52 mm`** (45°-Außenfasen innerhalb `Body_Top`, 3× Boden-Kühlschlitze, Ferrite/Ausgänge nach `+X` zum zentralen `Body_Top`-Ausschnitt) + **1× `UBEC_3A_Pi` (`5 V` Logik)** symmetrisch auf der 100 % portfreien `+Y`-Flanke bei **`X = 0,0, Y = +39,5, Z = 56,52 mm`**.
    3. **Heck-Schalter- & Sicherungs-Cockpit (`X ∈ [-127,0; -86,0 mm]`):** Starr über **beide** hinteren CFRP-M3-Spacer (`(-90,0; 0,0)` und `(-120,0; 0,0)`, insgesamt 10× M3-Senkschrauben) geklemmt: **2× Mini-Schiebeschalter** bündig versenkt in den $45^\circ$-Heckfasen bei **`(-116,0; ±14,5; Z = 59,00 mm)`** (`Switch_Logic_Pi` links `+Y` grün, `Switch_Servos_Armed` rechts `-Y` rot; selbst ausgefahrene Knöpfe geschützt innerhalb der `Body_Top`-Carbonkontur) + **1× stehende Top-Pull `25 A` Mini-ATM Sicherung** mittig zwischen den Schaltern bei **`(-105,0; 0,0; Z_flange = 78,80 mm)`** (Ziehkappe ragt bei `Z = 80,6..82,8 mm` werkzeuglos greifbar über das Canopy hinaus).
    4. **Front-Deck BNO085 9-DOF IMU-Plattform (`X = +75,0, Y = 0,0, Z_pcb = 58,32 mm`):** Über zwei symmetrische Längsstege (`|Y| ∈ [16,0; 21,5 mm]`, lässt den vorderen `Body_Top`-Ausschnitt 100 % offen) starr auf das geschlossene vordere Carbon-Deck vorgezogen; 4× M2.5-Sockel im gedrehten Adafruit-Raster (`17,78 × 20,32 mm`, nichtmagnetische Nylon-/Messingschrauben verwenden!) über `0,80 mm` isolierendem PETG-Freischnittboden (`+0,80 mm` Luft unter Lötstiften). Maximaler EMV-/Magnetabstand zu Heck-UBECs (`~156 mm`), Pi-UBEC (`~85 mm`), Front-Coxa-Servos (`~72,5 mm`) & Canopy-Magneten (`~48,5 mm`), `> 5,0 mm` Canopy-Kopffreiheit (`Z_max = 62,87 mm` vs. Canopy `≥ 67,91 mm`), `0,0000 mm³` Kollision (`chassis_assembly.FCStd`, 154/154 CAD-Links, URDF & `inertias.json` synchronisiert).
  * **Monolithisches einteiliges Magnet-Canopy ([`chassis_canopy.FCStd`](parts/chassis/chassis_canopy.FCStd), [`generate_chassis_canopy.py`](../../../scripts/v2/generate_chassis_canopy.py)):**
    * Redundantes `chassis_service_cover.FCStd` inkl. Generator, STL und aller Referenzen (CAD, URDF, Three.js Dashboard, Doku) restlos entfernt; 3 obsolete Rand-Spacer-Bohrungen (`+128, ±12` & `-120, 0`) entfernt (werkzeugloses Abheben per Magneten auf den 4 Pfeilern `±48, ±36`).
    * Glatt nach hinten über beide Hobbywing-UBECs gezogene Dorsal-Haube mit **5× $45^\circ$-`'>>>'` Chevron-Louvers** über dem Pi 4 SoC, **2×4 Heck-Abluftschlitzen** über den Hobbywing-Kühlkörpern, **2× nach unten offenen $45^\circ$-Schalterbögen** und zentraler **Top-Pull-Sicherungsöffnung (`17,0 × 11,2 mm`)** — hebt 100 % gerade nach `+Z` ohne Hängenbleiben ab.
  * **CoG-balancierter Level 1 & Geschlossene Belly Pan ([`chassis_core_lower.FCStd`](parts/chassis/chassis_core_lower.FCStd), [`chassis_core_upper.FCStd`](parts/chassis/chassis_core_upper.FCStd), [`chassis_belly_pan.FCStd`](parts/chassis/chassis_belly_pan.FCStd), [`chassis_battery_hatch.FCStd`](parts/chassis/chassis_battery_hatch.FCStd)):**
    * Alle obsoleten Level-1-UBEC-Altlasten und Taillen-Ausschnitte entfernt $\rightarrow$ **100 % geschlossene, nahtlose $G^1$-Taillenwände**, scharfe 4-eckige `Body_Bottom`-Passform (`159,80 × 49,80 mm`), **Front- UND Heck-Schwalbenschwanz** intakt (`X = +85..+135 mm` frei für Kopf/Hals, `X = -85..-132 mm` frei für Gaster).
    * **2S LiPo nach vorn-mittig auf `X = +36,0 mm`** verschoben (Pack `X ∈ [0; +72]`, XT60/Leitungen hinten `[-19,5; 0]`, oberer Anschlagsteg mit Zugentlastungs-Kerbe), kompensiert die $72\,\text{g}$ Heck-UBECs auf `< 1 mm` Schwerpunkt-Offset.
    * Glatte, staubdichte Belly Pan ohne Front-Kühlschlitze; **`VL53L5CX` 9-Zonen-ToF** auf feste Heckbrücke (`X = -58,5 mm`) verlegt; klappbare Akkuklappe auf **`116 mm`** (`X ∈ [-40,0; +76,0]`, 7-fach Filamentscharnier, Snap-Latch bei `X = +18,0`, nimmt zukünftige 2S-Packs bis `110 mm` auf) erweitert.
  * **Option G2 — Separates 2-DoF Power-Gaster-Modell ([`gaster_power_assembly.FCStd`](gaster_power_assembly.FCStd)):**
    * Eigenständiges, über Heck-Schwalbenschwanz + `(-90/-120, 0)` andockbares 2-DoF Power-Gaster ([`generate_gaster_power_assembly.py`](../../../scripts/v2/generate_gaster_power_assembly.py)) mit realen NR-645 Pan/Tilt-Servos, 2× Hobbywing 10A UBECs, `25 A` Mini-ATM Sicherung und 2× Mini-Schiebeschaltern.
  * **Verifikation & Workflow:** Exakt **$0{,}0000\,\text{mm}^3$** Kollision in `chassis_core_assembly.FCStd`, `chassis_assembly.FCStd`, `gaster_power_assembly.FCStd` (intern + angedockt) und `chassis_belly_pan ↔ chassis_battery_hatch`; URDF (`2,959 kg`, 28 kompakte Binary-STLs), `inertias.json`, [`03_power_distribution.yml`](../../../../electronics/wiring/03_power_distribution.yml) und 15 Assemblies / 153 CAD-Links synchronisiert; FreeCAD-One-Click-Makro `Reload_All.FCMacro` eingerichtet.
- [x] **Formschlüssige 2-Ebenen-Segmentierung des `Chassis_Core` (`Lower` + `Upper`) & 4× `M3 × 50 mm` Metall-Zuganker (Option 1):**
  * **Modelle & COTS:** [`chassis_core_lower.FCStd`](parts/chassis/chassis_core_lower.FCStd) (`45,2 cm³` / `57,4 g` massiv, `Z = 0,02..23,99 mm`), [`chassis_core_upper.FCStd`](parts/chassis/chassis_core_upper.FCStd) (`51,4 cm³` / `65,3 g` massiv, `Z = 24,01..53,28 mm`, **100 % stützfrei** plan auf Zwischenboden!), [`standoff_m3x50_round.FCStd`](../../cots/standoff_m3x50_round.FCStd) (4× `Ø5,0 × 50 mm` Metall-Distanzhülse in `Ø5,25 mm` Durchgangsbohrungen bei `(±45, ±30)`, `Z = 2,65..52,65 mm`) eingebunden in [`chassis_core_assembly.FCStd`](chassis_core_assembly.FCStd).
  * **Formschluss & DfAM:** Parametrisches `Z_SPLIT = 24,00 mm`; volle `1,60 mm` Außenwand bleibt ungeschwächt + 4× konzentrische Pfeiler-Zentrierkragen (`Ø8,30` in `Ø8,60` + $45^\circ$-Innenkegel) + 5× segmentierte Innen-Führungszungen (`1,80 mm` mit $45^\circ$-Rampen in durchgängigen Deck-Nuten: Front, 2× Heck, 2× Mittel-Taille) + $0{,}35\,\text{mm}$ V-Schattenfuge + $45^\circ$-LiPo-Stopprippen & -Bogen-Schott. Ersetzt 8× Ruthex M3 Inserts komplett; `Belly_Pan` & `RPi_Mount` bleiben 100 % unverändert!
  * **Verifikation:** **$0{,}0000\,\text{mm}^3$** Kollision (`Lower ↔ Upper`, `chassis_core_assembly.FCStd`, `chassis_assembly.FCStd`, `desk_stand_assembly.FCStd`); **264 / 264 CAD-Links** über 16 Assemblies OK.

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
    * **`tibia.FCStd` ($48{,}05\,\text{g}$, $56.845$ Knoten, Krallen-Sichel + vereinheitlichte 6-Fenster-Wangen + $2{,}50\,\text{mm}$ Untersteg):** Tripod `56°` ($20\,\text{N}$ mit echter $2{,}71\times$ Hebelkraft) $\sigma_{\text{max}} = 6{,}81\,\text{MPa}$ ($S = 6{,}61$), Sichel-/Steg-Zone $4{,}35\,\text{MPa}$ ($S = 10{,}34$); Knie-Stall $S = 10{,}81$; $25\,\text{N}$ Extremstoß $S = 3{,}40$ (Sichel $S = 5{,}19$); $12\,\text{N}$ Querlast $S = 2{,}94$ (Sichel $S = 3{,}63$, konservativ ohne Deckel).
    * **`tarsus.FCStd` ($9{,}37\,\text{g}$, 3D-Exoskelett $10{,}44 \rightarrow 6{,}40\,\text{mm}$ + $14{,}1\,\text{mm}$ Innenzunge):** Tripod `56°` ($20\,\text{N}$) $\sigma_{\text{max}} = 9{,}56\,\text{MPa}$, $u = 0{,}64\,\text{mm}$ ($S_{\text{Peak}} = 4{,}71$, Schaft $S = 8{,}21$); $35\,\text{N}$ Extremstoß ($4{,}5\times$ Stall) Schaft $S = 2{,}80$ / Peak $S = 1{,}76$; $12\,\text{N}$ Querlast $S_{\text{Schaft}} = 4{,}22$ ($u = 1{,}76\,\text{mm}$).

- [ ] **Topologieoptimierung weiterer Komponenten (`coxa.FCStd`, `chassis_core_lower/upper.FCStd`):**  
  * **Coxa-Gelenk:**
    * FEM-Optimierung des $45^\circ$-A-Truss-Gussets zur Reduktion von Kerbspannungen an der Krafteinleitung vom Servohorn ins Gegenlager.
  * **Chassis-Core-Monocoque (`chassis_core_lower.FCStd`, `chassis_core_upper.FCStd`):**
    * Bionische Fachwerkfenster im Monocoque-Körper zwischen den 4 M3-Standoff-Pfeilern und den Seitenwänden.

---

## 9. Offene Ideen & Geplante Ausbaustufen (Heck-Cockpit, Displays, Canopy & Kopf)

*(Dokumentierte Konzept-Optionen für künftige Iterationen — der verifizierte aktuelle CAD-Stand mit $0{,}0000\,\text{mm}^3$ Kollision bleibt bis zur Auswahl unverändert; siehe auch [`decisions.md`](../../../../../docs/hardware/decisions.md).)*

- [ ] **Heck-Bedieneinheit mit Master-Switch (Vergleichsstudie `Rear_Control_Options`, 3 Optionen):**
  * **Option 1 — `3-Stufen-Master` (Empfehlung, geringe Komplexität):**
    * Ein `3P3T` Mini-Schiebeschalter (`OFF → LOGIC → ARMED`, verhindert mechanisch Servo-Freigabe vor Pi-Boot; Standby `< 0,5 mA`), ein `6×6 mm` Pi Safe-Shutdown-Taster (`GPIO3`, schützt die MicroSD-Karte), 2× 3 mm Status-LEDs (Grün `5 V` / Rot `6 V`) sowie die zentrale Top-Pull `25 A` Mini-ATM Sicherung als echte `0,00 mA` galvanische Trennung.
  * **Option 2 — `30 A High-Side MOSFET Master` (Soft-Latch & Auto-Power-Off):**
    * Kompaktes `24×16 mm` 30 A High-Side P-MOSFET / Pololu Power-Switch-Board zwischen den Hobbywing-UBECs (`< 10 µA` Ruhestrom; Raspberry Pi schaltet sich nach `shutdown` vollständig selbst stromlos) + Master-Taster + Pi-Shutdown-Taster + separater roter `SERVOS ARM/KILL` DPST-Schiebeschalter + 2× Status-LEDs + `25 A` Sicherung.
  * **Option 3 — `Heck-Telemetrie-Cockpit mit Display`:**
    * Kombiniert Option 1 oder 2 mit einem bündig hinter einem Canopy-Sichtfenster eingelassenen Status-Display im Heck (Akkuspannung, Strom, IP-Adresse, Gait-Modus, Temperatur).
- [ ] **Display-Auswahl & Multi-Display-Integration (Heck-Status & bionische Kopf-Augen):**
  * **`0,91"` I²C OLED (`128×32`, `38×12 mm`, SSD1306, ~3,90 €/Stk.):** Schlankes Visier, passt direkt auf die Heck-Schräge (`Option_3_OLED_Telemetry`); feste Adresse `0x3C` (kein Adress-Jumper), gerade Pinleiste vorverlötet, keine M2-Bohrungen (PETG-Klemmtasche).
  * **`0,96"` I²C OLED (`128×64`, `27,0×27,3 mm`, SSD1306, Mono Blau oder feste 2-Zonen Gelb `y=0..15` / Blau `y=16..63`, ~2,20–2,90 €/Stk.):** Unbestückte Stiftleiste (ideal für flaches $90^\circ$-Löten), 4× M2-Bohrungen (`23×23 mm`), `0x3C/0x3D` Adress-Jumper. Passt sauber auf die Heck-Schräge, wenn die `25 A` Sicherung in den freien `20 mm`-Mittelkanal zwischen beiden UBECs (`X = -76, Y = 0`, flaches Canopy-Dach) vorverlegt wird. Gelb/Blau ideal als Heck-Status-HUD; Mono oder RGB besser für Kopf-Augen.
  * **`0,96"` SPI IPS TFT (`80×160`, ST7735, `~30×24 mm`, 65k RGB):** Kompakte Echtfarb-Option für die Heck-Schräge.
  * **`1,54"` SPI IPS TFT (`240×240`, ST7789, `32×44 mm`, 65k RGB, `CS`-Pin herausgeführt, ~7,50 €/Stk.):** Zu groß für die schmale Heckspitze (`X = -102..-128`), aber passend für die breite freie Front-Canopy-/Oberdeck-Zone (`X = +52..+98`) oder ein künftiges Kopf-Visier.
  * **Multi-Display-Bus-Architektur (0 % Echtzeit-Blockade):** Dedizierte zusätzliche Hardware-I²C-Busse am Pi 4 (`i2c-3`, `i2c-4`, `i2c-5` via `dtoverlay`) oder Hardware-**SPI0 (`CE0`/`CE1`)** strikt getrennt vom Echtzeit-Bus `i2c-1` (`50–100 Hz` Servo-/ADC-/IMU-Regelschleife bleibt unbeeinflusst; Stromaufnahme `~15–25 mA` pro OLED, `~30–50 mA` pro IPS TFT).
- [x] **Canopy-Magnetbefestigung an den 4 Pfeilern (`±48, ±36 mm`) ausdetaillieren (`Ø5 × 2 mm` Neodym + Selbstzentrierung):**
  * **Umgesetzt in [`generate_chassis_rpi_mount.py`](../../../scripts/v2/generate_chassis_rpi_mount.py), [`generate_chassis_canopy.py`](../../../scripts/v2/generate_chassis_canopy.py) & [`generate_chassis_assembly.py`](../../../scripts/v2/generate_chassis_assembly.py):**
    * **Untere Pfeiler (`chassis_rpi_mount.FCStd`):** Horizontale Stirnfläche bei $Z = 72{,}10\,\text{mm}$ ($\varnothing 8{,}00\,\text{mm}$, $45^\circ \times 0{,}80\,\text{mm}$ Einführfase), zentrierte $\varnothing 5{,}25 \times 2{,}15\,\text{mm}$ Magnettasche ($Z = 69{,}95\dots 72{,}10\,\text{mm}$) mit $\varnothing 1{,}80\,\text{mm}$ Kleber-/Entlüftungsbohrung.
    * **Obere Canopy-Dome (`chassis_canopy.FCStd`):** Monolithisch innen angeformte Zentrierbecher ($r_a = 5{,}40\,\text{mm}$, streng innerhalb `loft_outer` beschnitten $\rightarrow$ 100 % glatte Außenhaut!) mit $45^\circ$-Trichtereinlauf ($r = 4{,}70 \rightarrow 4{,}20\,\text{mm}$, $0{,}20\,\text{mm}$ Spielpassung über dem Pfeiler), $0{,}15\,\text{mm}$ Axialspalt bei $Z = 72{,}25\,\text{mm}$ und nach unten geöffneter $\varnothing 5{,}25 \times 2{,}15\,\text{mm}$ Magnettasche ($Z = 72{,}25\dots 74{,}40\,\text{mm}$, $\ge 3{,}3\,\text{mm}$ Restwandstärke nach außen).
    * **COTS-Referenz & Verifikation:** 8× [`magnet_5x2.FCStd`](../../cots/magnet_5x2.FCStd) in `chassis_assembly.FCStd` verlinkt (`0,0000 mm³` Kollision über alle 24 Baugruppen-Komponenten, `162/162` CAD-Links OK; kompaktes $\varnothing 5 \times 2\,\text{mm}$ Format minimiert das Streufeld zum Front-BNO085).
- [ ] **Künftige Front-Hals-/Kopf-Integration im reservierten Überhang (`X = +85..+135 mm`):**
  * Nutzung des erhaltenen Front-Schwalbenschwanzes & der vorderen M3-Spacer (`+128, ±12`) für bionischen Kopf (optional mit Stereo-Display-Augen, CSI-Kamera und Front-ToF).





