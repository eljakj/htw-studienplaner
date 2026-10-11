# PRD: Studienverlauf AI v2 – Eigener Plan pro Nutzer

Stand: 11.10.2026

> Dieses Dokument beschreibt die Planung von Version 2. Den aktuellen Stand der Umsetzung zeigt das [README](../README.md).

## Kurzfassung und Empfehlung

v2 bleibt eine statische Seite ohne Konto und ohne Server-Speicher: Jeder Browser hält seinen eigenen Plan, neue Besucher starten leer, und das Beispielprofil wird zu einer Sandbox, die nie gespeichert wird. Für mehrere Personen mit getrennten Browserprofilen reicht das bereits, denn getrennte Browserprofile haben getrennten Speicher und können sich nicht mischen.

Was sich gegenüber heute ändert:

- **Ein Build für alle.** Der Server liefert nur noch die neutrale Seite; der eigene Stand kommt per Datei-Import in den Browser statt per Rebuild.
- **Erstbesuch mit Auswahl.** „Eigenen Plan starten“, „Beispiel ansehen“ oder „Plan importieren“; das aktuelle Semester ergibt sich aus dem Studienbeginn.
- **Sichern und Umziehen.** Export und Import als JSON-Datei, weil Browserspeicher verloren gehen kann.
- **Kein Sync, kein Konto**: Export und Import als Datei sind entschieden (10.10.2026, siehe [ADR-0002](adr/0002-export-import-instead-of-sync.md)).

## Problem und Ausgangslage

Heute legt der Build einen Stand fest in die Seite, und jeder Besucher startet mit genau diesem Stand: entweder dem Beispielprofil oder einem persönlichen Profil.

- Ein neuer Student sieht zuerst fremde Daten und muss sie per „Semesterstart“ wegklicken.
- Ein persönlicher Stand braucht einen eigenen Build auf dem Server und ist dann für jeden mit dem Link sichtbar.
- Das aktuelle Semester (`currentSem`) ist beim Build fest eingetragen und passt nicht für andere Studierende.
- Ein Plan lässt sich weder sichern noch auf ein anderes Gerät übertragen. Gelöschte Browserdaten bedeuten Datenverlust.

## Ziele, Nicht-Ziele, Erfolgskriterien

Das Ziel: Wer die Seite öffnet, hat in unter einer Minute einen eigenen, leeren Plan im richtigen Semester, und niemand sieht die Daten eines anderen.

**Ziele**

1. Neuer Besucher kommt mit höchstens 3 Klicks zu seinem eigenen Plan.
2. Persönliche Daten bleiben im Browser; der Server speichert nichts Persönliches.
3. Pläne verschiedener Personen mischen sich nie.
4. Ein Plan lässt sich sichern und auf ein anderes Gerät übertragen.
5. Ein einziger Build für alle, kein persönlicher Build mehr.

**Nicht-Ziele in v2**

- Konten, Login, Server-Sync
- Weitere Studiengänge
- Automatische Übernahme aus dem LSF
- Analytics oder Tracking jeder Art

**Erfolgskriterien**

| Kriterium | Messung |
| --- | --- |
| Erstbesuch bis eigener Plan ≤ 3 Klicks | E2E-Test spielt den Weg durch |
| Keine Personendaten im Build | Test durchsucht `dist/index.html` nach Profilwerten |
| Kein Mischen zwischen Plänen | E2E-Test: zwei Browser-Kontexte, getrennte Ergebnisse |
| Export → Import ergibt identische Ansicht | E2E-Test vergleicht LP und Status aller 34 Plätze |

## Nutzer und Szenarien

Fünf Situationen decken die Nutzung ab; jede bekommt einen klaren Weg, und keiner davon braucht ein Konto.

| Wer | Situation | Was passiert in v2 |
| --- | --- | --- |
| Neuer Student | Öffnet die Seite zum ersten Mal | Auswahl beim Start, Studienbeginn angeben, leerer Plan im richtigen Semester |
| Besucher, der sich das Projekt ansieht | Will nur sehen, was das Projekt kann | „Beispiel ansehen“: fiktive Daten, nichts wird gespeichert |
| Hauptnutzer (Maintainer) | Pflegt den eigenen Plan jedes Semester | Einmal die eigene Datei importieren, danach täglich im Browser; ab und zu exportieren |
| Zweite Person mit eigenem Browserprofil | Will einen eigenen Plan | Eigener Speicher, startet leer; technisch getrennt vom Plan anderer |
| Nutzer auf einem zweiten Gerät | Laptop zu Hause, Handy unterwegs | Export auf Gerät A, Import auf Gerät B; kein Sync, bewusst entschieden |

