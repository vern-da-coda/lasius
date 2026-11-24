# Hexapod:Lasius – Kabelbaum- & Konfektionierungs-Spezifikation (Wiring Harness Spec)

---

[Index](../../README.md) | [Software](../../software/README.md) | [Hardware](../../hardware/README.md) | [Docs](../../docs/README.md) |<br>
[Wiring & Schematics](wiring/README.md) | [Closed Loop Plan](../../docs/hardware/closed_loop_plan.md) | [Wiring Plan](../../docs/hardware/wiring_plan.md) | [Electronics Backlog](TODO.md)

---

Dieses Dokument definiert die exakten **Leitungslängen, Kabelbaum-Strukturen, Steckerbelegungen und Werkstatt-Anleitungen** für den Bau und die Serien-Konfektionierung der 18-DOF-Elektronik von **Hexapod:Lasius**. Alle Längenmaße basieren auf den realen 3D-B-Rep-Modellen der Generation v2 (`body_assembly.FCStd`, `leg_assembly.FCStd`, `chassis_core_assembly.FCStd`).

---

## 1. Master-Übersicht: Leitungslängen & Schnittmaße

### 1.1 Bein-Innenverkabelung (Single-Leg Sub-Harness, 6 Beine)

Jedes Bein verfügt über eine autarke Sensorik-Kammer im Oberschenkel ([`parts/femur/femur.FCStd`](../mechanics/models/custom/v2/parts/femur/femur.FCStd)), in der ein 4-Kanal-AD-Wandler (**ADS1115 `V280`**) sitzt.

| Signal / Leitung | Adern & Querschnitt | Farbe | 3D-Pfad im CAD | Bewegungsschleife (Slack) | Konfektionier-Länge (Schnittmaß) | Anschluss / Pin |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **Coxa-Poti** (Hüft-Yaw) | 1× AWG 28 Silikon | **Weiß** (`WH`) | 88 mm | +30 mm (190° Femur-Nick) + 20 mm Strip | **150 mm** | Servo-Schleifer $\rightarrow$ Wandler `A0` |
| **Femur-Poti** (Oberschenkel) | 1× AWG 28 Silikon | **Weiß** (`WH`) | 50 mm | +20 mm (Bogenführung) + 20 mm Strip | **100 mm** | Servo-Schleifer $\rightarrow$ Wandler `A1` |
| **Tibia-Poti** (Knie) | 1× AWG 28 Silikon | **Weiß** (`WH`) | 50 mm | +20 mm (Knie-Bogen) + 20 mm Strip | **100 mm** | Servo-Schleifer $\rightarrow$ Wandler `A2` |
| **Fußsensor** (Omron D2F-L) | 2× AWG 28 Silikon | **Orange** (`NO`)<br>**Schwarz** (`COM`) | 134 mm | +51 mm (103° Knie-Hub) + 25 mm Strip | **210 mm** | Mikroschalter $\rightarrow$ Wandler `A3` & `GND` |

> [!TIP]
> **Serienfertigung der 18 Servos:**  
> Wenn alle verbleibenden 17 Servos einheitlich mit einer **150 mm** langen weißen Poti-Litze ausgestattet werden, kann die Leitung bei Femur und Tibia entweder direkt beim Crimpen auf 100 mm gekürzt werden, oder die 50 mm Überschuss verbleiben als Service- und Montageschleife im geräumigen Femur-Hohlraum.

---

### 1.2 Leg-to-Chassis I²C-Uplink (6 Beine $\rightarrow$ Zentrale Verteilerschiene)

Verbindung vom **Wandler (`ADS1115 V280`)** in der Femur-Kammer durch die Coxa-Bögen und Monocoque-Kabelports zur zentralen **3,3 V / GND-Schiene** und dem **Multiplexer (`PW548A / PCA9548A`)** auf dem Zwischenboden ($X = 0{,}0, Y = 0{,}0, Z = 28{,}0\,\text{mm}$).

