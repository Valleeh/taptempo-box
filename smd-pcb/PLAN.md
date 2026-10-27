# Tap-Tempo-Box – SMD-Platine für JLCPCB (Entwurfsplan)

Stand: 2026-10-25. Ziel: eine 2-lagige Platine, die JLCPCB fertigt **und mit SMD-Teilen bestückt**.
Der Arduino Nano wird nicht aufgesteckt, sondern seine Schaltung (ATmega328P + USB-Chip) sitzt direkt auf der Platine.
Nicht auf der Platine: OLED, Drehgeber, TAP-Taster, MIDI-DIN-Buchse (sitzen im Gehäuse, per Kabel angeschlossen).

Das bestehende Projekt `nano-perfboard` (Lochraster-Version) ist Referenz und wird **nicht verändert**.
Alles Neue entsteht in `smd-pcb/`.

## 1. Was die Box tut (unverändert)

Tap-Tempo- und MIDI-Clock-Box: Tempo per TAP-Taster tippen oder am Drehgeber einstellen, Anzeige auf OLED,
MIDI Clock + Start/Stop über DIN-Buchse, zwei potentialfreie Schaltausgänge (Optokoppler) auf einer 3,5-mm-Stereoklinke
(z. B. Tap-Tempo-Eingang an Effektpedalen). Versorgung 9 V DC oder USB.

Referenz-Schaltplan: `nano-perfboard/taptempo.kicad_sch` (KiCad 10), Pinbelegung bleibt gleich, damit die Firmware passt:

| Signal | ATmega-Pin (Arduino-Name) |
|---|---|
| TAP-Taster (gegen GND, interner Pull-up) | D5 |
| Start/Stop (Taster im Drehgeber, gegen GND) | D4 |
| Drehgeber A / B (je 100 nF gegen GND) | D3 / D2 |
| Optokoppler 1 → Klinke Tip (220 Ω Vorwiderstand) | D10 |
| Optokoppler 2 → Klinke Ring (220 Ω) | D9 |
| MIDI OUT: DIN Pin 5 über 220 Ω an TX, DIN Pin 4 über 220 Ω an +5 V, Pin 2 GND | D1/TX |
| OLED I²C SDA / SCL | A4 / A5 |

Klinke: Tip = Kollektor Opto 1, Ring = Kollektor Opto 2, Sleeve = beide Emitter (galvanisch getrennt, **nicht** an GND).

## 2. Neue Schaltungsteile (statt Nano-Modul)

- **MCU:** ATmega328P-AU (TQFP-32), 16-MHz-Quarz (3225) + 2 × 22 pF, 100 nF an jedem VCC/AVCC, AREF 100 nF gegen GND,
  RESET 10 kΩ nach 5 V. Status-LED an D13 (1 kΩ) wie beim Nano.
- **USB:** USB-C-Buchse (nur USB 2.0), CC1/CC2 je 5,1 kΩ gegen GND. USB-Seriell-Wandler **CH340C** (interner Oszillator, kein Quarz).
  CH340C TXD → ATmega RXD (D0), CH340C RXD ← ATmega TXD (D1). Auto-Reset: DTR → 100 nF → RESET.
  Hinweis: TX geht parallel an den CH340 und an MIDI – genau wie beim Nano, das ist ok.
- **ISP-Anschluss:** 2 × 3 Pads/Stiftleiste (MISO, SCK, RESET, VCC, MOSI, GND) zum einmaligen Brennen des Arduino-Bootloaders,
  denn JLCPCB liefert den ATmega leer. Gut beschriften.
- **Versorgung:** 9 V DC → Verpolschutz-Schottky (z. B. SS14/SS34) → AMS1117-5.0 (+ Eingangs-/Ausgangskondensatoren laut Datenblatt) → +5 V.
  USB-VBUS → Schottky (SS14) → +5 V, damit sich USB und Netzteil nicht gegenseitig speisen. Optional Polyfuse 500 mA in VBUS.
  Power-LED (1 kΩ). Strombedarf gesamt < 100 mA, AMS1117 bei 9 V ok (≈ 0,4 W).
