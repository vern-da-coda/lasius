# Lasius Hexapod: Das Große Audio-Briefing & Domänen-Manuskript

---


*Hinweis für Sprach-Engines (Text-to-Speech wie ElevenLabs, OpenAI Audio, Piper, Coqui) oder zum Vorlesen: Dieses Dokument ist im flüssigen Sprech- und Podcast-Stil verfasst. Abkürzungen und mathematische Formeln sind phonetisch ausgeschrieben, sodass der Text ohne Stocken vorgelesen werden kann.*

---

## Willkommen zum Lasius Deep Dive

Herzlich willkommen zu diesem umfassenden Audio-Briefing über das Robotik-Projekt Lasius. In dieser Episode tauchen wir tief ein in die Architektur, die Mechanik, die Elektronik, die Kinematik und die künstliche Intelligenz eines hochentwickelten, sechsbeinigen Laufroboters.

Egal, ob du diesen Text über eine moderne Sprach-KI hörst oder dir die Aufzeichnung beim Pendeln oder Trainieren anhörst: Am Ende dieses Briefings wirst du verstehen, wie jede einzelne Schraube, jede mathematische Formel und jedes neuronale Netzwerk im Projekt Lasius nahtlos ineinandergreifen.

Legen wir direkt los mit Kapitel eins: Das Leitbild und die Vision von Lasius.

---

## Kapitel 1: Leitbild, Vision & Systemüberblick

Lasius ist ein biomimetischer Laufroboter mit achtzehn Freiheitsgraden, dessen Name und Anatomie von der Gattung der Wegameisen inspiriert ist, wissenschaftlich Lasius niger. Ameisen gehören zu den effizientesten Fortbewegungskünstlern der Natur: Sie balancieren mühelos über unwegsames Gelände, können auf der Stelle wenden und besitzen durch ihre sechs Beine zu jedem Zeitpunkt eine extrem hohe statische und dynamische Stabilität.

Das übergeordnete Ziel des Projekts Lasius ist es, diese biologische Eleganz in ein modernes, industrietaugliches Robotik-System zu übertragen. Doch Lasius ist nicht einfach nur ein physischer Roboter: Das Repository vereint sieben eng miteinander verzahnte Domänen:

Erstens: Eine parametrische Mechanik, die nach dem Prinzip Hardware-as-Code modular in FreeCAD entwickelt wird.
Zweitens: Eine isolierte Elektronik- und Energieverteilung, die empfindliche 3,3-Volt-Logik sauber von induktiven Servo-Lasten trennt.
Drittens: Ein hochoptimierter Motion-Core in Python, der eine geschlossene dreidimensionale inverse Kinematik und einen harmonischen 50-Hertz-Ganggenerator berechnet.
Viertens: Ein interaktiver dreidimensionaler digitaler Zwilling im Webbrowser, aufgebaut mit Vue 3, TypeScript und Three.js.
Fünftens: Ein Linux-nativer Teleoperations-Client namens lasius-pilot, der moderne Gamepads wie den PlayStation 5 DualSense Controller mit extrem niedriger Latenz einbindet.
Sechstens: Eine physikalische 3D-Simulation in PyBullet und MuJoCo, die das exakte CAD-Modell mit realen Trägheitstensoren abbildet.
Und siebtens: Ein modernes Reinforcement-Learning-Setup auf Basis von Gymnasium und Stable-Baselines3, in dem künstliche neuronale Netze das adaptive Laufen trainieren.

Schauen wir uns nun die physische Grundlage an: Die Mechanik in Kapitel zwei.

---

## Kapitel 2: Mechanik & Hardware-as-Code

Die mechanische Struktur von Lasius basiert auf zwei zentralen Pfeilern: Einem verwindungssteifen Carbonfaser-Sandwich-Chassis und sechs identisch aufgebauten, modularen Beinen.

