# Lasius Sensor Hub & 3.3V / GND Distribution Carrier Board v2

---

[Project Index](../../../../README.md) | [Electronics Roadmap](../../TODO.md) | [Wiring Plan](../../../../docs/hardware/wiring_plan.md) |<br>
[Wiring Harness Spec](../../WIRING_HARNESS_SPEC.md) | [Chassis Core Assembly](../../../mechanics/models/custom/v2/chassis_core_assembly.FCStd)

---

Dieses KiCad-Projekt umfasst das vollständige Design, den Bestückungsplan und die fertigen Fertigungsdaten (Gerber RS-274X + Excellon Drill) für das zentrale Sensor- und Power-Carrier-Board des **Lasius** Hexapods.

Die Platine sitzt auf den integrierten M2.5-Domen des Zwischenbodens ($Z = 28{,}00\,\text{mm}$) im $24\,\text{mm}$-Spalt zwischen den beiden PCA9685 PWM-Controllern und ist **zu 100 % form- und maßkompatibel zum FreeCAD-Volumenmodell** ([`sensor_hub_board.FCStd`](../../../mechanics/models/custom/v2/parts/chassis/sensor_hub_board.FCStd)).

---

## 1. Board-Spezifikationen

| Parameter | Wert | Beschreibung |
| :--- | :--- | :--- |
| **Abmessungen** | $54{,}0 \times 22{,}0 \times 1{,}60\,\text{mm}$ | Passgenau für den Zwischenboden-Schacht; $R = 2{,}0\,\text{mm}$ Eckenradien. |
| **Lagen** | 2 Lagen (Top + Bottom) | Standard FR4, $35\,\mu\text{m}$ Cu ($1\,\text{oz}$), Matt-Schwarz oder Waldgrün. |
| **Befestigung** | 2× M2.5 Bohrungen | $\varnothing 2{,}7\,\text{mm}$ im Abstand von $26{,}0\,\text{mm}$ ($X = 0{,}0, Y = \pm 13{,}0\,\text{mm}$). |
| **Multiplexer-Sockel** | 2× 12-Pin Buchsenleiste | $2{,}54\,\text{mm}$ Raster, $17{,}54\,\text{mm}$ Reihenabstand für TCA9548A / PW548A. |
| **Adresse** | **`0x71`** (Hardware-Fixed) | `A0` fest auf `3,3 V` verdrahtet; `A1` und `A2` auf `GND`. |
| **Bein-Steckplätze** | 6× 4-Pin Stiftleisten | $2{,}54\,\text{mm}$ THT (oder JST-XH), straight $1:1$ Pinout passend zu V280 ADC. |

---

## 2. Pinbelegung der 4-Pin Bein-Steckplätze

Das Pinout ist **exakt 1:1 identisch zur Reihenfolge auf den ADS1115 (`V280`) Platinen im Femur**, sodass handelsübliche 4-adrige Flachbandleitungen ohne gekreuzte Adern verwendet werden können:

| Pin | Signal | Drahtfarbe ([Master-Farbschema](../../WIRING_HARNESS_SPEC.md)) | Beschreibung |
| :---: | :--- | :--- | :--- |
| **1** | **`3,3 V`** | **Rot** | Geregelte Logikspannung vom Pi 4 (Pin 1) |
| **2** | **`GND`** | **Schwarz** | Star-GND Referenzmasse |
| **3** | **`SCx`** | **Gelb** | Multiplexer I²C-Takt (`SCL`) für Kanal $x$ |
| **4** | **`SDx`** | **Kanal-Farbe** | Multiplexer I²C-Daten (`SDA`) für Kanal $x$ |

### Kanal-Zuordnung & Kabelfarben:
* **Bank 1 ($+Y$, zeigt nach links):**
  * `J_LF` (CH0): Blau (`SD0`) + Gelb (`SC0`) $\rightarrow$ Bein Vorne Links (LF)
  * `J_LM` (CH1): Grün (`SD1`) + Gelb (`SC1`) $\rightarrow$ Bein Mitte Links (LM)
  * `J_LR` (CH2): Violett (`SD2`) + Gelb (`SC2`) $\rightarrow$ Bein Hinten Links (LR)
  * `J_RPI` (Main Bus): Blau (`SDA`) + Gelb (`SCL`) $\rightarrow$ Haupteingang vom Raspberry Pi
  * `J_PCA_L`: 2-Pin Versorgungsabgang (`3,3V / GND`) zum linken PCA9685-Controller