| Bein / Position | Kanal-Nr. | I²C-SDA-Farbe | 3D-Pfad im CAD | Hüft-Schleife & Toleranz | Standardisierte Schnittlänge |
| :--- | :---: | :--- | :---: | :---: | :---: |
| **Left Front (LF)** | `CH0` | **Blau** (`BU`) | 260 mm | +25 mm Hüft-Yaw + 15 mm Reserve | **300 mm** |
| **Left Middle (LM)** | `CH1` | **Grün** (`GN`) | 251 mm | +25 mm Hüft-Yaw + 15 mm Reserve | **300 mm** |
| **Left Rear (LR)** | `CH2` | **Violett** (`VT`) | 259 mm | +25 mm Hüft-Yaw + 15 mm Reserve | **300 mm** |
| **Right Front (FR)** | `CH3` | **Orange** (`OG`) | 260 mm | +25 mm Hüft-Yaw + 15 mm Reserve | **300 mm** |
| **Right Middle (RM)** | `CH4` | **Weiß** (`WH`) | 251 mm | +25 mm Hüft-Yaw + 15 mm Reserve | **300 mm** |
| **Right Rear (RR)** | `CH5` | **Grau** (`GY`) | 259 mm | +25 mm Hüft-Yaw + 15 mm Reserve | **300 mm** |

*Adern-Zusammensetzung je Uplink (4-polig AWG 28):*
1. **Rot** (`RD`): `3,3 V` Logik-Versorgung
2. **Schwarz** (`BK`): `GND` Masse
3. **Gelb** (`YE`): `SCx` I²C-Takt
4. **Kanal-Farbe**: `SDx` I²C-Daten

> [!NOTE]
> Durch die zentrische Anordnung des Multiplexers bei $(0, 0)$ sind alle 6 Strecken praktisch symmetrisch ($250\dots 260\,\text{mm}$). Alle 6 Kabelstränge können exakt identisch auf **300 mm** abgelängt werden.

---

### 1.3 Servo-PWM-Zuleitungen (18 Servos $\rightarrow$ PCA9685 PWM-Controller)

*Werkseitige Kabellänge der Torcster / Reely NR-645 Servos: ca. **300 mm**.*

| Servo-Position | Ziel-Controller | Effektiver 3D-Pfad | Status des 300 mm Werkskabels |
| :--- | :--- | :---: | :--- |
| **Coxa-Servos (6×)** | PCA9685 Links (`0x40`) / Rechts (`0x42`) | 150 – 215 mm | **Ausreichend** (ca. 85–150 mm Reserve) |
| **Femur-Servos (6×)** | PCA9685 Links (`0x40`) / Rechts (`0x42`) | 190 – 255 mm | **Ausreichend** (ca. 45–110 mm Reserve) |
| **Tibia-Servos nah** (`FL`, `ML`, `RR`) | Zugeordneter PCA9685 | 290 – 300 mm | **Passgenau** (reicht direkt) |
| **Tibia-Servos fern** (`RL`, `FR`, `MR`) | Zugeordneter PCA9685 | 345 – 355 mm | **Verlängerung erforderlich:** Kurze 100 mm Servo-Verlängerung oder beim Neucrimpen auf 370 mm ablängen. |

---

## 2. Platinen-Stecker & Pinbelegungen

### 2.1 Wandler-Platine (`ADS1115 V280`) in der Femur-Kammer (6×)

Die Platine besitzt eine 10-polige Stiftleiste im 2,54 mm Raster.  
**Hardware-Befund (`V280`):** `SCL` liegt vor `SDA`!

```text
Pin-Header Belegung:
  [ 1: VDD ]  ── 3,3 V Logik (Rot)
  [ 2: GND ]  ── Masse (Schwarz)
  [ 3: SCL ]  ── I²C Takt SCx (Gelb)
  [ 4: SDA ]  ── I²C Daten SDx (Kanal-Farbe)
  [ 5: ADDR]  ── Feste Lötbrücke auf Pin 2 (GND) -> Adresse 0x48
  [ 6: ALRT]  ── (unbeschaltet)
  [ 7: A0  ]  ── Coxa-Poti (Weiß)      [+ 100 nF nach GND auf Platinen-Unterseite]
  [ 8: A1  ]  ── Femur-Poti (Weiß)     [+ 100 nF nach GND auf Platinen-Unterseite]
  [ 9: A2  ]  ── Tibia-Poti (Weiß)     [+ 100 nF nach GND auf Platinen-Unterseite]
  [ 10: A3 ]  ── Fuß-Schalter (Orange) [+ 100 nF nach GND & 10 kΩ Pull-up nach VDD]
```

