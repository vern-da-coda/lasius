# Hexapod:Lasius – Mechanik & Hardware Style-Guide

---

[Project Index](../../README.md) | [Hardware Documentation](../README.md) | [Mechanics Documentation](README.md) | [v2 Models Backlog](models/custom/v2/TODO.md) | [Closed Loop Plan](../../docs/hardware/closed_loop_plan.md)

---

Dieses Dokument definiert die verbindlichen gestalterischen, geometrischen und fertigungstechnischen Richtlinien für alle mechanischen Bauteile des **Hexapod:Lasius** (Generation v2 und Folgegenerationen).

Das Ziel ist eine **konsistente bionische Formensprache**, maximale strukturelle Steifigkeit bei minimalem Gewicht sowie reproduzierbare Fertigungsqualität im FDM-3D-Druck (PETG).

---

## 1. Bionische Design-DNA (*Form follows Load & Bio-Motion*)

Das visuelle und konstruktive Leitbild von Lasius ist die Waldameise (*Lasius niger*):

* **Keine rein dekorativen Kanten:** Jede Wölbung, Versteifungsrippe oder Aussparung folgt einem realen Kraftfluss oder Funktionsbedarf (Drehmomentabstützung, Freigang, Kabelführung, Kaminbelüftung).
* **Fließende Übergänge ($G^1$-Stetigkeit):** Bauteile vermeiden abrupte 90°-Sprünge oder scharfkantige Querschnittsänderungen. Übergänge zwischen Funktionsabschnitten erfolgen über stetige Tangentenkurven ($G^1$).
* **Funktionale Kapselung:** Sensoren (z. B. ADS1115 im Femur, VL53L5CX in der Belly Pan) und Leitungen werden formschlüssig in die Struktur integriert, statt nachträglich außen aufgeschraubt zu werden.

---

## 2. Gliedmaßen- & Wangen-Geometrie (Limb & Joint Morphology)

```
       Gelenkkopf (Apex)
           (X_axis, Z_max)
               /-----\
              /       \  <-- S-Kurve 2
 S-Kurve 1   /         \____        Taille (Waist)
   /--------/               \______/-----\
  /                                       \_____  Käfig-Dach (Z_cage_top)
 (                                              |=========================
  \                                       /-----' Käfig-Boden (Z_cage_bot)
   \--------\               /------\-----/
             \         /----'
              \       /  <-- S-Kurve 4
               \-----/
           Gegenlager (Apex)
           (X_axis, Z_min)
```

### 2.1 Gelenkköpfe & Drehachsen
* **Scheitelpunkte (Apices):** Der höchste Punkt der oberen Wange ($Z_{\text{max}}$) und der tiefste Punkt des Gegenlagers ($Z_{\text{min}}$) liegen immer exakt auf der geometrischen Drehachse des Gelenks ($X_{\text{axis}}$).
* **Auslaufende Spitzen:** Gabel- und Wangenenden (wie bei $X = 0{,}0\,\text{mm}$ an der Coxa) dürfen nicht als plane 90°-Kappschnitte enden, sondern laufen über definierte Radien ($R \ge 3\text{--}5\,\text{mm}$) oder stetige Halbbögen organisch aus.

### 2.2 Anatomische Taillierung (Waist Curve)
Zwischen zwei Gelenken verjüngt sich ein Segment nicht monoton, sondern bildet eine **anatomische Taille** (Sehnenprofil):
1. **Oberer Kamm:** Fällt hinter dem Scheitelpunkt sanft unter die Dachhöhe des Folgekörpers ab, bildet eine leichte Einschnürung (Waist) und schwingt dann tangential auf die Anschlusshöhe auf.
2. **Unterer Kamm:** Steigt hinter dem Gegenlager an, bildet eine korrespondierende Taillierung und läuft tangential in den Boden des Folgekörpers ein.
3. **Mathematische Definition:**
   * Alle Übergänge werden aus Paaren gegenläufiger Kreisbögen mit stetiger Wendepunkt-Tangente ($G^1$) konstruiert (`make_s_curve_edges`).

---