Beginnen wir mit der Geometrie eines Beins. Jedes der sechs Beine besitzt drei motorisierte Gelenke, die von durchzugsstarken Metallgetriebe-Servos angetrieben werden:
Das erste Gelenk an der Hüfte ist die Coxa. Sie rotiert um die vertikale Achse und bestimmt die Gier-Richtung des Beins. Die wirksame Hebellänge der Coxa beträgt exakt 56,5 Millimeter.
Daran schließt sich das Oberschenkelgelenk an, der Femur. Es bewegt sich in der Nick-Ebene, also auf und ab, und hat eine Länge von 100 Millimetern. Um eine symmetrische Montage und Kollisionsfreiheit zu gewährleisten, besitzt der Femur einen seitlichen Versatz von 2,5 Millimetern.
Das dritte Gelenk ist die Tibia, der Unterschenkel, mit einer Länge von 130 Millimetern. Zusammen ergibt sich für jedes Bein eine maximale gestreckte Reichweite von 286,5 Millimetern.

Im kalibrierten, neutralen Stand des Roboters stehen die Fußspitzen auf einem Radius von 190 Millimetern um die Beinwurzeln. Die Bodenfreiheit des Chassis beträgt dabei exakt 161,5 Millimeter. An diesem Arbeitspunkt berühren alle sechs Fußspitzen den Boden perfekt symmetrisch.

Ein zentrales architektonisches Highlight des Projekts ist das sogenannte Drei-Ebenen-Prinzip in der CAD-Konstruktion:
Auf Ebene eins trennen wir strikt zwischen unveränderlichen Kaufteilen, im Englischen Commercial Off-The-Shelf oder COTS genannt, und selbst konstruierten Bauteilen. Schrauben, Kugellager und Servos liegen unantastbar im Ordner cots.
Auf Ebene zwei organisieren wir konstruktive Generationen. Generation eins steht für die aktuelle Basis mit gefrästen Carbonplatten und PETG-Abstandshaltern. Künftige Generationen, wie Generation zwei mit monolithischem 3D-Druck, werden in getrennten Ordnern gekapselt.
Auf Ebene drei unterscheiden wir zwischen Baugruppen und Einzelteilen. Komplette Baugruppen wie das Chassis liegen direkt im Generationsordner, während Einzelteile im Unterordner parts gekapselt sind.
Ganz wichtig dabei: Alle Dateinamen im CAD sind kanonisch und tragen keine Versionsnummern im Namen. So heißen die Teile schlicht femur punkt FCStd oder tibia punkt FCStd. Dadurch bleiben die internen Verknüpfungen in FreeCAD über Git-Commits hinweg absolut stabil.

Kommen wir in Kapitel drei zu den Nervenbahnen und Muskeln des Roboters: Der Elektronik und Sensorik.

---

## Kapitel 3: Elektronik, Stromversorgung & Sensorik

In der mobilen Robotik entscheidet die Spannungsversorgung über Leben und Tod des Systems. Servomotoren ziehen bei abrupten Richtungswechseln oder unter Spitzenlast gewaltige Ströme von bis zu zwanzig Ampere und erzeugen induktive Spannungsspitzen im Bordnetz. Würde man den Raspberry Pi an dieselbe Stromschiene hängen, käme es unweigerlich zu Brownouts, also plötzlichen Systemabstürzen durch Unterspannung.

Deshalb setzt Lasius auf eine strikt getrennte Zweischienen-Architektur:
Als zentrale Energiequelle dient ein Zwei-S-Lithium-Polymer-Akku mit einer Nennspannung von 7,4 Volt und einer Ladeschlussspannung von 8,4 Volt.
Von diesem Akku zweigen zwei separate Wandler ab:
Ein massiver, mit zwanzig Ampere belastbarer UBEC-Abwärtswandler erzeugt eine hochstabile 6,0-Volt-Motorschiene. Diese Schiene speist ausschließlich die Leistungsteile der achtzehn Servos.
Ein separater Gleichspannungswandler erzeugt fünf Volt bei drei Ampere für die Versorgung des Raspberry Pi 4 B. Der Einplatinencomputer selbst versorgt wiederum über seine interne 3,3-Volt-Schiene die Logikbausteine und Sensoren. Beide Kreise teilen sich eine gemeinsame Masseleitung, haben aber galvanisch entkoppelte Versorgungsspannungen.

Die Signalleitungen der Servos werden von zwei PCA9685 PWM-Treibern über den I-Zwei-C-Bus des Raspberry Pi gesteuert. Jeder Treiber besitzt sechzehn Kanäle mit einer präzisen Zwölf-Bit-Auflösung:
Treiber null auf I-Zwei-C-Adresse hexadezimal 40 steuert die neun Servos der drei linken Beine.
Treiber eins auf Adresse hexadezimal 41 steuert die neun Servos der rechten Beine.
Zusätzlich hören beide Treiber auf die globale Broadcast-Adresse hexadezimal 70, über die mit einem einzigen I-Zwei-C-Befehl ein synchroner Not-Aus ausgelöst werden kann.

