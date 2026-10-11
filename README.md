# HTW Studienplaner

[![CI](https://github.com/eljakj/htw-studienplaner/actions/workflows/ci.yml/badge.svg)](https://github.com/eljakj/htw-studienplaner/actions/workflows/ci.yml)

**English:** A static single-page web app (one HTML file, vanilla JS, no framework) to plan the Bachelor programme "Angewandte Informatik (B)" at HTW Berlin. Every module is a hexagon in the colors of the study plan; one click sets its status, and the credit points are counted. The plan stays in your browser (`localStorage`); there is no account, no server-side storage and no tracking. The module catalog is written in Python and embedded at build time. Tests: pytest (unit) and Playwright (E2E); delivery: Docker with nginx, GitHub Actions, image on GHCR. Several local plans, deleting with undo, export/import as a JSON file and a backup reminder are included. Status: feature complete for version 1.0, see [Status und Roadmap](#status-und-roadmap). Everything below is in German; setup commands work on Windows, Linux and macOS.

**Deutsch:** Interaktiver Studienverlaufsplan für den Bachelor **Angewandte Informatik (B)** an der HTW Berlin. Jedes Modul ist ein Sechseck in den Farben des Studienverlaufsplans. Ein Klick setzt den Status, und die Leistungspunkte (LP) werden mitgezählt. Der Plan bleibt in deinem Browser: kein Konto, kein Server-Speicher, kein Tracking.

**Live-Demo:** <https://eljakj.github.io/htw-studienplaner/> (GitHub Pages, dieselbe neutrale Seite wie im Docker-Image; der Link funktioniert erst, wenn Pages im Repository aktiviert ist, siehe [docs/architecture.md](docs/architecture.md)).

> Inoffizielles Projekt, kein Angebot der HTW Berlin. Alle Angaben ohne Gewähr; maßgeblich sind die Studienordnung (SPO) und das LSF.

![Studienverlauf mit fiktivem Beispielprofil, dunkles Theme](docs/screenshot-dark.png)

<details>
<summary>Helles Theme</summary>

![Studienverlauf mit fiktivem Beispielprofil, helles Theme](docs/screenshot-light.png)

</details>

Die Screenshots zeigen ein **fiktives** Beispielprofil.

## Funktionen

- **Status pro Modul:** bestanden, läuft jetzt, Prüfung nachholen, kein Platz, später geplant. Nur bestandene Module zählen zu den 180 LP.
- **Auswahl per Dropdown** statt Kürzel-Tippen: 5 Wahlpflichtplätze (19 Module), 2 AWE-Plätze (73 Kurse) und 2 Fremdsprachenplätze (22 Kurse).
- **Studienbeginn:** Du wählst Sommer- oder Wintersemester und das Jahr; daraus ergibt sich das aktuelle Fachsemester („jetzt“). Die Grenzen folgen dem Akademischen Kalender der HTW (Sommersemester 1.4. bis 30.9., Wintersemester 1.10. bis 31.3.; geprüft an den Kalendern SoSe 2025, SoSe 2026 und WiSe 2026/27). Ab dem 7. Semester bleibt „jetzt“ beim 6. Semester mit dem Hinweis „über Regelstudienzeit“; liegt der Beginn in der Zukunft, ist kein Semester markiert.
- **Erstbesuch:** Solange noch kein Plan gespeichert ist, zeigt die Seite über dem Plan die Karte „Wie möchtest du starten?“. „Eigenen Plan starten“ führt in drei Klicks zum eigenen Plan: Start anklicken, Sommer- oder Wintersemester wählen, Jahr tippen und „Los“. Danach ist das richtige Semester markiert, und die Karte erscheint nicht wieder. „Plan importieren“ öffnet den Dateiauswahldialog für eine Sicherung (siehe Import).
- **Beispielplan:** „Beispiel ansehen“ auf der Startkarte, der Link „Beispielplan ansehen“ am Seitenende oder die Adresse `…/#beispiel` zeigen einen Plan mit **erfundenen** Daten (4. Semester, relativ zu heute). Ein Banner weist darauf hin. Im Beispiel wird nichts gespeichert, auch nicht beim Ändern oder Neuladen, und der eigene Plan bleibt unberührt. „Eigenen Plan starten“ im Banner verlässt das Beispiel: ohne gespeicherten Plan geht es mit der Startauswahl weiter, mit gespeichertem Plan zurück zum eigenen Plan. Die Beispieldaten stehen in [`demo/profile.demo.json`](demo/README.md) und sind in jedem Build enthalten.
- **Voraussetzungen:** Hinweise auf notwendige und empfohlene Voraussetzungen.
- **Rückgängig / Wiederholen** (Strg+Z, Strg+Y), **Semesterstart** (alle Plätze leeren) und Umschalter für **dunkles und helles Theme**.
- **Export:** „Exportieren“ in der Werkzeugzeile lädt deinen Plan als JSON-Datei herunter, zum Beispiel `studienverlauf-mein-plan-2026-10-11.json`. Die Datei enthält dein Profil (Name, Studienbeginn, Status, Notizen, gewählte Module), den Katalogstand („LSF WiSe 2026/27“) und den Zeitpunkt des Exports. Sie entsteht komplett in deinem Browser, es gibt keine Anfrage an einen Server, und der Export schreibt nichts in den Speicher. Er geht auch bei gesperrtem Speicher. Im Beispielplan ist der Knopf deaktiviert, denn exportiert wird immer der eigene Plan.
- **Import:** „Importieren“ in der Werkzeugzeile (und „Plan importieren“ auf der Startkarte) öffnet den Dateiauswahldialog. Die Seite prüft die Datei, bevor sich irgendetwas ändert, und zeigt eine Vorschau wie „47 LP bestanden – übernehmen?“ mit Name, Studienbeginn und Katalogstand. Was nicht passt, wird verworfen und aufgelistet: unbekannte Plätze, Status und Module, ungültiger Studienbeginn, auf 28 Zeichen gekürzte Notizen. Texte aus der Datei werden nur als Text gesetzt, nie als HTML. „Übernehmen“ **ersetzt** den ganzen aktuellen Plan; die Vorschau nennt dessen LP und rät zum vorherigen Export. Ungültige Dateien (kein JSON, falsche Form, fremde Datei, unbekannte Version, größer als 1 MB) ändern nichts und nennen den Grund. Alte Dateien im v1-Format (ohne `app` und `v`, nur `m` und `names`) werden übernommen. Im Beispielplan ist der Import deaktiviert.
- **Mehrere Pläne:** Über dem Plan wählst du den Plan im Umschalter, legst mit „Neuer Plan“ einen weiteren an (höchstens 20), und „Name ändern“ öffnet Name (bis 40 Zeichen) und Untertitel (bis 80 Zeichen); der Untertitel ersetzt die Zeile unter der Überschrift. Jede Änderung wird sofort gespeichert, beim Umschalten geht nichts verloren. Jeder Tab kann einen anderen Plan offen haben. Export und Import arbeiten mit dem gerade offenen Plan; beim Import gibt es zusätzlich „Als neuen Plan hinzufügen“.
- **Löschen mit Rückgängig:** „Löschen“ fragt direkt in der Seite nach („Plan „…“ (N LP bestanden) wirklich löschen?“). Danach bringt „Rückgängig“ den Plan zurück, solange die Seite offen bleibt. Wird der letzte Plan gelöscht, erscheint wieder die Startauswahl.
- **Sicherungs-Erinnerung:** Ist ein Plan seit 30 Tagen nicht exportiert (oder wurde nie exportiert und ist älter als 30 Tage), erscheint ein Hinweis mit „Jetzt exportieren“ und „Später“. Jeder Export stellt die Uhr für diesen Plan zurück. Leere Pläne und das Beispiel lösen keinen Hinweis aus.
- **Katalog-Updates:** Gibt es ein gespeichertes Modul oder einen Platz nach einem Katalogwechsel nicht mehr, nennt die Seite das einmal („Der Katalog hat sich geändert …“) und speichert den bereinigten Plan. Status und Notizen bleiben erhalten.
- **Ohne Backend:** eine einzelne HTML-Datei. Der Stand liegt nur im `localStorage` deines Browsers (Schlüssel `studienverlauf-ai-v2`) und wird bei jeder Änderung still gespeichert. Mehrere offene Tabs gleichen sich ab. Kann der Browser nicht speichern (privates Fenster, gesperrter Speicher), zeigt die Seite sofort einen Hinweis und bleibt benutzbar. Ein Stand aus dem alten Schlüssel `studienverlauf-ai-v1` wird beim ersten Laden einmal übernommen; der alte Schlüssel bleibt unverändert stehen.

## Schnellstart

Du brauchst Python 3 und Git. Der Build benötigt keine weiteren Pakete.

**Linux, macOS, WSL2 (bash):**

```bash
git clone https://github.com/eljakj/htw-studienplaner.git
cd htw-studienplaner
python3 build.py
xdg-open dist/index.html      # macOS: open dist/index.html
```

**Windows (PowerShell):**

```powershell
git clone https://github.com/eljakj/htw-studienplaner.git
cd htw-studienplaner
python build.py
start dist\index.html
```

`build.py` schreibt `dist/index.html`, eine einzelne Datei. Du kannst sie direkt im Browser öffnen. Der Build ist immer neutral: Er enthält nur den Katalog, den erfundenen Beispielplan und keine persönlichen Daten; es gibt keine Option für eigene Startwerte. Deinen eigenen Plan legst du im Browser an oder importierst ihn aus einer Sicherungsdatei. Alle Optionen zeigt `python build.py --help`.

## Entwickeln und testen

Einmalig: virtuelle Umgebung anlegen und die Test-Pakete installieren.

```bash
python -m venv .venv
source .venv/bin/activate         # Linux, macOS, WSL2
source .venv/Scripts/activate     # Git Bash unter Windows
pip install -r requirements-dev.txt
python -m playwright install chromium
```

In PowerShell aktivierst du die Umgebung mit `.venv\Scripts\Activate.ps1`.

```bash
python -m pytest              # Unit-Tests (Katalog, Build, nginx-Konfiguration, Image-Tags)
python -m pytest tests/e2e    # Browser-Tests mit Playwright
```

Die Browser-Tests bauen die Seite selbst und starten einen lokalen Server. Mehr dazu in [CONTRIBUTING.md](CONTRIBUTING.md).

## Docker

Das Image enthält nur die neutrale Seite und läuft mit nginx ohne Root-Rechte auf Port 8080.

```bash
docker build -t htw-studienplaner .
docker run --rm -p 8080:8080 htw-studienplaner
```

Danach öffnest du <http://localhost:8080>. Den Zustand des Containers zeigt `http://localhost:8080/healthz` (Antwort: `ok`).

Das fertige Image veröffentlicht GitHub Actions nach jedem erfolgreichen Lauf auf `main` (dieselbe Seite geht dann auch an GitHub Pages):

```bash
docker pull ghcr.io/eljakj/htw-studienplaner:latest
```

Wie die Seite auf einem Server mit `docker compose` läuft, steht in [docs/deployment.md](docs/deployment.md).

## Datenschutz

- Dein Plan bleibt in deinem Browser (`localStorage`). Es gibt kein Konto und keinen Server-Speicher.
- Die Seite lädt nichts von anderen Servern und setzt keine Cookies. Eine Content Security Policy erlaubt nur das eigene Skript.
- Der mitgelieferte nginx-Container schreibt kein Zugriffsprotokoll und im Fehlerprotokoll nur schwere Fehler. Besucheradressen werden also nicht gespeichert.
- Betreibt jemand die Seite hinter einem Proxy oder Dienst (zum Beispiel Cloudflare), gelten dessen eigene Protokolle. Sie sind nicht Teil dieses Projekts.
- Persönliche Dateien wie `profile.json` und `studienverlauf-*.json` stehen in der `.gitignore` und gehören nie ins Repository.

## Architektur

Ein Python-Build bettet den Katalog (`src/catalog.py`) in eine HTML-Vorlage (`src/index.tpl.html`) ein und schreibt `dist/index.html`. Alles Weitere, also Zustand und Darstellung, passiert im Browser.

```
src/catalog.py  +  src/index.tpl.html
                 |
             build.py
                 |
         dist/index.html  -->  Docker-Image (nginx)  -->  GHCR  -->  docker compose
```

Ausführlich: [docs/architecture.md](docs/architecture.md) (Build, Speicher, Teststrategie, CI und Auslieferung).

## Status und Roadmap

Die Planung steht im [PRD](docs/PRD.md); Phasen und Meilensteine M0 bis M2.

- **M0 Grundlage (erledigt):** Repo-Gerüst, Katalog mit Tests, Build, Browser-Tests, CI, Docker-Image mit nginx, Veröffentlichung auf GHCR, Deployment mit `docker compose`.
- **M1 Eigener Start (erledigt):** neutraler Build für alle, Startauswahl, Studienbeginn bestimmt das aktuelle Semester, Beispiel als Sandbox, Export und Import als JSON-Datei.
- **M2 Sichern und Profile (erledigt):** lokale Profile, Name und Untertitel, Löschen mit Bestätigung und Rückgängig, Sicherungs-Erinnerung, Katalog-Updates beim Laden, öffentliche Demo über GitHub Pages.

Nicht geplant: Konto und Sync zwischen Geräten (ADR-0002) und der Nur-Lese-Link (PRD A11, nur eine Idee).

Offen:

- Für Quantencomputing, Spezielle Anwendungen der Informatik und Interdisziplinäres Projekt kennt das LSF noch keine B-Nummer; der Katalog führt sie unter eigenen Kürzeln (braucht Auskunft von Studienbüro oder SPO).
- Wann der alte Schlüssel `studienverlauf-ai-v1` gelöscht wird; das PRD sagt nur „eine Version lang“. Bis dahin bleibt er unverändert stehen.
- Ob die Seite öffentlich erreichbar sein soll und dann ein Impressum und ein Datenschutzhinweis nötig sind.

## Architekturentscheidungen

- [ADR-0001: Eine statische HTML-Datei, Vanilla JS, Katalog in Python](docs/adr/0001-single-static-file.md)
- [ADR-0002: Export und Import statt Konto oder Sync](docs/adr/0002-export-import-instead-of-sync.md)
- [ADR-0003: Content Security Policy mit Skript-Hash, beim Build erzeugt](docs/adr/0003-content-security-policy.md)
- [ADR-0004: Ein neutraler Build für alle, der eigene Plan lebt im Browser](docs/adr/0004-one-neutral-build.md)
- [ADR-0005: Mehrere lokale Profile in einem Speicherschlüssel](docs/adr/0005-local-profiles.md)

## Mitmachen

Kleine Schritte: ein Issue, ein Branch, ein Pull Request. Regeln und Befehle stehen in [CONTRIBUTING.md](CONTRIBUTING.md). Code, Commits, Issues und Pull Requests sind auf Englisch, die Oberfläche und dieses README auf Deutsch.

## Lizenz

[MIT](LICENSE)