## 3. Fachwerk- & Gewichtsreduktions-Standards (Truss Architecture)

Wo geschlossene Vollwände statisch nicht erforderlich sind, werden standardisierte bionische Fachwerkfenster eingesetzt.

| Parameter | Standard-Wert | Begründung |
| :--- | :--- | :--- |
| **Stegbreite ($w_{\text{strut}}$)** | **$2{,}50\,\text{mm}$** | Exakt 6 Perimeter bei $0{,}40\,\text{mm}$ Nozzle / $0{,}42\,\text{mm}$ Linienbreite; 100 % massiv gedruckt ohne Lücken. |
| **Fachwerk-Winkel ($\alpha$)** | **$45{,}0^\circ$** | Garantiert stützstrukturfreien FDM-Druck; optimale Schub- und Biegesteifigkeit. |
| **Horizontale Strut-Delta ($\Delta X_{45}$)** | **$3{,}536\,\text{mm}$** | $w \cdot \sqrt{2}$; Versatz für parallele 45°-Flanken. |
| **Eckenverrundung ($R_{\text{fillet}}$)** | **$1{,}40\text{--}2{,}00\,\text{mm}$** | Beseitigt Kerbspannungen (*Notch-Stress Reduction*) an allen Dreiecks- und Trapezecken. |
| **Flanken-Topologie** | **Warren-Truss** | Abwechselnde $45^\circ$-Dreiecke für schlanke Biegebalken (Tibia, Coxa-Wangen). |
| **Zentral-Topologie** | **A-Truss / Chevrons** | Pfeilförmige Chevrons mit zentralem First für Torsionsbrücken und Rumpfelemente. |

---

## 4. Kanten-, Fasen- und Belüftungs-Hierarchie

### 4.1 Außenkanten & Lichtkanten (Tactile Fillets)
* **Standard-Außenradius:** Exponierte Außenkanten entlang von Wangen, Kämmen und Rumpfschalen erhalten ein **$R = 1{,}0\text{--}1{,}5\,\text{mm}$ Fillet**.
* **Zweck:** Angenehme Griffigkeit ohne scharfe Grate, verbesserte Schichthaftung an Rändern und hochwertige Lichtkanten im Rendering und Realteil.

### 4.2 Funktions- & Schutzfasen (Chamfers)
* **Kabeldurchführungen:** $45^\circ \times 1{,}0\text{--}1{,}5\,\text{mm}$ Einlauffasen an allen Kabeltunnels und Durchbrüchen (Schutz vor Durchscheuern der Servolitzen im Dauerbetrieb).
* **Steckermontagen & Fügefalze:** $45^\circ \times 0{,}5\,\text{mm}$ Fügefasen für spielfreies Ineinanderschieben von Kappen und Deckeln.

### 4.3 Bionische Belüftungs-Louvers (`>>>`)
Elektronikkammern (BCM2711 SoC, Femur-ADC-Kammer) nutzen einheitliche bionische Kamin-Lamellen:
* **Form:** $45^\circ$ nach vorn gepfeilte Schlitze mit abgerundeten Kapsel-/Pillenenden.
* **Geometrie:** Schlitzbreite $2{,}5\text{--}3{,}0\,\text{mm}$, Lamellensteg $3{,}0\text{--}4{,}0\,\text{mm}$, Tiefenwinkel $45^\circ$ für regengeschützte passive Konvektion.

---

## 5. Fertigungsgerechte Konstruktion (DfAM für PETG)

Alle mechanischen Eigenkonstruktionen sind primär für den FDM-Druck aus **PETG** optimiert.

### 5.1 Wandstärken-Klassen
* **Klasse 1 – Leichte Abdeckungen & Hauben:** $1{,}60\text{--}2{,}00\,\text{mm}$ (4 Perimeter, formsteif durch Doppelkrümmung).
* **Klasse 2 – Fachwerkstreben & Rippen:** $2{,}50\,\text{mm}$ (massiv aus Perimetern aufgebaut).
* **Klasse 3 – Gelenkwangen & tragende Hauptträger:** $5{,}00\text{--}6{,}20\,\text{mm}$ (maximale Torsions- und Biegesteifigkeit).
* **Klasse 4 – Servohorn-Aufnahmen & Drehmomenteinleitung:** $\ge 3{,}50\text{--}4{,}50\,\text{mm}$ massives Material um Schraubenkränze.

