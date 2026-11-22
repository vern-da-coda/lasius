# Lasius Elektronik & Verkabelung – Backlog & Testbench-Status

---

[Project Index](../../README.md) | [Hardware Documentation](../README.md) | [Wiring & Harnesses](wiring/README.md) | [Software TODO](../../software/TODO.md) |<br>
[Closed Loop Plan](../../docs/hardware/closed_loop_plan.md) | [Bring-Up Status](../../docs/hardware/testbench_bringup_status.md) | [Wiring Plan](../../docs/hardware/wiring_plan.md)

---

Dieses Dokument bündelt den aktuellen Testbench-Stand, Hardware-Befunde, das verbindliche Farbschema sowie alle offenen Elektronik-, Verkabelungs- und Integrations-Aufgaben für den **Lasius** Hexapod (`hardware/electronics/`).

> [!IMPORTANT]
> **Rollennamen der Platinen im Aufbau:**
> * **Controller** = PCA9685 PWM-Servotreiber (`0x40` links, `0x42` rechts)
> * **Multiplexer** = PCA9548A / TCA9548A 8-Kanal I²C-Multiplexer (`0x71` via `A0 → 3,3 V`)
> * **Wandler** = ADS1115 (`V280`) 4-Kanal ADC (`0x48` via `ADDR → GND`)

---

## 1. Bereits auf der Testbench verifiziert (`bkhexapod`)

- [x] **Stufe 1 – Hauptbus Daisy-Chain (`Pi 4 → Controller [0x40] → Multiplexer [0x71]`):**  
  * Violettes `PCA9548A` (`PW548A`)-Breakout ohne frontseitige Lötjumper; `R6/R1/R2` (`10 kΩ`) ziehen `A0/A1/A2` auf `GND`, `R3/R4/R5` (`10 kΩ`) ziehen `RST/SDA/SCL` auf `VIN`.
  * `VIN` + `A0` auf `3,3 V` gesetzt → stabile Erkennung auf **`0x71`** neben **Controller `0x40`** (ohne Boot-Kollision durch `0x70 ALLCALL`), alle 8 Kanäle (`CH0–CH7`) sauber umschaltbar.
- [x] **Stufe 2 – Erster Wandler (`0x48`) auf Multiplexer `CH0` (`LF`):**  
  * Verifiziert via [`test_electronics.py`](../../scripts/bench/test_electronics.py) (`--step 5`, `--scan`).
  * Analogbereich an `Wandler A0` kalibriert geprüft: `GND` = `0,0000 V` (`raw = 0`), `3,3 V` = `3,3100 V` (`raw = 26480`).
  * **Hardware-Befund (`V280`-Platine):** Auf der Platine liegt **`SCL` vor `SDA`** (`VDD | GND | SCL | SDA | ADDR | ALRT | A0–A3`, siehe [`ads1115_reference.jpg`](../mechanics/drawings/references/ads1115_reference.jpg)); die untersuchte Charge liefert zudem linksbündige **12-Bit**-Werte (`16 Counts = 2,0 mV/Schritt`, entspricht `~0,26°` am Reely NR-645 – für Joint-Feedback ausreichend).
- [x] **Stufe 3 – Erster Closed-Loop Servo-Poti-Test (`Controller CH0` ↔ `Wandler A0`):**  
  * `Star-GND` + `6,0 V` Labornetzteil am **Controller**; Live-Sweep `−60°` bis `+60°` in `15°`-Schritten (ohne externen `100 nF`-Filter):  
    *$R^2 = 0{,}999876$*, Steigung *$+7{,}530\,\text{mV}/^\circ$* (`132,802 °/V`), $V_{0^\circ} = 1{,}5590\,\text{V}$, max. Modellabweichung *$5{,}1\,\text{mV}$* (`0,68°`), Umkehr-Differenz bei `0°` *$-0{,}2\,\text{mV}$*, Standrauschen `0,00–1,03 mV`.
  * Referenzvergleich: [`servo_ch15_pot_calibration.json`](../../data/bench/servo_ch15_pot_calibration.json).

---

## 2. Verbindliches Master-Farbschema (Referenz für alle Ausbauschritte)