Nutzen zwei Personen **dasselbe** Browserprofil, teilen sie sich den Speicher. Dafür gibt es in Phase 2 lokale Profile mit Umschalter (A8).

## Anforderungen

Phase 1 braucht sieben Anforderungen (P0); danach ersetzt der Import den persönlichen Build vollständig.

| ID | Anforderung | Priorität | Akzeptanzkriterium |
| --- | --- | --- | --- |
| A1 | Neutraler Build: Server liefert eine Seite ohne persönliche Daten | P0 · Phase 1 | `dist/index.html` enthält keinen Profilwert; `--demo` und `--profile` gibt es nicht mehr ([ADR-0004](adr/0004-one-neutral-build.md)) |
| A2 | Startauswahl beim Erstbesuch: „Eigenen Plan starten“, „Beispiel ansehen“, „Plan importieren“ | P0 · Phase 1 | Erscheint nur ohne gespeicherten Plan; nach einer Wahl nicht wieder |
| A3 | Studienbeginn (SoSe/WiSe + Jahr) bestimmt das aktuelle Fachsemester; später änderbar | P0 · Phase 1 | Beginn SoSe 2025, Datum 10.10.2026 → 4. Semester ist als „jetzt“ markiert |
| A4 | Beispiel als Sandbox mit Banner „Beispiel – wird nicht gespeichert“ und Button „Eigenen Plan starten“ | P0 · Phase 1 | Änderungen im Beispiel und Reload lassen den eigenen Plan unverändert |
| A5 | Automatische, stille Speicherung im Browser (wie heute) | P0 · Phase 1 | Jede Änderung überlebt einen Reload |
| A6 | Hinweis, wenn der Browser nicht speichern kann (privates Fenster, blockierter Speicher) | P0 · Phase 1 | Banner erscheint sofort beim Laden, nicht erst bei der ersten Änderung |
| A7 | Export als JSON-Datei und Import mit Prüfung und Vorschau („47 LP bestanden – übernehmen?“) | P0 · Phase 1 | Export → Import in anderem Browser ergibt identische Ansicht; ungültige Datei ändert nichts und nennt den Fehler |
| A8 | Lokale Profile: mehrere Pläne in einem Browser, Umschalter mit Namen | P1 · Phase 2 · umgesetzt | Änderung in Profil A lässt Profil B unverändert |
| A9 | Plan oder Profil löschen, mit Bestätigung direkt in der Seite | P1 · Phase 2 · umgesetzt | Ohne Bestätigung wird nichts gelöscht; Rückgängig in derselben Sitzung möglich |
| A10 | Sicherungs-Erinnerung nach 30 Tagen ohne Export | P2 · Phase 2 · umgesetzt | Hinweis verschwindet nach einem Export |
| A11 | Nur-Lese-Link: Plan im Link kodiert, Empfänger sieht ihn ohne zu speichern | P2 · nicht geplant (Idee) | Geöffneter Link ändert den Plan des Empfängers nicht |
| A12 | Eigener Name und Untertitel im Kopf der Seite | P2 · Phase 2 · umgesetzt | Nach Reload und Export/Import erhalten |

## Datenmodell, Speicherung, Migration

Ein neuer Speicherschlüssel `studienverlauf-ai-v2` hält alle Profile eines Browsers; der Katalog bleibt wie heute fest in der Seite, gespeichert werden nur Abweichungen.

```json
{
  "v": 2,
  "active": "p1",
  "profiles": {
    "p1": {
      "name": "Mein Plan",
      "start": { "term": "SoSe", "year": 2025 },
      "rev": 1760108400000,
      "m": { "B31": { "s": "ok", "n": "" } },
      "names": {},
      "subtitle": "Mein Untertitel",
      "created": 1760108400000,
      "lastExport": 1760194800000
    }
  }
}
```

`subtitle`, `created` und `lastExport` stehen nur im Speicher, wenn sie gesetzt sind. Pro Browser sind höchstens 20 Pläne möglich; Name bis 40 Zeichen, Untertitel bis 80 Zeichen.

