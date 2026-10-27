"""Generate the beginner build guide (guide/index.html) from the verified layout data."""
import html, os
import perfboard as P
import drawings as D

HERE = os.path.dirname(os.path.abspath(__file__))
assert not P.check(), P.check()

NET_TEXT = {
    "OPTO1": "D10 → Widerstand R3", "OK1_A": "R3 → Optokoppler U2", "OK2_A": "R4 → Optokoppler U3",
    "TIP": "U2 → Klinke Tip", "SLEEVE": "Optokoppler → Klinke Sleeve", "SDA": "A4 → Display SDA",
    "SCL": "A5 → Display SCL", "GND": "Masse (GND)", "ENC_A": "C1 an Drehgeber A", "ENC_B": "C2 an Drehgeber B",
    "MIDI_4": "R1 → MIDI Pin 4", "MIDI_5": "R2 → MIDI Pin 5", "VIN9": "9 V → Diode", "VIN": "Diode → Nano VIN",
    "OPTO2": "D9 → Widerstand R4", "RING": "U3 → Klinke Ring", "+5V": "5 V vom Nano",
    "MIDI_TX": "TX → Widerstand R2", "TAP": "D5 → TAP-Leiste", "STARTSTOP": "D4 → Drehgeber-Taster",
}
WIRE_HEX = D.WIRE_HEX


def esc(s):
    return html.escape(str(s))


def bare_rows():
    rows = []
    for i, (net, pts) in enumerate(P.BARE, 1):
        path = " → ".join(pts)
        kind = "Bein umbiegen oder Lötbrücke" if len(pts) == 2 and _adjacent(pts[0], pts[1]) else "blanker Draht"
        rows.append(f'<tr><td><input type="checkbox" class="tick" id="b{i}" aria-label="Brücke {i} erledigt"></td>'
                    f'<td class="num">B{i}</td><td class="mono">{esc(path)}</td><td>{esc(NET_TEXT[net])}</td>'
                    f'<td class="muted">{kind}</td></tr>')
    return "\n".join(rows)


def _adjacent(a, b):
    (ca, ra), (cb, rb) = P.cr(a), P.cr(b)
    return abs(ca - cb) + abs(ra - rb) == 1


def ins_rows():
    rows = []
    for i, (net, a, b, color) in enumerate(P.INSULATED, 1):
        rows.append(f'<tr><td><input type="checkbox" class="tick" id="w{i}" aria-label="Draht {i} erledigt"></td>'
                    f'<td class="num"><span class="wtag" style="border-color:{WIRE_HEX[color]}">{i}</span></td>'
                    f'<td class="mono">{esc(a)} → {esc(b)}</td><td>{esc(NET_TEXT[net])}</td>'
                    f'<td><span class="swatch" style="background:{WIRE_HEX[color]}"></span>{esc(color)}</td></tr>')
    return "\n".join(rows)


def holes(ref):
    c = next(c for c in P.COMPONENTS if c["ref"] == ref)
    return ", ".join(f"{h} ({lab})" if lab else h for h, (lab, _) in c["pins"].items())


SKETCH = open(os.path.join(HERE, "..", "..", "firmware", "taptempo_test", "taptempo_test.ino")).read()