| Bereich / Signal | Farbe | Gilt für |
| :--- | :--- | :--- |
| **`3,3 V` Logik** *(Anker)* | **Rot** | `Pi Pin 1/17`, **Controller** `VCC`, **Multiplexer** `VIN & A0`, **Wandler** `VDD` *(niemals `5 V` / `V+`!)* |
| **`GND` & `ADDR`** *(Anker)* | **Schwarz** | Alle Massepunkte, **Wandler** `ADDR → GND`, **`Star-GND`** zum `6 V`-Netzteil |
| **`SCL` / `SCx` Takt** *(Anker)* | **Gelb** | Jede Taktleitung (`SCL1`, **Controller** `SCL`, `SC0–SC7`, **Wandler** `SCL`) |
| **Hauptbus + `CH0` (`LF`) Daten** | **Blau** | `Pi SDA1` → **Controller** `SDA` → **Multiplexer** `SDA` & `SD0` → **Wandler** `LF` (`CH0`) |
| **`CH1` (`LM`) Daten** | **Grün** | **Multiplexer** `SD1` → **Wandler** `LM` |
| **`CH2` (`LR`) Daten** | **Violett** | **Multiplexer** `SD2` → **Wandler** `LR` |
| **`CH3` (`RF`) Daten** | **Orange** | **Multiplexer** `SD3` → **Wandler** `RF` |
| **`CH4` (`RM`) Daten** | **Weiß** | **Multiplexer** `SD4` → **Wandler** `RM` |
| **`CH5` (`RR`) Daten** | **Grau** | **Multiplexer** `SD5` → **Wandler** `RR` |
| *(`CH6` Reserve Daten)* | ***Braun*** | *Stromsensor (`INA228`)* |
| **Analog `A0` (`Coxa` Poti)** | **Weiß** | Servo-Schleifer Coxa → **Wandler** `A0` (Poti-Leitung aus Servo immer Weiß) |
| **Analog `A1` (`Femur` Poti)** | **Weiß** | Servo-Schleifer Femur → **Wandler** `A1` (Poti-Leitung aus Servo immer Weiß) |
| **Analog `A2` (`Tibia` Poti)** | **Weiß** | Servo-Schleifer Tibia → **Wandler** `A2` (Poti-Leitung aus Servo immer Weiß) |
| **Analog `A3` (`Foot` Switch)** | **Orange** | Mikroschalter `NO` → **Wandler** `A3` (`COM → GND` = **Schwarz**) |

*(Am 6-Pin-Seitenheader des **Controllers** bleiben `OE` offen und **`V+` strikt unverbunden**, da auf `V+` die `6 V`-Servospannung liegt.)*

---

## 3. Offene Aufgaben (Backlog)

### AP 1: Zentrale `3,3 V / GND`-Verteilerschiene & Chassis-Integration
- [ ] **Verteilerplatine (`3,3 V / GND`-Schiene) für den Roboter entwerfen & löten:**  
  * **Hintergrund:** Der reale violette **Multiplexer** stellt auf `CH0–CH7` nur `SDx / SCx` bereit (keine eigenen `3,3 V / GND`-Pins je Kanal), und jeder **Wandler** besitzt nur `1× VDD` / `1× GND`. Im Vollausbau (6× Bein-**Wandler**, **Multiplexer** `VIN + A0`, `2× Controller`-Logik, später IMU / ToF / Stromsensor) werden ca. **10–13 Abgänge** benötigt.
  * **Umsetzung (Empfehlung):** Kompakte Lochrasterplatine mit gemeinsamer **Rot (`3,3 V`)**- und **Schwarz (`GND`)**-Leiste plus Stützkondensatoren (`100 nF` Keramik + `10 µF`) – idealerweise gleich als Trägerboard für den **Multiplexer** mit **6 verpolsicheren 4-Pin-Steckplätzen (`Rot · Schwarz · Gelb · Kanal-Farbe`)** je Bein.
  * **Strombudget beachten:** Alle genannten I²C-Logik- und Sensor-Boards liegen zusammen grob bei `~60–100 mA` und können direkt über Pi `Pin 1` (+ optional `Pin 17`) versorgt werden (keine stromhungrigen Verbraucher wie LEDs/Displays auf diese Schiene hängen).
- [ ] **`Star-GND`-Konzept sauber umsetzen:**  
  * Hohe `6 V`-Servoströme strikt über die zentrale [`Star_Ground_Bus`](wiring/03_power_distribution.yml)-Schiene direkt zu Batterie / UBECs zurückführen; die `GND`-Schiene des `3,3 V`-Verteilers nur über **genau eine** Referenzverbindung an `Star-GND` koppeln (Schutz vor Erdschleifen / `Ground Bounce`).
- [ ] **Bauraum- & Stecker-Check im Chassis ([`body_assembly.FCStd`](../mechanics/models/custom/v2/body_assembly.FCStd)):**  
  * Einbauplatz, Zugentlastung und vertikale Steckerhöhe der `3,3 V / GND`-Verteilerplatine neben dem **Multiplexer** auf dem Electronics Tray prüfen.