- **Export** = genau ein Profil plus `catalog` (Katalogstand, z. B. „LSF WiSe 2026/27“) und `exportedAt`. Dateiname `studienverlauf-<name>-<datum>.json`. Die Datei trägt außerdem `app` (`htw-studienplaner`) und `v` (2), damit der Import eigene Dateien erkennt; `id` und `rev` des Profils werden nicht exportiert. Im Beispielplan (Sandbox) ist der Export ausgeschaltet (entschieden am 11.10.2026).
- **Import** prüft mit derselben Logik wie das Laden heute (`sane()`): unbekannte Plätze, Status und Module werden verworfen und in der Vorschau genannt.
- **Migration:** Gibt es nur den alten Schlüssel `studienverlauf-ai-v1`, wird er beim ersten Laden zu Profil „Mein Plan“. Der alte Schlüssel bleibt eine Version lang als Rückfallebene stehen.
- **Mehrere Tabs:** Die letzte Änderung gewinnt; andere offene Tabs laden über das `storage`-Ereignis nach.
- **Beispiel/Demo:** läuft nur im Arbeitsspeicher und schreibt nie in `localStorage`. Die öffentliche Demo auf GitHub Pages ist dieselbe neutrale Seite wie die produktive.
- **Kein `profile.json` beim Build:** `--demo` und `--profile` wurden entfernt. Der eigene Stand kommt über Start­auswahl oder Import in den Browser (A2, A7).
- **Profile (A8):** mehrere Pläne im selben Schlüssel, jeder Tab hat seinen eigenen aktiven Plan, jede Änderung wird sofort gespeichert ([ADR-0005](adr/0005-local-profiles.md)).
- **Löschen (A9):** Bestätigung in der Seite, danach „Rückgängig“ bis zum Schließen der Seite. Wird der letzte Plan gelöscht, erscheint wieder die Startauswahl; der alte v1-Schlüssel kommt nicht zurück.
- **Sicherungs-Erinnerung (A10):** 30 Tage nach dem letzten Export, oder nach `created`, wenn nie exportiert wurde. Nicht bei leerem Plan, nicht im Beispiel. „Später“ gilt nur für diesen Besuch.
- **Name und Untertitel (A12):** pro Plan, im Export enthalten, nur als Text gesetzt.

## Datenschutz und Sicherheit

Die Seite verarbeitet keine persönlichen Daten auf dem Server; der Plan verlässt den Browser nur als Datei, die der Nutzer selbst exportiert.

- Keine Cookies, kein Tracking, keine Anfragen an fremde Server (keine externen Schriften oder Skripte).
- Der Build enthält nur Katalog und fiktive Demo-Daten (A1); ein Test sichert das ab.
- nginx schreibt kein Zugriffsprotokoll und im Fehlerprotokoll nur schwere Fehler, damit keine IP-Adressen gespeichert werden (Entscheidung der Maintainer).
- Importierte Dateien sind fremde Eingaben: Werte werden nur als Text gesetzt, nie als HTML; Notizen bleiben auf 28 Zeichen begrenzt.
- Exportdateien enthalten den Studienstand der Person. Wo sie liegen, liegt in der Hand der Person.

## Randfälle

Der größte Risikofall ist Datenverlust durch gelöschte Browserdaten; dagegen helfen nur Export (A7) und die Erinnerung (A10).

| Situation | Verhalten |
| --- | --- |
| Privates Fenster oder Speicher blockiert | Seite funktioniert, Banner sagt „wird nicht gespeichert“ (A6) |
| Browserdaten gelöscht | Plan ist weg; letzter Export stellt ihn wieder her |
| Zwei Tabs offen | Letzte Änderung gewinnt, der andere Tab lädt nach |
| Neuer Katalog zum Semesterwechsel | Entfernte Module oder Plätze werden verworfen, einmal angezeigt („Der Katalog hat sich geändert …“) und der bereinigte Plan sofort gespeichert; Status und Notizen bleiben |
| Import einer Datei aus anderer Version | v1-Dateien (alte Seite, ohne `app` und `v`) werden migriert, unbekannte Versionen und fremde Dateien abgelehnt |
| Import: ungültige Datei oder größer als 1 MB | Nichts ändert sich, die Seite nennt den Grund |
| Import in einen nicht leeren Plan | Die Vorschau nennt die LP des aktuellen Plans, „Übernehmen“ ersetzt ihn ganz; kein Rückgängig (entschieden am 11.10.2026) |
| Zwei Personen, ein Browserprofil | Je ein lokales Profil (A8); jeder Tab kann einen anderen Plan offen haben |
| Plan löschen | Erst nach Bestätigung in der Seite; „Rückgängig“ bis zum Schließen der Seite (A9) |
| Letzten Plan gelöscht | Startauswahl erscheint wieder, der alte v1-Stand wird nicht neu übernommen |
| 20 Pläne erreicht | „Neuer Plan“ ist ausgeschaltet, ebenso „Als neuen Plan hinzufügen“ beim Import |
| Seit 30 Tagen nicht gesichert | Hinweis mit „Jetzt exportieren“ und „Später“ (A10); ein Export blendet ihn aus |
| Plan ohne Datum (älterer Stand) | Kein Hinweis, bis die erste Änderung das Datum `created` setzt |
| Studienbeginn liegt mehr als 6 Semester zurück | „jetzt“ bleibt beim 6. Semester, Hinweis „über Regelstudienzeit“ |
| Studienbeginn in der Zukunft | Kein Semester ist „jetzt“, Hinweis „Studium beginnt im …“ |
| Kein Studienbeginn gewählt | Kein Semester ist „jetzt“, Hinweis „Bitte wählen“ |