Ein ganz besonderes Feature von Lasius ist die sogenannte Closed-Loop-Testbench: Standard-Servos besitzen intern zwar ein Potentiometer, geben diesen Ist-Winkel aber normalerweise nicht nach außen weiter. Bei Lasius werden die internen Potentiometer aller achtzehn Servos angezapft und über Tiefpassfilter an sechs ADS1115 Sechzehn-Bit-Analog-Digital-Wandler geführt. Da alle sechs Wandler dieselbe Standard-Adresse besitzen, werden sie über einen TCA9548A Acht-Kanal-I-Zwei-C-Multiplexer auf Adresse hexadezimal 71 kaskadiert. Dadurch kann der Raspberry Pi zu jedem Zeitpunkt den exakten, realen Winkel jedes einzelnen Gelenks mit hoher Präzision zurücklesen.

Für die Lageerkennung im Raum sorgt eine BNO085 Neun-Achs-Trägheitsmesseinheit, kurz IMU, die Orientierung, Drehraten und Beschleunigungen driftfrei erfasst.

Wie aus diesen Winkeln flüssige Bewegungen entstehen, hören wir jetzt in Kapitel vier.

---

## Kapitel 4: Motion Core & Die Mathematik des Gehens

Das Herzstück der Software ist das Paket lasius-core. Hier laufen zwei fundamentale mathematische Prozesse ab: Die inverse Kinematik und der Ganggenerator.

Beginnen wir mit der inversen Kinematik. Die Aufgabe der inversen Kinematik besteht darin, eine gewünschte räumliche Position der Fußspitze – ausgedrückt in den kartesischen Koordinaten x, y und z – in die drei Gelenkwinkel Alpha für die Coxa, Beta für den Femur und Gamma für die Tibia umzurechnen.
Viele komplexe Roboter nutzen dafür numerische Näherungsverfahren, die iterativ rechnen und viel Rechenzeit fressen. Bei Lasius dagegen ist die Bein-Geometrie so elegant konstruiert, dass sich die inverse Kinematik in geschlossener Form analytisch mit einfachen trigonometrischen Funktionen lösen lässt:
Der Coxa-Winkel Alpha ergibt sich direkt aus dem Arkustangens von y geteilt durch x.
Die Gelenke von Femur und Tibia bilden zusammen mit dem Zielpunkt ein Dreieck in der vertikalen Beinebene. Über den Kosinussatz und die bekannten Beinlängen lassen sich die Winkel Beta und Gamma in Mikrosekunden exakt berechnen. Das bedeutet: Lasius kann selbst auf einem kleinen Mikrocontroller zehntausende Kinematik-Lösungen pro Sekunde fehlerfrei ermitteln.

Über dieser inversen Kinematik sitzt der Ganggenerator, genannt OmniGait. Er arbeitet mit einer festen Frequenz von 50 Hertz, also fünfzig Rechenschritten pro Sekunde. Um ruckartige Belastungen auf die Servogetriebe zu verhindern, erzeugt OmniGait die Fußkurven nicht als harte Polygone, sondern über harmonische Kosinus-Trajektorien. Dadurch sind Geschwindigkeit und Beschleunigung an den Umkehrpunkten der Bewegung mathematisch stetig.

OmniGait unterstützt drei klassische hexapode Gangarten:
Erstens: Den Tripod-Gait oder Dreibeingang. Hier schwingen immer drei Beine gleichzeitig nach vorne – das linke vordere, das rechte mittlere und das linke hintere Bein –, während die anderen drei Beine fest auf dem Boden stehen und das Chassis vorwärts schieben. Bei der halben Schrittphase wechselt die Gruppe. Das ist der schnellste und dynamischste Gang für flaches Terrain.
Zweitens: Den Ripple-Gait oder Wellengang. Hier schwingen immer zwei Beine gleichzeitig, während vier Beine Bodenkontakt halten. Das erhöht die Stabilität auf unebenem Untergrund spürbar.
Drittens: Den Wave-Gait. Hier bewegt sich immer nur ein einziges Bein zur Zeit, während fünf Beine sicheren Stand garantieren. Das ist der Gang für steile Hänge oder extremes Geröll.