### AP 2: Schaltpläne (`WireViz`) & Dokumentation abgleichen
- [x] **WireViz-Spezifikationen & READMEs an reale Hardware & Master-Farbschema anpassen:**  
  * [`01_i2c_sensor_bus_topology.yml`](wiring/01_i2c_sensor_bus_topology.yml): Reale Belegung des **Multiplexers** (`SDx/SCx` ohne integrierte `3,3 V/GND`-Kanäle), zentrale `3,3 V / GND`-Verteilerschiene (`Dist_3V3_GND_Rail`), Hauptbus-Daisy-Chain (`Pi → Controller Left 0x40 → Controller Right 0x42 → Multiplexer 0x71`) und Pro-Kanal-Farbcode (`Blau/Grün/Violett/Orange/Weiß/Grau + Gelb`) eingepflegt.
  * [`02_single_leg_feedback_harness.yml`](wiring/02_single_leg_feedback_harness.yml): Analoge Adernfarben (`A0/A1/A2 = Weiß` [Poti-Leitung aus den Servos immer Weiß], `A3 = Orange/Schwarz`), Split-Uplink sowie reale `V280`-Pinreihenfolge (`SCL` vor `SDA`) und `ADDR → GND` eingepflegt.
  * [`03_power_distribution.yml`](wiring/03_power_distribution.yml) & [`04_pca9685_servo_distribution.yml`](wiring/04_pca9685_servo_distribution.yml) (`Dist_3V3_GND_Rail` inkl. Einzelreferenz an `Star_Ground_Bus`, einheitliche Platinen-Benennung **Controller / Multiplexer / Wandler**) sowie [`wiring/README.md`](wiring/README.md), [`hardware/README.md`](../README.md) und [`README.md`](../../README.md) aktualisiert.
- [x] **WireViz-Diagramme (`.svg`, `.png`, `.html`, `.bom.tsv`) neu gebaut** (`cd hardware/electronics/wiring && uv run wireviz ...`).
- [ ] **Detail-Dokumentation in `docs/` nachziehen:**  
  * [`docs/hardware/wiring_plan.md`](../../docs/hardware/wiring_plan.md) & [`docs/hardware/testbench_bringup_status.md`](../../docs/hardware/testbench_bringup_status.md) auf den aktuellen Testbench-Stand (Stufe 1–3 abgeschlossen, `V280`, `3,3 V / GND`-Verteilerschiene) aktualisieren.
- [x] **Kanal-Mapping `LR` zwischen Doku & Software vereinheitlichen:**  
  * [`config.yaml`](../../software/lasius-core/src/lasius/core/config.yaml) (`left_rear_*` jetzt symmetrisch auf `CH8–10`, identisch zu `right_rear_*` & [`04_pca9685_servo_distribution.yml`](wiring/04_pca9685_servo_distribution.yml)) inklusive Regressionstest `test_servo_channel_symmetry()` in [`test_config.py`](../../software/lasius-core/tests/test_config.py) vereinheitlicht.

### AP 3: Hardware-Ausbau Testbench & Serienaufbau (18 DOF)
- [ ] **Vollständiges Testbein (`LF` auf `CH0`) am Wandler aufbauen:**  
  * Zweites & drittes Servo-Poti an **`A1` (Weiß, Femur)** und **`A2` (Weiß, Tibia)** sowie den `Omron D2F-L` Fußschalter mit **`10 kΩ` Pull-up (`A3 → 3,3 V`)** an **`A3` (Orange)** + `COM → GND` (**Schwarz**) testen.
- [ ] **Filter-Test (`4× 100 nF` MLCC) unter Volllast eines Beins:**  
  * Rauschen an `A0–A2` prüfen, während alle 3 Servos gleichzeitig unter Last laufen; entscheiden, wie die `100 nF` + `10 kΩ` Passivbauteile platzsparend in die freie Lötzone von [`femur.FCStd`](../mechanics/models/custom/v2/parts/femur/femur.FCStd) eingelötet werden.
- [ ] **Zweiten Controller (`0x42`, rechts, `A1` gebrückt) in Daisy-Chain integrieren & testen.**
- [ ] **Restliche `5×` `V280`-Wandler einzeln prüfen:**  
  * Jeden weiteren **Wandler** vor dem Einbau in die Femur-Kammern auf Adresse `0x48` (`ADDR → GND`), 12- vs. 16-Bit-Auflösung und Kanal-Isolation (`CH1–CH5`) verifizieren.
