# Lasius Project Rules & Engineering Guidelines

## 1. Arbeitsweise & Entscheidungsdisziplin
- **Strukturiert & geordnet arbeiten:** Jede Änderung am Repository folgt einer klaren, reproduzierbaren Ordnung (saubere Verzeichnishierarchie, konsistente Benennung, verifizierte Referenzen/Links und aufgeräumter Git-Status ohne verwaiste Duplikate).
- **Unklarheiten & Anti-Patterns aktiv hinterfragen:** Wenn Anforderungen mehrdeutig sind oder technische Nachteile mit sich bringen (z. B. gebrochene CAD-Referenzen durch Versionsnummern im Dateinamen), nicht blind ausführen, sondern aktiv hinterfragen, Vor- und Nachteile darlegen und eine fundierte Empfehlung geben.
- **Erst Zielstruktur zeigen, dann ausführen:** Vor größeren Umstrukturierungen oder Dateioperationen immer zuerst die geplante Zielstruktur / Outline zeigen und auf Bestätigung warten, bevor Dateien verschoben oder umbenannt werden.

## 2. CAD- & Mechanik-Architektur (`hardware/mechanics/`)
Alle Modelle unter `hardware/mechanics/models/` und Fertigungsexporte unter `hardware/mechanics/export/{step,stl,dxf}/` folgen dem 3-Ebenen-Prinzip (*Hardware-as-Code*):

1. **Ebene 1 — Veränderlichkeit (`cots/` vs. `custom/`):**
   - `cots/`: Unveränderliche Kauf- und Normteile (Commercial Off-The-Shelf: Servos wie `servo_nr645.FCStd`, Kugellager, Schrauben, Muttern, Passscheiben).
   - `custom/`: Eigenkonstruktionen, die iterativ weiterentwickelt und gefertigt werden.
2. **Ebene 2 — Konstruktive Generationen (`custom/v1/`, `custom/v2/`, ...):**
   - Jede Generation kapselt eine konsistente Evolutionsstufe (z. B. `v1` = Platten-/Spacer-Baseline, `v2` = monolithischer 3D-Druck mit gekapselter Sensorik).
3. **Ebene 3 — Einstiegspunkt vs. Baustein (`v{N}/` vs. `v{N}/parts/`):**
   - **Assemblies (`*_assembly.FCStd`)** liegen als Haupteinstiegspunkte direkt im Generationsordner (`custom/v{N}/`).
   - **Einzelteile** liegen gekapselt im Unterordner `custom/v{N}/parts/`.
4. **Kanonische Dateinamen & Generations-Vererbung:**
   - Dateinamen sind **kanonisch und ohne Versions-Suffix** (z. B. `parts/femur.FCStd`, `parts/tibia.FCStd`, `leg_assembly.FCStd`), damit FreeCAD `App::Link`-Referenzen (`PropertyXLink`) und Git-Historien stabil bleiben.
   - **Chassis-Platten-Invariante (Hardware-Freeze):** Die beiden $2{,}0\,\text{mm}$ Carbonfaser-Platten ([`body_bottom.FCStd`](hardware/mechanics/models/custom/v1/parts/body_bottom.FCStd) und [`body_top.FCStd`](hardware/mechanics/models/custom/v1/parts/body_top.FCStd)) **existieren bereits als physische, fertig gefräste Hardware** und sind das **einzige Bauteil, das unverändert aus Generation `v1` in `v2` übernommen wird**. Alle anderen v1-Eigenkonstruktionen (v1-Beine, v1-Spacers) sind obsolet und werden in v2 durch bionische monolithische 3D-Druckteile ersetzt. Sämtliche v2-Neukonstruktionen (Monocoque-Zentralkern, Belly Pan, Canopy, Montageblöcke) müssen sich zwingend an das bestehende Kontur- und Bohrungsraster der physischen Carbonplatten anpassen.
   - Unveränderte Bauteile aus einer früheren Generation werden nicht kopiert, sondern per relativem `App::Link` aus der Vorgängergeneration referenziert (z. B. `../v1/parts/body_bottom.FCStd`).
   - **Fertigungsexporte (`export/{step,stl,dxf}/`):** Spiegelt die Ordnerstruktur von `models/` 1:1 für fertigbare Einzelteile (`parts/`) und COTS-Komponenten. **Assemblies (`*_assembly`) erhalten keine Fertigungsexporte** (weder STEP noch STL), da Assemblies reine logische Baugruppen/Systemeinstiegspunkte sind und niemals am Stück gedruckt oder gefertigt werden.
   - Nach jeder Pfadänderung müssen alle Assembly-`XLink`-Pfade sowie `python3 scripts/dev/check_links.py` verifiziert werden.
5. **Mechanik-Style-Guide & Bionische Formensprache:**
   - Alle Neukonstruktionen und Überarbeitungen folgen den verbindlichen Gestaltungs- und Fertigungsrichtlinien in [`hardware/mechanics/STYLE_GUIDE.md`](hardware/mechanics/STYLE_GUIDE.md) ($G^1$-stetige Taillierungen, $45^\circ$-Fachwerkfenster mit $w = 2{,}50\,\text{mm}$, $R = 1{,}4\text{--}2{,}0\,\text{mm}$ Eckenradien, $R = 1{,}0\text{--}1{,}5\,\text{mm}$ Außenfillets, DfAM-Wandstärken für PETG).