#### Passiv-Bauteile (direkt an der Stiftleiste auf der Platinenunterseite verlötet):
1. **4× 100 nF MLCC Keramikkondensatoren (Code 104):**
   - Zwischen `A0` und `GND`
   - Zwischen `A1` und `GND`
   - Zwischen `A2` und `GND`
   - Zwischen `A3` und `GND`
2. **1× 10 kΩ SMD- oder Bedrahteter Widerstand:**
   - Zwischen `A3` und `VDD` (`3,3 V`) als definierter Pull-up.
3. **1× Drahtbrücke:**
   - Zwischen `ADDR` und `GND`.

#### Steckverbinder am Wandler:
- **Stecker 1 (I²C-Uplink, 4-polig Dupont / JST Buchse):**  
  `[1: Rot (3,3 V), 2: Schwarz (GND), 3: Gelb (SCx), 4: Kanal-Farbe (SDx)]` $\rightarrow$ Pins 1–4.
- **Stecker 2 (Analog-Feedback, 4-polig Dupont Buchse):**  
  `[1: Weiß (A0 Coxa), 2: Weiß (A1 Femur), 3: Weiß (A2 Tibia), 4: Orange (A3 Fuß)]` $\rightarrow$ Pins 7–10.
- **Masse Fußschalter:** Die schwarze `COM`-Ader des Fußschalters wird auf die Masseleitung des Wandlers gelötet oder gecrimpt.

---

### 2.2 Zentrale 3,3 V / GND-Verteilerschiene & Multiplexer (`PW548A`)

Da der violette `PW548A`-Multiplexer auf seinen Kanälen `CH0–CH7` nur `SDx` und `SCx` bereitstellt, fasst die Verteilerplatine die Versorgungs- und Signalleitungen pro Bein zusammen:

```text
Bein-Steckplätze (6x 4-polig, polarisiert oder farblich markiert):
  Pin 1: 3,3 V  (Rot, von zentraler 3,3 V-Schiene)
  Pin 2: GND    (Schwarz, von zentraler Logik-Masse)
  Pin 3: SCx    (Gelb, vom entsprechenden Multiplexer-Kanal SC0–SC5)
  Pin 4: SDx    (Kanal-Farbe, vom entsprechenden Multiplexer-Kanal SD0–SD5)
```

- **Mux-Adresse Jumper `A0`:** Fest auf `3,3 V` gebrückt $\rightarrow$ Multiplexer antwortet auf **`0x71`** (kein Boot-Konflikt mit PCA9685 `0x70 ALLCALL`).
- **Massebezug:** Die Logik-Masse dieser Schiene wird über **genau eine** niederohmige Referenzleitung an den zentralen `Star-GND` des 6 V-Leistungskreises angebunden.

---

### 2.3 PWM-Treiber (`PCA9685`, 2×)

- **Controller Links (`0x40`):** 9 Servo-Kanäle für die linken Beine (`FL: CH0–2`, `LM: CH4–6`, `LR: CH8–10`). Front-Erweiterung `CH3` frei für linke Mandibel.
- **Controller Rechts (`0x42`, Jumper A1 gebrückt):** 9 Servo-Kanäle für die rechten Beine (`RF: CH0–2`, `RM: CH4–6`, `RR: CH8–10`). Front-Erweiterung `CH3` frei für rechte Mandibel.
- Standard 3-polige Servo-Stecker: `[Braun/Schwarz = GND, Rot = V+ (6V), Gelb/Orange = PWM Signal]`.

---

## 3. Werkstatt-Anleitung: Servo-Umbau (Poti-Leitung Weiß)

### Benötigtes Werkzeug & Material
- 17× Torcster / Reely NR-645 MG BB Servos
- Feindraht-Lötkolben mit feiner Bleistiftspitze (ca. 300–320 °C) und feines Elektroniklot
- Hochflexible Silikonlitze **AWG 28 oder AWG 30 in Weiß**
- Feinmechaniker-Kreuzschlitz-Schraubendreher (Größe **PH0** oder **PH00**)
- Feine Pinzette, Abisolierzange, Schere
- Schrumpfschlauch ($\varnothing 1{,}0\,\text{mm}$) oder Kapton-Tape
- Digitalmultimeter mit feinen Prüfspitzen

---

### Durchführung Schritt für Schritt