- [ ] **Alle 18 Servos (`Reely / Torcster NR-645 MG BB`) umbauen & einzeln durchmessen:**  
  * **Spezifikation & Maße:** Siehe verbindliche Leitfaden- und Längenmatrix in [`WIRING_HARNESS_SPEC.md`](WIRING_HARNESS_SPEC.md).
  * **1 Servo verifiziert (`bkhexapod`), 17 Servos ausstehend:**
    * Weiße hochflexible Silikonlitze (AWG 28/30) auf **150 mm** (Coxa) bzw. **100 mm** (Femur/Tibia) an den mittleren Schleiferabgriff des internen 5kΩ-Drehpotis anlöten.
    * Leitung parallel zum Werkskabel durch die Gehäusetülle herausführen und Deckel schließen.
  * **Zwingende QC-Messtoleranz vor Platinenanschluss:** Bei **jedem** Servo vor dem Anstecken an einen **Wandler** per Multimeter gegen `GND` bestätigen, dass über den kompletten Stellweg strikt `≤ 3,3 V` anliegen ($0{,}88\dots 2{,}25\,\text{V}$ normal, $1{,}56\,\text{V}$ neutral, niemals $> 3{,}3\,\text{V}$).
- [ ] **Kabelbäume & Platinen-Stecker nach 3D-CAD-Maßen konfektionieren ([`WIRING_HARNESS_SPEC.md`](WIRING_HARNESS_SPEC.md)):**  
  * **6× I²C-Uplinks (Wandler $\rightarrow$ Zentrale Verteilerschiene):** 4-adrig AWG 28 (`Rot, Schwarz, Gelb, Kanal-Farbe`), einheitliche Schnittlänge **300 mm** (Dupont / JST-XH 4-Pin Buchse).
  * **6× Fußsensor-Leitungen (Omron D2F-L $\rightarrow$ Wandler `A3` & `GND`):** 2-adrig AWG 28 (`Orange, Schwarz`), Schnittlänge **210 mm**.
  * **6× Wandler-Eingangsstecker (Analog A0–A3):** 4-Pin-Buchse (`A0 Weiß Coxa, A1 Weiß Femur, A2 Weiß Tibia, A3 Orange Fuß`).
  * **PWM-Zuleitungen zu den PCA9685:** 300 mm Werkskabel für Coxa/Femur/Tibia-nah nutzen; Tibia-fern (`RL, FR, MR`) mit 100 mm Servo-Verlängerung versehen.

### AP 4: Bench- & Software-Integration (`scripts/bench/` & `lasius-core`)
- [x] **[`pot_calibration_wizard.py`](../../scripts/bench/pot_calibration_wizard.py) automatisieren:**  
  * Option `--adc` ergänzt: Vollautomatische oder interaktive Einlesung über Multiplexer (`CH0–CH7`) + Wandler (`A0–A3`) mit Sicherheits-Hardlimit ($\le 3{,}3\,\text{V}$), konfigurierbarer Mittelwertbildung (`--samples`), `--auto`-Modus und vollwertigem Mock-Modus (`--mock`) für Offline-Tests.
- [ ] **Diagnose-Skripte sauber auf `bkhexapod` ausrollen & pflegen:**  
  * [`test_electronics.py`](../../scripts/bench/test_electronics.py) und aktualisierten Kalibrier-Wizard nach `~/lasius/scripts/` auf den Pi synchronisieren.
  * Sub-Kanal-Scan in `test_electronics.py` verbessern (bereits auf dem Hauptbus erkannte Adressen wie `0x40` / `0x42` beim Sub-Scan herausfiltern) und Diagnose-Ausgabe ggf. auf 12-/16-Bit-Erkennung anpassen.
- [ ] **Closed-Loop-Telemetrie in `lasius-core` implementieren:**  
  * Treiberklasse für **Multiplexer + Wandler** in den HAL integrieren und Gelenkwinkel-Kalibrierungen (`slope`, `intercept`) pro Servo laden.

### AP 5: Geplante Sensor- & Leistungserweiterungen
- [ ] **9-DOF IMU (`BNO085`, `0x4A`)** am Hauptbus testen.
- [ ] **Strom-/Spannungsüberwachung (`INA228` / `INA260`)** an `CH6` (**Braun / Gelb**) einbinden.
- [ ] **ToF-Abstandssensoren (`VL53L4CD` / `VL53L5CX`)** an `CH7` / Chassis-Unterseite integrieren.
- [ ] **Finalen Leistungsstrang (`03_power_distribution.yml`) aufbauen & belasten:**  
  * `XT60BE-M` → `25 A` Sicherung → `20 A` Hauptschalter → `2× 6,0 V UBEC` + `5,1 V` Pi-Buck aufbauen und Übergang von Labornetzteil auf LiPo/UBEC verifizieren.