### 5.2 Normteil-Sitze & Passungen
* **Kugellager 684ZZ ($\varnothing 8 \times 3\,\text{mm}$):**
  * Bohrung: $\varnothing 8{,}05\,\text{mm}$ (leichte Presspassung für FDM).
  * Bundkragen: $R = 3{,}30\,\text{mm}$ ($0{,}30\,\text{mm}$ Überstand über Lageraußenring), damit nur der Innenring geklemmt wird und das Gelenk leichtgängig dreht.
* **Flachmutter DIN 439 M4 (Gegenlager-Gewindesitz):**
  * Sechskanttasche: Schlüsselweite $SW = 7{,}10\,\text{mm}$, Taschentiefe $2{,}40\,\text{mm}$.
  * Fester Anschlagkragen: $0{,}60\,\text{mm}$ Restwand zur Durchgangsbohrung ($\varnothing 4{,}10\,\text{mm}$).
* **Gewindeeinsätze (Ruthex M2 / M2.5 / M3):**
  * Bohrungsdurchmesser exakt nach Hersteller-Datenblatt mit $8^\circ$-Einlaufsenkung für sauberes thermisches Einschmelzen.

---

## 6. Farb- & Materialkodierung (Visual Identity in CAD & Digital Twin)

Zur eindeutigen visuellen Unterscheidbarkeit in FreeCAD und im Three.js Digital Twin gilt folgende Farbpalette:

| Baugruppe / Rolle | Farbe | RGB-Werte | Material / Finish |
| :--- | :--- | :--- | :--- |
| **Strukturteile Chassis & Beine** | Anthrazit / Schiefergrau | `(0.20, 0.22, 0.25)` | PETG matt / Carbon |
| **Gelenkwangen & Halterungen** | Technisches Mittelblau | `(0.12, 0.35, 0.65)` | PETG matt |
| **Wartungsdeckel & Kappen** | Graphitschwarz | `(0.15, 0.15, 0.18)` | PETG Feinstruktur |
| **Plexiglas-Canopy** | Eisblau-Transluzent (55 % Alpha) | `(0.85, 0.92, 0.98)` | Acrylglas / Tiefzieh |
| **LiPo-Akku (COTS)** | Signalgold / Gelb | `(0.95, 0.75, 0.10)` | Schrumpfschlauch |
| **PWM-Servotreiber PCA9685** | Adafruit-Signalblau | `(0.04, 0.38, 0.88)` | PCB |
| **I2C-Multiplexer TCA9548A** | Signalviolett | `(0.58, 0.15, 0.75)` | PCB |
| **Raspberry Pi 4 Model B** | Signalgrün | `(0.10, 0.55, 0.25)` | PCB |

---

## 7. Parametrischer Code-Standard (Hardware-as-Code)

Jedes CAD-Generatorskript in `hardware/mechanics/scripts/v2/` folgt dieser Struktur:
1. **Konstanten-Block am Dateianfang:** Keine hartcodierten magischen Zahlen im Modellierungscode; alle Abmessungen ($W_{\text{STRUT}}$, $R_{\text{FILLET}}$, Achsabstände) werden oben zentral deklariert.
2. **Modulare Geometrie-Helfer:**
   * `make_s_curve_edges(p1, p2)` für $G^1$-stetige S-Kurven.
   * `make_filleted_polygon_2d(pts, r_list)` für verrundete Fachwerkfenster.
   * `make_hex_nut_pocket_z(cx, cy, z1, z2, sw)` für Mutternsitze.
3. **Synchroner Export:** Jedes Skript speichert das FreeCAD-Dokument (`.FCStd`) und exportiert im selben Durchlauf synchrone `.step`- und `.stl`-Dateien in die korrespondierenden Ordner unter `hardware/mechanics/export/`.
