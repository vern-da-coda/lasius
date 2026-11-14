# Lasius Hexapod: Elektronik-Testbench & I2C-Sensorbus Leitfaden

*Systematischer Bring-Up-Leitfaden für die Inbetriebnahme des multiplexierten I2C-Sensorbusses (TCA9548A + ADS1115 ADCs) am Raspberry Pi 4.*

---

## 1. Übersicht & Architektur

Für die Closed-Loop-Gelenkwinkelrückführung und Fußsensorik nutzt der Lasius Hexapod eine zweistufige I2C-Architektur (**Controller / Multiplexer / Wandler**):
* **Aktoren (Controller):** Zwei PCA9685 Servotreiberboards (`0x40` links, `0x42` rechts) als Daisy-Chain am primären I2C-Bus 1 des Raspberry Pi 4 (`ALLCALL 0x70` in `lasius-core` deaktiviert).
* **Sensorik (Multiplexer & Wandler):** Ein zentraler **TCA9548A / PCA9548A 8-Kanal-I2C-Multiplexer** (`0x71`) trennt die 6 Bein-**Wandler** (**ADS1115 V280**, `0x48`, verifizierte linksbündige **12-Bit**-Auflösung mit `2,0 mV`-Stufen), sodass alle Wandler dieselbe Standardadresse `0x48` nutzen können. Die `3,3 V / GND`-Logikversorgung erfolgt zentral über eine **`3,3 V / GND`-Verteilerschiene** mit Einzelreferenz an `Star-GND`, da das reale `PW548A`-Breakout auf `CH0–CH7` nur `SDx / SCx` führt.

```mermaid
flowchart TD
    Pi["Raspberry Pi 4 (I2C1 / 3.3V Pin 1/17)"]
    Rail["Zentrale 3,3V / GND Verteilerschiene"]
    Ctrl1["Controller Links (PCA9685 0x40) - 9 Servos"]
    Ctrl2["Controller Rechts (PCA9685 0x42) - 9 Servos"]
    Mux["Multiplexer (PCA9548A / PW548A 0x71 via A0 -> 3.3V)"]
    
    ADC0["CH0: Wandler V280 (0x48) - Left Front Leg"]
    ADC1["CH1: Wandler V280 (0x48) - Left Middle Leg"]
    ADC2["CH2: Wandler V280 (0x48) - Left Rear Leg"]
    ADC3["CH3: Wandler V280 (0x48) - Right Front Leg"]
    ADC4["CH4: Wandler V280 (0x48) - Right Middle Leg"]
    ADC5["CH5: Wandler V280 (0x48) - Right Rear Leg"]
    CH6["CH6: INA228 Power Monitor (0x45)"]
    CH7["CH7: VL53L4CD / VL53L5CX ToF (0x29)"]

    Pi -->|SDA1 / SCL1| Ctrl1
    Ctrl1 -->|I2C Pass-Through| Ctrl2
    Ctrl2 -->|I2C Pass-Through| Mux
    Pi -->|3.3V / GND| Rail
    Rail -.->|3.3V / GND| Ctrl1
    Rail -.->|3.3V / GND| Ctrl2
    Rail -.->|3.3V / GND| Mux

    Mux -->|SC0 / SD0| ADC0
    Mux -->|SC1 / SD1| ADC1
    Mux -->|SC2 / SD2| ADC2
    Mux -->|SC3 / SD3| ADC3
    Mux -->|SC4 / SD4| ADC4
    Mux -->|SC5 / SD5| ADC5
    Mux -->|SC6 / SD6| CH6
    Mux -->|SC7 / SD7| CH7
```

---

## 2. Sicherheitsregeln & Spannungspegel