Semestergrenzen (A3): Laut Akademischem Kalender der HTW läuft das Sommersemester vom 01.04. bis 30.09. und das Wintersemester vom 01.10. bis 31.03. (geprüft an den Kalendern SoSe 2025, SoSe 2026 und WiSe 2026/27). „Jetzt“ richtet sich nach diesem Semesterzeitraum, nicht nach dem Beginn der Lehrveranstaltungen. Ab dem 7. Semester gilt „über Regelstudienzeit“.

## Meilensteine und Roadmap

Phase 1 ist der Kern: Danach läuft die Seite mit einem Build für alle, und der eigene Stand wird einmal in den Browser importiert. Phase 2 ist umgesetzt (11.10.2026).

**Roadmap (3 Phasen, 2 Gates)**

| Phase | Inhalt | Ziel |
| --- | --- | --- |
| Phase 1 · Eigener Start | A1 neutraler Build, A2 Startauswahl, A3 Studienbeginn, A4 Beispiel-Sandbox, A5–A6 Speichern und Hinweis, A7 Export und Import | Ein Build für alle |
| Gate 1 | Alle E2E-Tests grün, kein Personendatum im Build | bestanden (11.10.2026) |
| Phase 2 · Sichern und Profile | A8 lokale Profile, A9 Löschen mit Bestätigung, A10 Sicherungs-Erinnerung, A12 Name im Seitenkopf, Katalog-Update beim Laden, GitHub Pages | Profile pro Person · umgesetzt |
| Gate 2 | Nur wenn Export/Import im Alltag nicht reicht | bewusst geöffnet (11.10.2026): Phase 2 wird umgesetzt, ohne Alltagserfahrung abzuwarten |
| Phase 3 · nicht geplant | A11 Nur-Lese-Link (Idee), Konto und Sync bewusst verworfen | Entscheidung: Export/Import |

Phase 3 ist gestrichelt: Sync ist bewusst nicht geplant, weil Export und Import reichen; die Begründung steht in [ADR-0002](adr/0002-export-import-instead-of-sync.md).

## Offene Fragen

- [x] Entschieden am 11.10.2026: „Beispiel ansehen“ bleibt auch auf der produktiven Seite. Das Beispiel steckt im neutralen Build (erfundene Daten), Produktion und GitHub Pages zeigen dieselbe Seite (A4).
- [x] Entschieden am 11.10.2026: Lokale Profile (A8) kommen in Phase 2 und sind umgesetzt (ADR-0005).
- [ ] Wann wird der alte Schlüssel `studienverlauf-ai-v1` gelöscht? Das PRD sagt nur „eine Version lang“ (Migration). Bis das entschieden ist, bleibt er stehen und wird nie verändert.
- [ ] Für Quantencomputing, Spezielle Anwendungen der Informatik und Interdisziplinäres Projekt kennt das LSF noch keine B-Nummer (braucht Auskunft von Studienbüro oder SPO). Der Katalog führt sie unter eigenen Kürzeln, bis Studienbüro oder SPO Klarheit schaffen.
- [ ] Wird die produktive Seite öffentlich erreichbar? Dann prüfen, ob ein Impressum und ein kurzer Datenschutzhinweis nötig sind.
- [x] Entschieden am 10.10.2026: kein Sync zwischen Geräten, Export und Import reichen.