#### Schritt 1: Gehäuse vorsichtig öffnen
1. Das Servo mit dem Abtrieb nach unten auf die Arbeitsmatte legen.
2. Die 4 langen Gehäuseschrauben an der Unterseite herausdrehen.
3. Den unteren Plastik-Gehäusedeckel behutsam senkrecht nach oben abziehen.
4. *Wichtig:* Den oberen Getriebedeckel nicht anheben, damit die gefetteten Metallzahnräder nicht herausfallen.

#### Schritt 2: Potentiometer-Schleifer lokalisieren
1. Die kleine Servoplatine leicht anheben oder zur Seite neigen, um freien Blick auf die 3 Anschlüsse des Drehpotentiometers zu erhalten.
2. Das Potentiometer besitzt 3 Anschlusspins:
   - Die beiden **äußeren Pins** liegen an Masse und der internen Referenzspannung.
   - Der **mittlere Pin** ist der bewegliche Schleiferabgriff (Wiper), der das Joint-Winkelsignal liefert.

#### Schritt 3: Weiße Ader anlöten
1. Ein Stück weiße Silikonlitze (**150 mm**) an einem Ende ca. 1,5–2,0 mm abisolieren und mit minimal Lot vorverzinnen.
2. Die Litze zügig und präzise an den **mittleren Anschluss** des Potentiometers anlöten (Lötzeit $< 2\,\text{s}$, um den Kunststoffkörper des Potis nicht zu überhitzen).
3. Sicherstellen, dass keine Zinnbrücke zu den Nachbarpins oder zum Servogehäuse besteht.
4. Lötstelle mit einem winzigen Tropfen Heißkleber oder Kapton-Band gegen Erschütterung und Berührung sichern.

#### Schritt 4: Leitungsführung & Zusammenbau
1. Die weiße Litze parallel zum bestehenden 3-adrigen Servokabel durch die seitliche Gummitülle bzw. Gehäuse-Aussparung nach außen führen.
2. Die Elektronikplatine wieder sauber in die Führungsnuten des Gehäuses einsetzen.
3. Den unteren Gehäusedeckel aufsetzen; dabei strikt darauf achten, dass keine Leitungen im Dichtungsrand eingeklemmt werden.
4. Die 4 Gehäuseschrauben über Kreuz handfest anziehen.

---

### Schritt 5: Zwingende Qualitäts- & Überspannungs-Prüfung (QC Gate)

> [!CAUTION]
> **Elektrische Zerstörungsgefahr bei Fehlverkabelung:**  
> Wird versehentlich einer der äußeren Pins kontaktiert oder liegt ein interner Kurzschluss vor, kann die Spannung $3{,}3\,\text{V}$ überschreiten. Bei Anschluss an den ADS1115 zerstört eine Spannung $> 3{,}6\,\text{V}$ den ADC-Kanal und gefährdet den Raspberry Pi!

Jedes der 17 modifizierten Servos muss vor dem Weiterbau zwingend dieses Messprotokoll durchlaufen:

```text
Messaufbau:
  [ Labornetzteil / 6V Quelle ] ───> Servo Rot (+) & Braun/Schwarz (-)
  [ Digitalmultimeter (DC V)  ] ───> COM an Braun/Schwarz (-)
                                ───> V-Prüfspitze an neue weiße Leitung
```

#### Prüf-Kriterien:
1. **Ruhespannung bei Mittelstellung (Neutral ~1500 µs):**
   * Sollwert: **$1{,}55\,\text{V} \dots 1{,}57\,\text{V}$**
2. **Spannungshub über den manuellen oder servogesteuerten Stellweg ($\pm 60^\circ$ bis $\pm 90^\circ$):**
   * Bei Drehung im Uhrzeigersinn: Spannung steigt monoton bis max. ca. **$2{,}10\dots 2{,}25\,\text{V}$**.
   * Bei Drehung gegen den Uhrzeigersinn: Spannung sinkt monoton bis min. ca. **$0{,}88\dots 1{,}00\,\text{V}$**.
3. **Hard-Limit Sicherheitskriterium:**
   * Zu **keinem Zeitpunkt** des gesamten Drehwinkels darf die gemessene Spannung **$\mathbf{> 3{,}30\,\text{V}}$** betragen!
4. **Freigabe:** Erst wenn Kriterien 1–3 erfüllt sind, erhält das Servo das Freigabelabel für die Montage im Chassis.