PAGE = f"""<title>Tap-Tempo-Box Bauanleitung</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Semi+Condensed:wght@600;700&family=Barlow:ital,wght@0,400;0,500;0,600;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* Layout: a workshop manual — one readable column, drawings full width, tick-off tables. */
:root {{
  --bg: #f4f5f6; --panel: #ffffff; --ink: #1d232b; --muted: #5d6874; --line: #d9dde2;
  --accent: #c8282d; --warn-bg: #fff4e5; --warn-ink: #7a4300; --ok: #2a7a3a; --code: #f0f2f4;
  --pb-board: #c9a46a; --pb-edge: #8a6a3a; --pb-pad: #e4e4e4; --pb-drill: #5a4a30;
  --display: "Barlow Semi Condensed", "Arial Narrow", sans-serif;
  --body: "Barlow", "Helvetica Neue", Arial, sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, Menlo, Consolas, monospace;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --bg: #14181d; --panel: #1b2027; --ink: #e6e9ed; --muted: #9aa5b1; --line: #2e353e;
    --accent: #ff5a5f; --warn-bg: #3a2a12; --warn-ink: #ffcf8a; --ok: #6fd08a; --code: #222831;
    --pb-board: #b8925a; --pb-edge: #6d5330; --pb-pad: #d4d4d4; --pb-drill: #4a3c26; color-scheme: dark;
  }}
}}
:root[data-theme="dark"] {{
  --bg: #14181d; --panel: #1b2027; --ink: #e6e9ed; --muted: #9aa5b1; --line: #2e353e;
  --accent: #ff5a5f; --warn-bg: #3a2a12; --warn-ink: #ffcf8a; --ok: #6fd08a; --code: #222831;
  --pb-board: #b8925a; --pb-edge: #6d5330; --pb-pad: #d4d4d4; --pb-drill: #4a3c26; color-scheme: dark;
}}
body {{ background: var(--bg); color: var(--ink); font: 16px/1.6 var(--body);
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px));
  padding-block: 24px 64px; }}
main {{ max-width: 860px; margin: 0 auto; display: flex; flex-direction: column; gap: 28px; }}
header h1 {{ font: 700 clamp(30px, 5vw, 44px)/1.05 var(--display); margin: 0; letter-spacing: .005em; text-wrap: balance; }}
header p {{ margin: 8px 0 0; color: var(--muted); max-width: 62ch; }}
.facts {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }}
.facts span {{ background: var(--panel); border: 1px solid var(--line); border-radius: 4px; padding: 4px 10px; font-size: 14px; }}
section {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 20px 22px; min-width: 0; }}
h2 {{ font: 700 26px/1.15 var(--display); margin: 0 0 10px; text-wrap: balance; }}
h2 .step {{ color: var(--accent); margin-right: 8px; font-variant-numeric: tabular-nums; }}
h3 {{ font: 600 14px/1.2 var(--display); text-transform: uppercase; letter-spacing: .1em; color: var(--muted); margin: 18px 0 8px; }}
p, li {{ max-width: 68ch; }}
ul, ol {{ padding-left: 22px; margin: 6px 0; display: grid; gap: 4px; }}
.mono, code {{ font-family: var(--mono); font-size: .9em; }}
code {{ background: var(--code); padding: 1px 5px; border-radius: 3px; }}
.muted {{ color: var(--muted); }}
.warn {{ background: var(--warn-bg); color: var(--warn-ink); border-radius: 6px; padding: 10px 14px; margin: 12px 0; }}
.warn strong {{ color: inherit; }}
.table-wrap {{ overflow-x: auto; }}
table {{ border-collapse: collapse; width: 100%; font-size: 15px; }}
th, td {{ text-align: left; padding: 6px 8px; border-bottom: 1px solid var(--line); vertical-align: top; }}
th {{ font: 600 13px var(--display); text-transform: uppercase; letter-spacing: .08em; color: var(--muted); }}
td.num {{ font-family: var(--mono); font-variant-numeric: tabular-nums; white-space: nowrap; }}
.tick {{ width: 18px; height: 18px; accent-color: var(--ok); }}
tr:has(.tick:checked) td:not(:first-child) {{ color: var(--muted); text-decoration: line-through; text-decoration-color: var(--ok); }}
.swatch {{ display: inline-block; width: 12px; height: 12px; border-radius: 2px; margin-right: 6px; vertical-align: -1px; border: 1px solid #0003; }}
.wtag {{ display: inline-grid; place-items: center; width: 22px; height: 22px; border-radius: 50%; border: 3px solid; font-weight: 700; font-size: 12px; }}
.boards {{ display: grid; grid-template-columns: minmax(0, 640px); justify-content: center; gap: 28px; }}
.boards figure {{ margin: 0; min-width: 0; }}
figcaption {{ font-size: 14px; color: var(--muted); margin-top: 4px; }}
figcaption strong {{ color: var(--ink); }}
.steps {{ counter-reset: s; list-style: none; padding: 0; }}
.steps > li {{ counter-increment: s; display: grid; grid-template-columns: 28px 1fr; gap: 10px; align-items: start; }}
.steps > li::before {{ content: counter(s); font: 700 15px/26px var(--display); color: #fff; background: var(--accent); border-radius: 50%; width: 26px; text-align: center; }}
pre {{ background: var(--code); border-radius: 6px; padding: 14px; overflow-x: auto; font: 13px/1.5 var(--mono); }}
.progress {{ font-size: 14px; color: var(--muted); }}
{D.CSS}
@media (max-width: 720px) {{ section {{ padding: 16px; }} }}
</style>

<main>
<header>
  <h1>Tap-Tempo-Box löten</h1>
  <p>Schritt für Schritt auf einer Lochrasterplatine, ohne Vorkenntnisse. Alles, was man falsch herum einsetzen kann, ist markiert. Hake beim Löten ab, was erledigt ist; die Haken bleiben in diesem Browser gespeichert.</p>
  <div class="facts"><span>Zeit: ca. 4–6 Stunden</span><span>Platine 5 × 7 cm, 18 × 24 Löcher</span><span>{len(P.BARE)} Brücken, {len(P.INSULATED)} Drähte</span><span class="progress" id="progress">0 erledigt</span></div>
</header>

<section>
  <h2>Einkaufsliste</h2>
  <div class="table-wrap"><table>
    <thead><tr><th>Anzahl</th><th>Teil</th><th>Hinweis</th></tr></thead>
    <tbody>
      <tr><td>1</td><td>Lochrasterplatine 5 × 7 cm (Lötpunkte, 2,54 mm)</td><td>doppelseitig verzinnt ist leichter zu löten</td></tr>
      <tr><td>1</td><td>Arduino Nano (Klon reicht)</td><td>mit Mini-USB oder USB-C, beides passt</td></tr>
      <tr><td>2</td><td>Buchsenleiste 15-polig, 2,54 mm</td><td>Sockel für den Nano</td></tr>
      <tr><td>2</td><td>IC-Sockel 4-polig (DIP-4)</td><td>oder einen 8-poligen durchsägen</td></tr>
      <tr><td>2</td><td>Optokoppler PC817</td><td>DIP-Gehäuse</td></tr>
      <tr><td>4</td><td>Widerstand 220 Ω, ¼ W</td><td>Farbringe Rot-Rot-Braun</td></tr>
      <tr><td>2</td><td>Kondensator 100 nF (Keramik, „104“)</td><td>Rastermaß 2,5 mm</td></tr>
      <tr><td>1</td><td>Schottky-Diode 1N5817</td><td>Verpolschutz</td></tr>
      <tr><td>1</td><td>Stiftleiste gerade, 1 × 40</td><td>für Display und Klinke</td></tr>
      <tr><td>1</td><td>Stiftleiste gewinkelt 90°, 1 × 40</td><td>für die vordere Reihe</td></tr>
      <tr><td>1 Pack</td><td>Dupont-Kabel Buchse–Buchse, 20 cm</td><td>werden halbiert, kein Crimpen nötig</td></tr>
      <tr><td>1</td><td>Drehgeber EC11 <em>mit Drucktaster</em> + Knopf</td><td>5 Beine: 3 vorne, 2 hinten</td></tr>
      <tr><td>1</td><td>Drucktaster 16 mm, nicht rastend</td><td>max. 22 mm tief</td></tr>
      <tr><td>1</td><td>OLED 0,96″ I²C (SSD1306), 4 Pins</td><td>27 × 28 mm</td></tr>
      <tr><td>1</td><td>MIDI-Einbaubuchse DIN 5-polig 180°</td><td>mit 2 Schraublöchern</td></tr>
      <tr><td>1</td><td>Klinken-Einbaubuchse 3,5 mm Stereo</td><td>Gewinde M6</td></tr>
      <tr><td>1</td><td>Hohlstecker-Einbaubuchse 5,5/2,1 mm</td><td>passend zu deinem Netzteil</td></tr>
      <tr><td>je 4</td><td>Schrauben M2 × 6 und M3 × 8 (Senkkopf)</td><td>Platine bzw. Deckel</td></tr>
      <tr><td></td><td>Schaltdraht (isoliert) in mehreren Farben, verzinnter Draht 0,5 mm, Schrumpfschlauch</td><td></td></tr>
    </tbody>
  </table></div>
  <h3>Werkzeug</h3>
  <p>Lötkolben mit Temperaturregelung, Lötzinn 0,8 mm mit Flussmittel, Seitenschneider, Abisolierzange, Multimeter mit Piepser, „dritte Hand“ oder Knete zum Festhalten, Filzstift.</p>
</section>

<section>
  <h2>Fünf Regeln fürs Löten</h2>
  <ol>
    <li>Lötkolben auf ca. 330 °C. Die Spitze immer leicht verzinnt halten, am nassen Schwamm oder Messingwolle abwischen.</li>
    <li>Erst Pad und Bein 1–2 Sekunden gleichzeitig erhitzen, dann das Zinn an die Stelle halten (nicht an die Spitze).</li>
    <li>Eine gute Lötstelle glänzt und sieht aus wie ein kleiner Vulkan. Eine Kugel oder graue Krümel: noch mal erhitzen.</li>
    <li>Nach jedem Bauteil die Beine kurz abschneiden. Nicht länger als 3–4 Sekunden auf einer Stelle bleiben.</li>
    <li>Nie löten, solange USB oder Netzteil angeschlossen ist. Gut lüften.</li>
  </ol>
</section>

<section>
  <h2>Der Lochplan</h2>
  <p>Die Löcher sind wie auf einem Steckbrett benannt: Spalten <strong>A–R</strong> von links nach rechts, Reihen <strong>1–24</strong> von hinten nach vorne. <code>K12</code> heißt Spalte K, Reihe 12.</p>
  <div class="warn"><strong>Wichtig:</strong> Von unten ist alles seitenverkehrt. Schreib mit Filzstift auf <em>beide</em> Seiten der Platine „A1“ an die Ecke links hinten (von oben gesehen) und „R24“ an die gegenüberliegende Ecke. Dann kannst du dich nicht verzählen.</div>
  <div class="boards">
    <figure>{D.component_side()}<figcaption><strong>Bestückungsseite</strong>, von oben. Hier stecken die Bauteile.</figcaption></figure>
    <figure>{D.solder_side()}<figcaption><strong>Lötseite</strong>, von unten (gespiegelt). Grau: blanke Brücken. Farbig: isolierte Drähte mit Nummer.</figcaption></figure>
  </div>
</section>

<section>
  <h2><span class="step">1</span>Flache Bauteile</h2>
  <p>Immer vom flachsten zum höchsten Bauteil löten, dann liegt die Platine beim Umdrehen plan auf. Bein durchstecken, auf der Unterseite leicht auseinanderbiegen, löten, abschneiden.</p>
  <ul class="steps">
    <li><span><strong>R1–R4</strong> (220 Ω, Rot-Rot-Braun). Richtung egal.<br><span class="mono muted">R1: P19–P23 · R2: R19–R23 · R3: L3–L7 · R4: L8–L12</span></span></li>
    <li><span><strong>D1</strong> (1N5817): A20–E20. <strong>Der Ring zeigt nach rechts zu E20</strong>, zum Nano.</span></li>
    <li><span><strong>C1</strong>: F23–G23 und <strong>C2</strong>: I23–J23. Richtung egal.</span></li>
    <li><span><strong>IC-Sockel</strong> U2 (M7, M8, P7, P8) und U3 (M12, M13, P12, P13). Die Kerbe des Sockels zeigt nach hinten (zu Reihe 1), dann weißt du später, wo Pin 1 hinkommt.</span></li>
  </ul>
</section>

<section>
  <h2><span class="step">2</span>Sockel und Stiftleisten</h2>
  <ul class="steps">
    <li><span><strong>Nano-Sockel</strong>: je eine 15-polige Buchsenleiste in E1–E15 und K1–K15. Trick: Den Nano zum Löten einstecken, dann sitzen beide Leisten garantiert im richtigen Abstand. Erst je ein Bein an den Enden löten, Sitz prüfen, dann den Rest. Danach den Nano wieder herausziehen.</span></li>
    <li><span><strong>Gerade Stiftleisten</strong> (kurze Seite in die Platine): 4 Pins in B7–B10 (Display) und 3 Pins in R7–R9 (Klinke).</span></li>
    <li><span><strong>Gewinkelte Stiftleisten</strong> in Reihe 24, Stifte zeigen nach vorne über den Platinenrand hinaus: A24–B24 (9 V), G24–K24 (Drehgeber), M24–N24 (TAP), P24–R24 (MIDI).</span></li>
  </ul>
</section>

<section>
  <h2><span class="step">3</span>Brücken auf der Lötseite</h2>
  <p>Grau im Lochplan. Bei direkt benachbarten Löchern einfach ein abgeschnittenes Bein oder einen Tropfen Zinn als Brücke nehmen. Bei längeren Strecken verzinnten Draht auf die Lötpunkte legen und an <em>jedem</em> genannten Punkt verlöten. Blanker Draht darf keine anderen Lötpunkte berühren.</p>
  <div class="table-wrap"><table>
    <thead><tr><th></th><th>Nr.</th><th>Von → nach</th><th>Wofür</th><th>Wie</th></tr></thead>
    <tbody>{bare_rows()}</tbody>
  </table></div>
</section>

<section>
  <h2><span class="step">4</span>Isolierte Drähte</h2>
  <p>Farbig im Lochplan, mit Nummer. Draht etwas länger abschneiden als nötig, Enden 3 mm abisolieren, verzinnen und direkt an den Lötpunkt des Bauteilbeins anlöten. Diese Drähte dürfen sich kreuzen.</p>
  <div class="table-wrap"><table>
    <thead><tr><th></th><th>Nr.</th><th>Von → nach</th><th>Wofür</th><th>Farbe</th></tr></thead>
    <tbody>{ins_rows()}</tbody>
  </table></div>
</section>

<section>
  <h2><span class="step">5</span>Durchmessen, bevor Strom drauf kommt</h2>
  <p>Multimeter auf Durchgang (Piepser). Nano und Optokoppler sind noch <em>nicht</em> eingesteckt.</p>
  <ul>
    <li><strong>Kein Piep</strong> zwischen E12 (5V) und E14 (GND). Piept es: Kurzschluss suchen, nicht weitermachen.</li>
    <li><strong>Kein Piep</strong> zwischen A24 (+9 V) und B24 (GND).</li>
    <li><strong>Piep</strong> zwischen E14 und jedem dieser Punkte: B10, B24, H24, K24, N24, Q24, M8, M13.</li>
    <li><strong>Piep</strong> zwischen K8 und M24 (TAP), K9 und J24, K10 und G24, K11 und I24.</li>
    <li><strong>Piep</strong> zwischen E8 und B8 (SDA), E9 und B9 (SCL), E12 und B7, E12 und P19.</li>
    <li>Dioden-Messbereich: Rot an A20, Schwarz an E20 zeigt ca. 0,2–0,3 V. Andersherum: nichts.</li>
    <li>Mit der Lupe: keine Zinnbrücken zwischen benachbarten Lötpunkten, vor allem an den Nano-Leisten.</li>
  </ul>
</section>

<section>
  <h2><span class="step">6</span>Kabel für Deckel und Buchsen</h2>
  <p>Dupont-Kabel in der Mitte durchschneiden. Die Buchse (schwarzes Steckerende) kommt auf die Stiftleiste, das freie Ende wird an das Bauteil gelötet. Über jede Lötstelle Schrumpfschlauch. Kabel lang genug lassen, dass sich der Deckel aufklappen lässt (ca. 15 cm).</p>
  <div class="table-wrap"><table>
    <thead><tr><th>Teil</th><th>Leiste</th><th>Anschluss</th></tr></thead>
    <tbody>
      <tr><td>TAP-Taster</td><td class="mono">M24, N24</td><td>beide Beine des Tasters, Richtung egal</td></tr>
      <tr><td>Drehgeber</td><td class="mono">G24–K24</td><td>3er-Seite: links A → G24, Mitte C → H24, rechts B → I24. 2er-Seite (Taster) → J24 und K24. Dreht er falsch herum, A und B tauschen.</td></tr>
      <tr><td>Display</td><td class="mono">B7–B10</td><td>nach Beschriftung: VCC → 5V (B7), SDA → B8, SCL → B9, GND → B10. Die Reihenfolge am Display ist je nach Hersteller anders; nur die Namen zählen. Am Display die Kabel direkt anlöten, kein Dupont-Stecker (sonst wird es unter dem Deckel zu hoch). Hat das Display schon Stifte, die Kabel daran löten und die Stifte danach kürzen.</td></tr>
      <tr><td>MIDI-Buchse</td><td class="mono">P24, Q24, R24</td><td>Pin 4 → P24, Pin 2 (mittlerer Kontakt) → Q24, Pin 5 → R24. Die Nummern stehen meist klein neben den Lötfahnen. Pins 1 und 3 bleiben frei.</td></tr>
      <tr><td>Klinkenbuchse</td><td class="mono">R7, R8, R9</td><td>Tip → R7, Sleeve → R8, Ring → R9. Welche Fahne was ist: Stecker einstecken und mit dem Piepser suchen.</td></tr>
      <tr><td>9-V-Buchse</td><td class="mono">A24 (+), B24 (−)</td><td>siehe Hinweis zum Netzteil</td></tr>
    </tbody>
  </table></div>
  <div class="warn"><strong>Netzteil:</strong> Auf dem Netzteil ist ein kleines Symbol mit Plus und Minus. Effektgeräte-Netzteile (Boss-Standard) haben <strong>Minus innen</strong>: dann den Mittelstift der Buchse an B24 (−) und den äußeren Kontakt an A24 (+). Bei „Plus innen“ genau umgekehrt. Falsch herum geht nichts kaputt (dafür ist die Diode da), die Box bleibt nur aus.</div>
</section>

<section>
  <h2><span class="step">7</span>Einstecken und erster Test</h2>
  <ul class="steps">
    <li><span><strong>Optokoppler</strong> in die Sockel: Der Punkt auf dem Chip kommt nach links oben, auf <code>M7</code> bzw. <code>M12</code>.</span></li>
    <li><span><strong>Nano</strong> in den Sockel: USB-Buchse nach hinten zu Reihe 1. Pin „D12“ steckt in K1, „VIN“ in E15. Die Beschriftung auf dem Nano muss zum Lochplan passen.</span></li>
    <li><span>Nur USB anschließen. Arduino IDE installieren, Bibliothek <strong>U8g2</strong> installieren (Werkzeuge → Bibliotheken verwalten), Board „Arduino Nano“ wählen. Bei Klonen unter Prozessor „ATmega328P (Old Bootloader)“ probieren, falls das Hochladen scheitert.</span></li>
    <li><span>Test-Sketch unten hochladen. Das Display zeigt „Hardware-Test“. TAP und Drehgeber-Taster müssen „an“ anzeigen, Drehen zählt hoch und runter.</span></li>
    <li><span>Klinken-Ausgang: Multimeter auf Durchgang zwischen Tip und Sleeve der Klinkenbuchse. Es piept im Sekundentakt abwechselnd mit Ring–Sleeve.</span></li>
    <li><span>Dann das 9-V-Netzteil statt USB: Display muss wieder angehen.</span></li>
  </ul>
  <h3>Test-Sketch</h3>
  <pre><code>{esc(SKETCH)}</code></pre>
</section>

<section>
  <h2><span class="step">8</span>Einbau</h2>
  <ul class="steps">
    <li><span>Buchsen in die Rückwand (9 V links, 3,5 mm rechts) und die MIDI-Buchse in die rechte Seitenwand schrauben. Passt eine Buchse nicht durchs Loch, vorsichtig aufbohren.</span></li>
    <li><span>Platine mit 4 Schrauben M2 auf die Abstandshalter, USB-Buchse zeigt zur Rückwand in die Öffnung.</span></li>
    <li><span>Taster, Drehgeber (mit Mutter) und Display (4 kleine Schrauben M2) am Deckel befestigen, Kabel aufstecken.</span></li>
    <li><span>Deckel mit 4 Schrauben M3 zuschrauben.</span></li>
  </ul>
</section>

<section>
  <h2>Wenn etwas nicht geht</h2>
  <ul>
    <li><strong>Display bleibt dunkel:</strong> SDA und SCL vertauscht oder VCC/GND falsch. Bei manchen Displays steht die Adresse 0x3D statt 0x3C.</li>
    <li><strong>Nano wird heiß:</strong> sofort abstecken, Kurzschluss zwischen 5V und GND suchen (Schritt 5).</li>
    <li><strong>Taster reagiert nicht:</strong> Durchgang von der Stiftleiste zum Nano-Pin messen (Drahttabelle).</li>
    <li><strong>MIDI kommt nicht an:</strong> Pin 4 und Pin 5 an der Buchse tauschen. Dabei geht nichts kaputt.</li>
    <li><strong>Klinke schaltet nicht:</strong> Optokoppler falsch herum im Sockel (Punkt nach links oben).</li>
  </ul>
</section>
</main>

<script>
(function () {{
  const KEY = "taptempo-guide-ticks";
  let saved = {{}};
  try {{ saved = JSON.parse(localStorage.getItem(KEY) || "{{}}"); }} catch (e) {{ saved = {{}}; }}
  const boxes = Array.from(document.querySelectorAll(".tick"));
  const progress = document.getElementById("progress");
  function update() {{
    const done = boxes.filter((b) => b.checked).length;
    progress.textContent = done + " von " + boxes.length + " Verbindungen erledigt";
  }}
  boxes.forEach((b) => {{
    b.checked = !!saved[b.id];
    b.addEventListener("change", () => {{
      saved[b.id] = b.checked;
      try {{ localStorage.setItem(KEY, JSON.stringify(saved)); }} catch (e) {{}}
      update();
    }});
  }});
  update();
}})();
</script>
"""

if __name__ == "__main__":
    os.makedirs(os.path.join(HERE, "guide"), exist_ok=True)
    open(os.path.join(HERE, "guide", "index.html"), "w").write(PAGE)
    print("ok", len(PAGE) // 1024, "KB")
