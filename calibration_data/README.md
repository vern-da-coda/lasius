# Lasius – Servo Potentiometer Calibration Data

Dieses Verzeichnis enthält die experimentell ermittelten Kalibrierdaten und Regressionsmodelle für das analoge Positionsfeedback (Schleiferspannung des internen Potentiometers) der Reely NR-645 MG BB Servomotoren.

---

## 1. Übersicht & Messaufbau

- **Prüfling:** Reely NR-645 MG BB Analog-Standardservo
- **Modifikation:** Abgriffleitung direkt an den Schleifer (Wiper) des internen Potentiometers gelötet.
- **Signal:** Analogspannung gegen Servomasse (GND).
- **Ansteuerung:** PCA9685 Board 1 (`0x40`), Steckplatz Kanal 15 bei 50 Hz PWM.
- **Logikspannung:** 3,3 V (Raspberry Pi 4).
- **Lastspannung:** 5,0–6,0 V (Labornetzteil).
- **Messung:** 9 Stufen von $-60{,}0^\circ$ bis $+60{,}0^\circ$ in $15^\circ$-Schritten via [`scripts/pot_calibration_wizard.py`](../scripts/pot_calibration_wizard.py).

---

## 2. Kalibrierergebnisse (Reely NR-645 MG BB)

### 2.1 Modellparameter (Lineare Regression)

| Parameter | Wert | Einheit | Erläuterung |
| :--- | :--- | :--- | :--- |
| **Linearitätsgüte ($R^2$)** | **`0.999591`** | -- | $99{,}96\,\%$ Linearität über den gesamten Bereich |
| **Steigung / Empfindlichkeit ($m$)** | **`+7.589`** | $\text{mV} / ^\circ$ | Spannungshub pro Grad Stellwinkel ($0{,}007589\,\text{V}/^\circ$) |
| **Umrechnungsfaktor ($k$)** | **`131.772`** | $^\circ / \text{V}$ | Winkeländerung pro Volt |
| **Nullpunkt-Spannung ($V_{0^\circ}$)** | **`1.5633`** | $\text{V}$ | Spannung bei $0{,}0^\circ$ (1500 µs Mittelstellung) |
| **Max. Modellabweichung** | **`±1.45`** | $^\circ$ | Maximaler Winkelfehler bei linearer Approximation |
| **Max. Spannungsfehler** | **`±11.0`** | $\text{mV}$ | Maximale Residuen-Spannung |

### 2.2 Closed-Loop Berechnungsformel

Zur Rekonstruktion des physikalischen Winkels aus einem ADC-Messwert:

$$\theta(V) = (V_{\text{ADC}} - 1{,}5633\,\text{V}) \cdot 131{,}772^\circ$$

Umgekehrt zur Soll-Spannungsprüfung:

$$V(\theta) = 1{,}5633\,\text{V} + (\theta \cdot 0{,}007589\,\text{V}/^\circ)$$

---

## 3. Messwerttabelle

| Schritt | Soll-Winkel | PWM-Puls | Gemessen ($V$) | Modell ($V$) | Residuum ($\text{mV}$) | Winkelfehler |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | $-60{,}0^\circ$ | $1166{,}7\,\mu\text{s}$ | **1,11 V** | $1{,}108\,\text{V}$ | $+2{,}0\,\text{mV}$ | $+0{,}26^\circ$ |
| 2 | $-45{,}0^\circ$ | $1250{,}0\,\mu\text{s}$ | **1,22 V** | $1{,}222\,\text{V}$ | $-1{,}8\,\text{mV}$ | $-0{,}24^\circ$ |
| 3 | $-30{,}0^\circ$ | $1333{,}3\,\mu\text{s}$ | **1,34 V** | $1{,}336\,\text{V}$ | $+4{,}3\,\text{mV}$ | $+0{,}57^\circ$ |
| 4 | $-15{,}0^\circ$ | $1416{,}7\,\mu\text{s}$ | **1,44 V** | $1{,}450\,\text{V}$ | $-9{,}5\,\text{mV}$ | $-1{,}25^\circ$ |
| 5 | $0{,}0^\circ$ | $1500{,}0\,\mu\text{s}$ | **1,57 V** | $1{,}563\,\text{V}$ | $+6{,}7\,\text{mV}$ | $+0{,}88^\circ$ |
| 6 | $+15{,}0^\circ$ | $1583{,}3\,\mu\text{s}$ | **1,68 V** | $1{,}677\,\text{V}$ | $+2{,}8\,\text{mV}$ | $+0{,}37^\circ$ |
| 7 | $+30{,}0^\circ$ | $1666{,}7\,\mu\text{s}$ | **1,78 V** | $1{,}791\,\text{V}$ | $-11{,}0\,\text{mV}$ | $-1{,}45^\circ$ |
| 8 | $+45{,}0^\circ$ | $1750{,}0\,\mu\text{s}$ | **1,91 V** | $1{,}905\,\text{V}$ | $+5{,}2\,\text{mV}$ | $+0{,}68^\circ$ |
| 9 | $+60{,}0^\circ$ | $1833{,}3\,\mu\text{s}$ | **2,02 V** | $2{,}019\,\text{V}$ | $+1{,}3\,\text{mV}$ | $+0{,}18^\circ$ |

---

## 4. Dateien in diesem Verzeichnis

- [`ANSCHLUSSPLAN_18DOF_CLOSED_LOOP.md`](ANSCHLUSSPLAN_18DOF_CLOSED_LOOP.md): **Haupt-Spezifikation:** Vollständiger 18-Kanal Anschlussplan (TCA9548A Mux + 6× ADS1115), Lötbrücke `A0` (`0x71`), Tiefpassfilter & Python-Treiber.
- [`servo_ch15_pot_calibration.json`](servo_ch15_pot_calibration.json): Maschinenlesbare Roh- und Modelldaten für Softwareintegration.
- [`servo_ch15_pot_calibration.csv`](servo_ch15_pot_calibration.csv): Tabellarischer Export für Tabellenkalkulationen und Python-Datenanalyse.
- [`README.md`](README.md): Dokumentation und Formeln.