- **Netzteil-Polarität:** Effektgeräte-Netzteile haben Minus innen. Entscheidung: Buchse so beschalten, dass **Minus innen**
  (Boss-Standard) funktioniert; Verpolschutz-Diode schützt bei falschem Netzteil. Im Siebdruck „9V ⊖-◎-⊕“-Symbol (Minus innen) drucken.

## 3. Mechanik – Gehäuse 60 × 110 × 36 mm außen

Innenraum 56 × 106 mm, Wand 2 mm, Boden 2 mm, Deckel 2 mm. Gehäusemodell (CadQuery): `nano-perfboard/mech/enclosure.py`.
Koordinaten: x = Breite (0 links … 60 rechts, von vorne gesehen), y = Länge (0 vorne/TAP … 110 hinten/Display), z = Höhe.

- Deckel (fest): TAP-Taster Ø 16 bei (30, 20), tief bis z ≈ 14 → **vorderer Bereich y < 32 muss frei bleiben** (keine Platine darunter).
  Drehgeber bei (30, 52), Unterkante Beinchen z ≈ 21. OLED-Modul bei (30, 92), Unterseite z ≈ 29.
- Rechte Wand: MIDI-DIN-Einbaubuchse bei y = 68, z = 23, Körper ragt bis x ≈ 40 nach innen (z 15 … 31).
- **Neu für die SMD-Version:** USB-C-Buchse, 9-V-Hohlbuchse (5,5/2,1, Platinenmontage) und 3,5-mm-Stereoklinke
  (Platinenmontage) sitzen **auf der Platine an der hinteren Kante** und schauen durch die Rückwand.
- Platinengröße: maximal ca. 54 × 75 mm (x 3 … 57, y 32 … 107), ideal kleiner (≤ 50 × 70 hält die PCB billig; < 100 × 100 sowieso).
  4 Befestigungslöcher M3 (oder M2,5), so gelegt, dass sie nicht mit Buchsen kollidieren.
  Platine liegt auf Abstandshaltern 5 mm über dem Boden (Unterseite z = 7, Oberseite z = 8,6).
- Alle Bauteile + Stecker oberhalb der Platine müssen unter den Deckelteilen bleiben (siehe Höhen oben). SMD ist flach, kein Problem;
  Stecker für die Kabel zu Deckel/DIN dort platzieren, wo darüber Platz ist (nicht unter dem Drehgeber bei (30, 52)).

## 4. Anschlüsse für Teile außerhalb der Platine

Durchsteck-Stiftleisten 2,54 mm oder JST-XH (Wahl dokumentieren). Für Anfänger: **Stiftleisten + fertige Dupont-Kabel**.
| Stecker | Pins |
|---|---|
| OLED | 5V, SDA, SCL, GND (beschriftet) |
| Drehgeber | A, C(GND), B, SW, SW(GND) |
| TAP | TAP, GND |
| MIDI-DIN | Pin 4, Pin 2 (GND), Pin 5 |

Diese THT-Teile + Hohlbuchse/Klinke lötet der Nutzer selbst ein (oder JLCPCB-Handlötung, Kosten separat ausweisen).

## 5. Bauteilauswahl JLCPCB / LCSC

Regeln: **Basic- oder Preferred-Extended-Teile bevorzugen** (keine Rüstgebühr), Extended nur wo nötig. Alles einseitig (Oberseite) bestücken.
Passive in 0603 (Kondensatoren ≥ 10 µF ggf. 0805). Jede LCSC-Nummer **auf jlcpcb.com/parts prüfen** (Lagerbestand, Basic/Extended, Preis).
Kandidaten (zu verifizieren, nicht blind übernehmen):

| Teil | Kandidat | erwartet |
|---|---|---|
| ATmega328P-AU | C14877 | Extended |
| CH340C | C84681 | Extended |
| USB-C 16P (USB 2.0) | z. B. TYPE-C-31-M-12 C165948 oder C2765186 | Extended |
| AMS1117-5.0 | C6187 | Basic |
| SS14 / SS34 | C2480 / C8678 | Basic |
| Quarz 16 MHz 3225 | C13738 | Basic |
| Optokoppler SMD (PC817/EL817 SMD) | suchen | ? |
| Widerstände/Kondensatoren 0603, LED 0603 | Standard-Basic | Basic |