> [!CAUTION]
> **Strikt 3.3V Logikspannung:** Der Raspberry Pi 4 besitzt **keine 5V-toleranten GPIOs**.
> * Alle I2C-Komponenten (TCA9548A, ADS1115) müssen zwingend über **Pin 1 (3.3V)** des Raspberry Pi versorgt werden.
> * Niemals 5V an `VCC`, `SDA` oder `SCL` der Sensorik anlegen.

> [!IMPORTANT]
> **Vermeidung des 0x70 All-Call-Adresskonflikts:**
> Standardmäßig startet der TCA9548A auf Adresse `0x70`. In den PCA9685 PWM-Treibern ist `0x70` jedoch hardwaremäßig als *All-Call-Adresse* reserviert (Broadcast an alle Servotreiber).
> * **Lösung:** Schließe die Lötbrücke **`A0`** auf dem TCA9548A-Breakout (oder verbinde Pin `A0` mit 3.3V).
> * Dies verschiebt die Multiplexer-Adresse auf **`0x71`** und garantiert einen konfliktfreien Betrieb.

---

## 3. Verdrahtungstabelle (Testbench-Aufbau)

### 3.1 Verbindung: Raspberry Pi 4 $\leftrightarrow$ TCA9548A Multiplexer
| Raspberry Pi 4 Pin | Signal | TCA9548A Pin | Funktion |
|---|---|---|---|
| **Pin 1** | 3.3V DC | `VIN` / `VCC` | Logikversorgung |
| **Pin 6, 9 oder 14** | GND | `GND` | Gemeinsame Masse |
| **Pin 3 (GPIO 2)** | I2C1 SDA | `SDA` | I2C Datenleitung |
| **Pin 5 (GPIO 3)** | I2C1 SCL | `SCL` | I2C Taktleitung |
| *(Interne Brücke)* | 3.3V DC | `A0` | Adress-Offset $\to$ Basisadresse `0x71` |
| *(Offen / GND)* | GND | `A1`, `A2` | Unbeschaltet (Logisch 0) |

### 3.2 Verbindung: Zentrale `3.3V/GND` + Multiplexer (`CH0`) $\leftrightarrow$ Wandler (`ADS1115 V280`)
> [!NOTE]
> **Reale Platinen-Pinbelegung beachten (`PW548A` & `V280`):**
> * Am violetten **Multiplexer (`PW548A`)** liegen auf `CH0–CH7` ausschließlich `SDx / SCx` (keine eigenen `3,3 V / GND`-Pins je Kanal). `3,3 V` und `GND` kommen über die gemeinsame Verteilerschiene.
> * Am blauen **`V280`-Wandler** liegt **`SCL` vor `SDA`** (`VDD | GND | SCL | SDA | ADDR | ALRT | A0–A3`)!

| Quelle | Farbe (Master-Schema) | Wandler (`V280`) Pin | Funktion |
|---|---|---|---|
| **Pi / `3.3V`-Schiene** | **Rot** (`RD`) | `VDD` | Logik- und Referenzspannung (`Max AIN: VDD`) |
| **Pi / `GND`-Schiene** | **Schwarz** (`BK`) | `GND` | Gemeinsame Masse (`Star-GND`-Referenz) |
| **Multiplexer `SC0`** | **Gelb** (`YE`) | **`SCL`** *(Pin 3!)* | I2C Takt Sub-Kanal 0 |
| **Multiplexer `SD0`** | **Blau** (`BU`) | **`SDA`** *(Pin 4!)* | I2C Daten Sub-Kanal 0 |
| **`GND`-Schiene** | **Schwarz** (`BK`) | `ADDR` | Wählt Standardadresse `0x48` |
| *Coxa / Femur / Tibia / Fuß* | *Weiß / Grün / Violett / Orange* | `A0–A3` | Analoge Potis (`A0–A2`) + Fußschalter (`A3`) |

---

## 4. Der 6-Schritte-Inbetriebnahmeprozess