* **Bank 2 ($-Y$, zeigt nach rechts):**
  * `J_FR` (CH3): Orange (`SD3`) + Gelb (`SC3`) $\rightarrow$ Bein Vorne Rechts (FR)
  * `J_RM` (CH4): Weiß (`SD4`) + Gelb (`SC4`) $\rightarrow$ Bein Mitte Rechts (RM)
  * `J_RR` (CH5): Grau (`SD5`) + Gelb (`SC5`) $\rightarrow$ Bein Hinten Rechts (RR)
  * `J_AUX`: 4-Pin Erweiterung für CH6 (INA228 Stromsensor, Braun) und CH7 (ToF)
  * `J_PCA_R`: 2-Pin Versorgungsabgang (`3,3V / GND`) zum rechten PCA9685-Controller

---

## 3. Stückliste (Bill of Materials / BOM)

| Ref | Bauteil | Gehäuse / Raster | Spezifikation / Notiz |
| :--- | :--- | :--- | :--- |
| **U1** | TCA9548A / PW548A | Breakout-Modul | 8-Kanal I²C Multiplexer Modul (violett) |
| **J_TCA_L, J_TCA_R** | 2× 12-Pin Buchsenleiste | $2{,}54\,\text{mm}$ THT, 1-reihig | Bauhöhe $4{,}0\dots 8{,}5\,\text{mm}$ zum werkzeuglosen Stecken |
| **J_LF, J_LM, J_LR** | 3× 4-Pin Stiftleiste | $2{,}54\,\text{mm}$ THT (oder JST-XH) | Linke Beinbank ($+Y$) |
| **J_FR, J_RM, J_RR** | 3× 4-Pin Stiftleiste | $2{,}54\,\text{mm}$ THT (oder JST-XH) | Rechte Beinbank ($-Y$) |
| **J_RPI, J_AUX** | 2× 4-Pin Stiftleiste | $2{,}54\,\text{mm}$ THT | Pi Haupteingang & Sensor-Erweiterung |
| **J_PCA_L, J_PCA_R** | 2× 2-Pin Stiftleiste | $2{,}54\,\text{mm}$ THT | Controller Logik-Versorgung |
| **C1** | $10\,\mu\text{F}$ Elko / Tantal | Radial $D = 5{,}0\,\text{mm}$, RM $2{,}5\,\text{mm}$ | $\ge 6{,}3\,\text{V}$ Entkopplung auf der 3,3V-Schiene |
| **C2** | $100\,\text{nF}$ Keramikkondensator | Disc / MLCC RM $2{,}5\,\text{mm}$ | Hochfrequenz-Entstörung nah am Multiplexer |
| **H1, H2** | 2× M2.5 Schrauben | Zylinderkopf / Linsenkopf | Befestigung in den Monocoque-Domen ($L = 6\dots 8\,\text{mm}$) |

---

## 4. Fertigung & Bestellung (Ready-to-Order)

Die produktionsfertigen Gerber-Daten liegen gepackt bereit unter:  
**[`sensor_hub_gerbers.zip`](sensor_hub_gerbers.zip)**

### Bestellung bei JLCPCB:
1. `sensor_hub_gerbers.zip` per Drag & Drop auf [jlcpcb.com](https://jlcpcb.com) hochladen.
2. Abmessungen werden automatisch erkannt: **$54 \times 22\,\text{mm}$**, 2 Lagen.
3. PCB Color nach Wunsch wählen (Empfehlung: **Matte Black** passend zum Anthrazit PA-CF Chassis).
4. Fertigungskosten: ca. **2 $ für 5 Stück**.

### Bestellung bei AISLER:
1. `sensor_hub_gerbers.zip` (oder direkt die `.kicad_pcb`-Datei) auf [aisler.net](https://aisler.net) hochladen.
2. „Beautiful PCBs“ auswählen (Lieferzeit: **3–4 Werktage** aus Deutschland/Niederlande).