## 6. Umsetzung (Schritte)

1. Ordner `smd-pcb/kicad/` – neues KiCad-10-Projekt `taptempo-smd`.
2. Schaltplan mit allen Teilen aus 1.–4., jedem SMD-Teil Footprint + Feld `LCSC` (Teilenummer) zuordnen. ERC: 0 Fehler.
3. Platinenumriss nach 3., Bauteile platzieren (Buchsen an die Hinterkante, USB-C mittig-ish, Quarz nah am ATmega,
   Entkoppelkondensatoren direkt an den Pins, CH340C nah an USB-C), Befestigungslöcher.
4. Routen (Freerouting: `~/.kicad-mcp/freerouting.jar`, Java ist installiert) + GND-Fläche auf beiden Lagen.
   Leiterbahnen: Signal ≥ 0,25 mm, Versorgung ≥ 0,5 mm, USB D+/D− kurz und parallel. DRC: 0 Fehler (JLCPCB-Regeln: min. 0,127 mm Bahn/Abstand, Via 0,3/0,6 mm).
5. Fertigungsdaten für JLCPCB: Gerber + Bohrdaten (ZIP), **BOM-CSV** (Comment, Designator, Footprint, LCSC) und **CPL-CSV**
   (Designator, Mid X, Mid Y, Layer, Rotation). Rotations-Offsets von JLCPCB beachten und dokumentieren (häufige Fehlerquelle).
6. 3D-Export (STEP) der Platine und Einbau-Check: eine Kopie von `enclosure.py` in `smd-pcb/mech/` anpassen
   (Rückwand-Löcher für USB-C, Hohlbuchse, Klinke an den echten Positionen; Abstandshalter an den Befestigungslöchern),
   STL/STEP erzeugen und auf Kollisionen prüfen. Die venv in `nano-perfboard/mech/.venv` (CadQuery) darf benutzt werden.
7. Kostenschätzung mit den echten Zahlen: Teilezahl, Lötstellen, Anzahl Extended-Sorten, Preis für 5 Platinen (davon 2 bzw. 5 bestückt),
   Versand nach Deutschland, 19 % MwSt.
8. `README.md`: was wo liegt, Bestellanleitung JLCPCB Schritt für Schritt, Bootloader brennen (Arduino as ISP / USBasp),
   offene Punkte.

## 7. Abnahmekriterien

- ERC 0 Fehler, DRC 0 Fehler, alle Netze geroutet.
- Platine passt ins Gehäuse ohne Kollision; Buchsen fluchten mit Rückwand-Löchern.
- BOM: jede Position hat eine LCSC-Nummer, die lieferbar ist; Extended-Teile ≤ 5 Sorten.
- Pinbelegung exakt wie Tabelle in 1. (Firmware-kompatibel mit Nano-Version).
- Nichts bestellen, keine Accounts anlegen, `nano-perfboard` nicht verändern.

## 8. Bekannte Stolpersteine (aus der bisherigen Arbeit)

- KiCad-MCP-Server (Tools `mcp__kicad__*`) ist eingerichtet. Bibliothekstabellen liegen in `~/.config/kicad/10.0/`.
- Der MCP kann Footprints auf der Platine nicht tauschen (`replace_component` fehlt): Footprint im Schaltplan ändern,
  Footprint-Block aus der `.kicad_pcb` entfernen (Textbearbeitung), dann `sync_schematic_to_board`.
- Python-`pcbnew` (KiCad 10, Python 3.14) wird nach Änderungen am Board instabil (SWIG-Typfehler) – lieber Text-Edits oder kicad-cli.
- Nach externen Dateiänderungen `open_board` neu aufrufen, sonst verweigert der MCP das Speichern.
- Freerouting nimmt bestehende Bahnen mit; vor einem Neu-Routing alle `(segment …)`/`(via …)` aus der Datei entfernen.
- `MountingHole:MountingHole_3.2mm` gibt es nicht, richtig ist `MountingHole:MountingHole_3.2mm_M3`.