### Schritt 1: Vorbereitung & Adressprüfung
1. Lötbrücke `A0` am TCA9548A prüfen bzw. schließen (Adresse `0x71`).
2. Sicherstellen, dass der Pi heruntergefahren ist, bevor Jumperkabel gesteckt werden.
3. Verifikation im Skript:
   ```bash
   python3 scripts/bench/test_electronics.py --step 1
   ```

### Schritt 2: TCA9548A mit dem Pi verbinden
1. Stecke die 4 Leitungen: 3.3V (Pin 1), GND (Pin 6), SDA (Pin 3), SCL (Pin 5).
2. Raspberry Pi booten.
3. Verifikation im Skript:
   ```bash
   python3 scripts/bench/test_electronics.py --step 2
   ```

### Schritt 3: I2C-Erkennung des Multiplexers prüfen
1. Scan auf dem Raspberry Pi ausführen:
   ```bash
   i2cdetect -y 1
   ```
2. Erwartetes Ergebnis: In Zeile `70:` erscheint `71`.
3. Verifikation mit dem Lasius-Testtool:
   ```bash
   python3 scripts/bench/test_electronics.py --step 3
   ```

### Schritt 4: ADS1115 an Sub-Kanal 0 anbinden
1. Verdrahte VDD, GND, SD0 $\to$ SDA, SC0 $\to$ SCL.
2. Verbinde ADDR des ADS1115 mit GND (festigt `0x48`).
3. Verifikation im Skript:
   ```bash
   python3 scripts/bench/test_electronics.py --step 4
   ```

### Schritt 5: Sub-Bus-Umschaltung & ADC-Erkennung verifizieren
1. Der Multiplexer schaltet Kanal 0 aktiv und scannt den Sub-Bus:
   ```bash
   python3 scripts/bench/test_electronics.py --step 5
   ```
2. Erwartetes Ergebnis: `✔ ERFOLG: ADS1115 erkannt auf Sub-Kanal 0 (Adresse 0x48)!`.

### Schritt 6: Analoge Spannungsmessung an A0
1. Schließe ein Potentiometer oder einen Spannungsteiler an `A0` an (Schleifer an A0, äußere Pins an 3.3V und GND).
2. Einzelmessung durchführen:
   ```bash
   python3 scripts/bench/test_electronics.py --step 6
   ```
3. Live-Monitor starten:
   ```bash
   python3 scripts/bench/test_electronics.py --channel 0 --read-analog 0
   ```
   *Drehe am Potentiometer: Der Spannungswert muss stufenlos von 0.000 V bis 3.300 V wandern.*

---

## 5. Vollständiger System-Scan

Sobald mehrere Beine oder Sensoren angeschlossen sind, scannt das Tool die gesamte Bus-Hierarchie in einem Durchlauf:

```bash
# Auf dem Raspberry Pi:
python3 scripts/bench/test_electronics.py --scan

# Auf dem Entwicklungs-Laptop (Offline-Simulation):
python3 scripts/bench/test_electronics.py --scan --mock
```

---

## 6. Troubleshooting & Häufige Fehler

| Symptom | Mögliche Ursache | Abhilfe |
|---|---|---|
| `i2cdetect` zeigt leere Tabelle | I2C im Kernel deaktiviert | `sudo raspi-config` $\to$ Interface Options $\to$ I2C aktivieren, Reboot. |
| Permission denied auf `/dev/i2c-1` | Fehlende Benutzergruppe | `sudo usermod -aG i2c $USER`, neu einloggen. |
| TCA9548A erscheint auf `0x70` statt `0x71` | `A0` unbeschaltet | Brücke `A0` schließen oder Pin `A0` mit 3.3V verbinden. |
| ADS1115 auf CH0 wird nicht erkannt | `ADDR` floatet | `ADDR`-Pin fest mit Masse (`GND`) verbinden. |
| ADC liest konstant 0V oder 3.3V | Schleifer offen / falscher Pin | Prüfe Verbindung von `A0` mit Multimeter gegen GND. |
