# Lasius Hexapod – Verkabelungs- und Kabelbaum-Dokumentation (WireViz)

Dieses Verzeichnis enthält die vollständige Kabelbaum- und Verdrahtungsplanung des **Lasius Hexapod Roboters** im **WireViz („Cabling as Code“)** Format.

---

## 1. Verwendete Hardware-Komponenten

| Komponente | Anzahl | Funktion & Spezifikation |
| :--- | :---: | :--- |
| **TCA9548A** | 1× | 8-Kanal I2C-Multiplexer (1.8V–5V, Logik auf 3.3V). Adresse per Lötbrücke an `A0` auf **`0x71`** konfiguriert. |
| **ADS1115** | 6× | 16-Bit 4-Kanal Präzisions-ADCs (1 Board pro Bein). Alle auf Standard-Adresse **`0x48`** an den isolierten Sub-Kanälen `CH0` bis `CH5`. |
| **100 nF MLCC** | 18–24× | 0,1 µF 50V monolithische Vielschicht-Keramikkondensatoren als Tiefpass-Entstörfilter direkt zwischen `Ax` und `GND`. |
| **Reely NR-645 MG BB** | 18× | Metallgetriebe-Servos (3 pro Bein: Coxa, Femur, Tibia). Interner Schleiferkontakt (Weiß) herausgeführt für Closed-Loop Feedback. |
| **PCA9685** | 2× | 16-Kanal 12-Bit PWM-Servotreiber auf Haupt-I2C-Bus (`0x40` Links, `0x42` Rechts). |
| **Omron D2F-L** | 6× | Taktile Mikroschalter in den Fußspitzen an Pin `A3` des jeweiligen Bein-ADS1115. |

---

## 2. Pläne & Diagramme

### Plan 1: `01_i2c_sensor_bus_topology.yml`
* **Zweck:** Visualisiert die I2C-Master-Hub-Topologie vom Raspberry Pi über den TCA9548A-Multiplexer zu den 6 Bein-ADCs.
* **Kanalzuordnung:**
  * `CH0`: Linkes Vorderbein (LF, `0x48`)
  * `CH1`: Linkes Mittelbein (LM, `0x48`)
  * `CH2`: Linkes Hinterbein (LR, `0x48`)
  * `CH3`: Rechtes Vorderbein (RF, `0x48`)
  * `CH4`: Rechtes Mittelbein (RM, `0x48`)
  * `CH5`: Rechtes Hinterbein (RR, `0x48`)

### Plan 2: `02_single_leg_feedback_harness.yml`
* **Zweck:** Detaillierter Kabelbaum für ein einzelnes 3-DOF-Bein.
* **Signale & Filter:**
  * `A0`: Coxa Servo Poti-Schleifer + 100 nF gegen GND
  * `A1`: Femur Servo Poti-Schleifer + 100 nF gegen GND
  * `A2`: Tibia Servo Poti-Schleifer + 100 nF gegen GND
  * `A3`: Fußkontakt-Schalter + 100 nF gegen GND
  * 3-polige PWM- und Laststromzuleitungen (Orange/Rot/Braun) zum PCA9685-Block
* **Grenzfrequenz des Filters:**
  $$f_c = \frac{1}{2 \pi \cdot R_{\text{poti}} \cdot C} \approx \frac{1}{2 \pi \cdot 2500\,\Omega \cdot 100\,\text{nF}} \approx 636\,\text{Hz}$$
  *(Filtert hochfrequente PWM-Schaltimpulse und Motorkommutierungs-Rauschen wirksam heraus).*

### Plan 3: `03_power_distribution.yml`
* **Zweck:** Stromversorgung, getrennte Spannungsregler und gemeinsame Sternmasse (Star-GND).
* **Zweige:**
  * 2S/3S LiPo $\to$ 15A Hauptschalter
  * High-Current UBEC (6.0V 15A Peak) $\to$ Servo V+ Klemmen beider PCA9685
  * Step-Down (5.1V 4A) $\to$ Raspberry Pi 4 Logik
  * Gemeinsamer Masse-Sternpunkt verhindert Ground-Bounces zwischen Servolast und ADC-Sensorik.

---

## 3. Diagramme & Stücklisten neu generieren

Alle Pläne können jederzeit ohne Installation mit einem einzigen Befehl kompiliert werden:

```bash
cd hardware/electronics/wiring
uv run wireviz 01_i2c_sensor_bus_topology.yml
uv run wireviz 02_single_leg_feedback_harness.yml
uv run wireviz 03_power_distribution.yml
```

WireViz erzeugt für jede Datei automatisch:
* `.svg`: Skalierbare Vektorgrafik für Web & Dokumentation
* `.png`: Rastergrafik zur schnellen Vorschau
* `.html`: Interaktiver Schaltplan mit klickbaren Komponenten
* `.bom.tsv`: Tabellarische Stückliste (Material, Längen, Aderquerschnitte)