Das Geniale an OmniGait: Der Gang ist vollkommen omnidirektional. Der Roboter kann sich gleichzeitig vorwärts bewegen, seitwärts strafen und sich um die eigene Hochachse drehen – alles stufenlos kombiniert.

Wie dieser Roboter visualisiert und gesteuert wird, besprechen wir in Kapitel fünf.

---

## Kapitel 5: 3D Digital Twin, Dashboard & Gamepad-Steuerung

Um einen Roboter sicher zu entwickeln, benötigt man ein klares Fenster in seinen inneren Zustand. Dieses Fenster bietet das Paket lasius-dashboard.

Das Dashboard ist eine moderne Web-Applikation, entwickelt mit Vue 3, TypeScript und Three.js für hardwarebeschleunigtes WebGL-Rendering. Es bietet eine interaktive 3D-Ansicht des Roboters, ein künstliches Horizont-Display basierend auf den IMU-Daten, Leistungsanzeigen für Strom und Spannung sowie virtuelle Bedienelemente.

Das architektonische Highlight des Dashboards ist sein sogenannter Dual-Engine-Aufbau:
Im Browser läuft ein kompletter, autarker Klon der Kinematik- und Gang-Engine in reinem TypeScript. Ruft man das Dashboard ohne echten Roboter auf – zum Beispiel unter dashboard punkt lasius punkt kaemmereit punkt de –, läuft der digitale Zwilling vollkommen eigenständig im Browser. Man kann ihn per Tastatur, virtuellem Steuerkreuz oder Gamepad direkt über den Bildschirm laufen lassen.
Sobald sich das Dashboard jedoch über einen 50-Hertz-WebSocket mit einem echten Lasius-Roboter oder der PyBullet-Physiksimulation verbindet, schaltet die clientseitige Simulation stumm und das Three.js-Modell visualisiert die echten Sensordaten des Roboters in Echtzeit.

Für die manuelle Steuerung steht das Werkzeug lasius-pilot bereit. Es wurde nach der Unix-Philosophie entwickelt: Maximal leichtgewichtig und ohne schwere Abhängigkeiten. Es liest die Rohdaten des Gamepads direkt aus der Linux-Kernel-Schnittstelle unter dev input js0.
Über YAML-Dateien lassen sich beliebige Controller konfigurieren. Standardmäßig ist ein optimiertes Profil für den PlayStation 5 DualSense Controller hinterlegt:
Mit dem linken Analogstick steuert man die Translation – also stufenlos vorwärts, rückwärts und seitlich.
Mit dem rechten Analogstick steuert man die Drehung auf der Stelle.
Über die Aktionstasten Kreuz, Viereck und Dreieck wechselt man blitzschnell zwischen Tripod-, Ripple- und Wave-Gang.
Und die Kreistaste oder die PlayStation-Taste dient als sofortiger Not-Aus, der alle Servos augenblicklich stromlos schaltet.
Besonders praktisch: Schließt man den PS5-Controller per USB-C an den Laptop an, bleibt das Bluetooth-Pairing mit der Konsole im Wohnzimmer vollständig erhalten.

Damit sind wir perfekt vorbereitet für Kapitel sechs: Die Physik-Simulation und das Training künstlicher Intelligenz.

---

## Kapitel 6: Physik-Simulation & Reinforcement Learning

Kommen wir zu der wohl faszinierendsten Domäne von Lasius: Dem virtuellen Prüfstand und dem Reinforcement Learning.

Bevor ein Steuerungsalgorithmus auf teurer Hardware getestet wird, muss er sich in einer realitätsnahen Physiksimulation beweisen. Bei Lasius wird das FreeCAD-Konstruktionsmodell über ein Python-Skript vollautomatisch in ein standardisiertes URDF-Modell exportiert. Dabei werden aus den echten 3D-Volumenkörpern nicht nur die visuellen und Kollisions-Netze generiert, sondern auch die exakten Massen, Schwerpunkte und Trägheitstensoren jedes einzelnen Glieds physikalisch exakt berechnet.

Dieses Modell wird in die PyBullet-Physik-Engine geladen. Bei einer Physik-Frequenz von 250 Hertz werden Bodenreibung, Trägheitskräfte, Hebelwirkungen und Gelenkdämpfungen exakt simuliert. Über das Orchestrierungs-Skript sim pilot punkt sh kann man die PyBullet-Simulation und das Gamepad-Werkzeug mit einem einzigen Befehl synchron starten – inklusive automatischem Prozess-Aufräumen beim Schließen.

Auf dieser soliden Basis setzt das neue Reinforcement-Learning-Setup auf. Herzstück ist die Klasse LasiusGymEnv, ein standardisiertes Gymnasium-Environment.
Der Beobachtungsraum des Agenten umfasst 66 kontinuierliche Werte:
Drei Werte für den projizierten Schwerkraftvektor im Chassis-Koordinatensystem – das liefert die Neigung des Roboters völlig frei von kardanischen Blockaden, dem gefürchteten Gimbal Lock.
Sechs Werte für die linearen und rotatorischen Geschwindigkeiten im Raum.
Achtzehn Werte für die aktuellen Abweichungen der Gelenkwinkel von der Standposition.
Achtzehn Werte für die aktuellen Gelenkgeschwindigkeiten.
Drei Werte für die vorgegebenen Soll-Geschwindigkeiten.
Und achtzehn Werte für die unmittelbar zuvor ausgeführte Aktion, um abrupte Zuckungen zu dämpfen.

Beim Aktionsraum setzt Lasius auf ein hochmodernes Prinzip: Das Residual Reinforcement Learning.
Ein End-to-End-Lernen, bei dem ein neuronales Netz alle achtzehn Gelenke von Null auf steuert, scheitert in der Praxis oft: Der Roboter zappelt am Anfang wild und stürzt hunderttausende Male ab, bevor er überhaupt koordinierte Beinbewegungen entdeckt.
Beim Residual RL dagegen liefert die bewährte analytische Kinematik von OmniGait zu jedem Zeitschritt eine absolut stabile Basistrajektorie. Das neuronale Netz lernt lediglich additive Korrekturen im Bereich von plus/minus elf Komma fünf Grad.
Das Ergebnis: Der Roboter läuft ab Zeitschritt eins stabil. Das neuronale Netz konzentriert sich voll und ganz darauf, Bodenunebenheiten auszugleichen, Neigungen an Hängen zu minimieren und Energie zu sparen.

Mit dem Algorithmus Proximal Policy Optimization, kurz PPO, aus der Bibliothek Stable-Baselines3 wurde dieses Setup trainiert. Dank vier paralleler Umgebungen erreichte das Training auf einer handelsüblichen Laptop-CPU einen Durchsatz von über 420 Bildern pro Sekunde. Bereits nach knapp acht Minuten und zweihunderttausend Schritten konvergierte das Netzwerk: In drei unabhängigen Benchmark-Läufen über jeweils tausend Schritte lief der Roboter die vollen zwanzig Sekunden fehlerfrei durch, hielt seine Soll-Geschwindigkeit exakt ein und zeigte eine beispielhafte Haltungsstabilität.

---

## Kapitel 7: Fazit & Was als Nächstes kommt

Fassen wir zusammen: Das Projekt Lasius demonstriert eindrucksvoll, wie moderne Open-Source-Technologien ein mechatronisches Gesamtkunstwerk formen.
Von den parametrischen CAD-Modellen in FreeCAD über die deterministische 50-Hertz-Kinematik, die saubere I-Zwei-C-Bus-Elektronik und den reaktiven digitalen Three.js-Zwilling bis hin zum GPU-freien Reinforcement Learning in PyBullet: Jedes Modul folgt klaren architektonischen Leitlinien, ist modular getestet und über Unittests abgesichert.

Der nächste spannende Schritt auf der Roadmap führt zurück zur realen Hardware:
Auf der Elektronik-Testbench wird nun die Verkabelung des TCA9548A Multiplexers an den Raspberry Pi abgeschlossen, gefolgt von der Inbetriebnahme der Sechzehn-Bit-ADCs. Sobald dieser Closed-Loop-Rückkanal steht, kann das in der Simulation trainierte neuronale Netz im echten Roboter aufspielen – und Lasius wird lernen, sich in der realen Welt genauso souverän zu bewegen wie im digitalen Raum.

Vielen Dank fürs Zuhören bei diesem umfassenden Architektur-Briefing des Lasius Hexapod Projekts!
