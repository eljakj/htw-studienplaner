# -*- coding: utf-8 -*-
"""Katalog Angewandte Informatik (B), HTW Berlin, Immatrikulation ab WS 2021.

Quellen: LSF WiSe 2026/27, Studienordnung (SPO) Angewandte Informatik (B).
Electives last checked against the LSF and the official overview: 2026-10-11.
Pro Semester im LSF neu abgleichen: lsf-Flag bei Wahlpflicht, AWE- und Sprachlisten.

Der Katalog ist neutral: jedes Modul startet als "geplant". Einen persoenlichen Stand
(Status, Notizen, gewaehlte Module) legt man als Profil darueber, siehe apply_profile().
"""
import json

CATS = {
  "kern":   {"label": "Kerninformatik",                          "color": "#76b900"},
  "math":   {"label": "Mathematische und technische Grundlagen", "color": "#ffff00"},
  "sonst":  {"label": "Sonstige fachübergreifende Kompetenzen",  "color": "#f4b183"},
  "wp":     {"label": "Spezieller Anwendungsbereich (Wahlpflicht)", "color": "#f46300"},
  "andere": {"label": "Andere Fachdisziplinen",                  "color": "#a6a6a6"},
  "fach":   {"label": "Fachpraktikum",                           "color": "#9a719d"},
  "ba":     {"label": "Bachelorarbeit inkl. Begleitseminar",     "color": "#8faadc"},
}

NEUTRAL_FIX = {"s": "plan", "n": "noch nicht angemeldet"}
NEUTRAL_FLEX = {"s": "plan", "n": "", "mod": None}
STATUS = {"ok", "run", "plan", "retake", "nospot"}  # bestanden, laeuft, geplant, Wiederholung, kein Platz


def fix(id, sem, name, lp, cat, ev=None, nv=None, c=""):
    """Pflichtmodul. ev = Empfohlene, nv = Notwendige Voraussetzung (Modul-IDs)."""
    d = {"id": id, "sem": sem, "t": "fix", "cat": cat, "lp": lp, "name": name, "def": dict(NEUTRAL_FIX)}
    if ev: d["ev"] = ev
    if nv: d["nv"] = nv
    if c: d["c"] = c
    return d


def flex(id, sem, t, cat, lp, label, pair=None):
    """Flexibler Platz (t = wp | awe | fs), das Modul waehlt man im Dropdown."""
    d = {"id": id, "sem": sem, "t": t, "cat": cat, "lp": lp, "label": label, "def": dict(NEUTRAL_FLEX)}
    if pair: d["pair"] = pair
    return d


# Reihenfolge = Reihenfolge in der Zeile (6 Spalten), Semester 6 oben
SLOTS = [
  fix("B62", 6, "Bachelorarbeit", 12, "ba", c="a3"),
  fix("B63", 6, "Bachelorseminar + Kolloquium", 3, "ba", c="a1"),
  fix("B61", 6, "Fachpraktikum", 15, "fach", c="a2"),

  fix("B51", 5, "Datenschutz & Datensicherheit", 5, "kern", ev=["B35"]),
  fix("B52", 5, "Computer- & Maschinenethik", 5, "andere", ev=["B32"]),
  fix("B53", 5, "Projektstudium", 5, "andere"),
  flex("WP3", 5, "wp", "wp", 5, "Wahlpflichtmodul 3"),
  flex("WP4", 5, "wp", "wp", 5, "Wahlpflichtmodul 4"),
  flex("WP5", 5, "wp", "wp", 5, "Wahlpflichtmodul 5"),

  fix("B41", 4, "Web Application Development", 5, "kern"),
  fix("B42", 4, "Software Engineering 2", 5, "kern", ev=["B32"]),
  fix("B43", 4, "Verteilte Systeme", 5, "kern"),
  flex("WP1", 4, "wp", "wp", 5, "Wahlpflichtmodul 1"),
  flex("WP2", 4, "wp", "wp", 5, "Wahlpflichtmodul 2"),
  fix("B46", 4, "Projektmanagement", 5, "andere", ev=["B32"]),

  fix("B31", 3, "Programmierung 3", 6, "kern"),
  fix("B32", 3, "Software Engineering 1", 5, "kern"),
  fix("B33", 3, "Algorithmen & Datenstrukturen", 5, "kern", ev=["B26"]),
  fix("B35", 3, "Mobile Betriebssysteme & Netzwerke", 5, "kern"),
  fix("B34", 3, "Einführung Data Science", 5, "math", ev=["B26"]),
  flex("B36", 3, "awe", "sonst", 2, "AWE 1", pair="awe"),
  flex("B37", 3, "awe", "sonst", 2, "AWE 2", pair="awe"),

  fix("B21", 2, "Programmierung 2", 6, "kern"),
  fix("B24", 2, "Datenbanken", 5, "kern"),
  fix("B22", 2, "Formale Sprachen", 5, "kern"),
  fix("B23", 2, "Betriebssysteme & Netzwerke", 5, "kern"),
  fix("B26", 2, "Mathematik 2", 5, "math", nv=["B16"]),
  flex("B25", 2, "fs", "sonst", 4, "Fremdsprache 2"),

  fix("B11", 1, "Programmierung 1", 6, "kern"),
  fix("B12", 1, "Technische & logische Grundlagen", 5, "kern"),
  fix("B13", 1, "Praktische Grundlagen", 5, "kern"),
  fix("B14", 1, "Wissenschaftliches Arbeiten", 5, "andere"),
  fix("B16", 1, "Mathematik 1", 5, "math"),
  flex("B15", 1, "fs", "sonst", 4, "Fremdsprache 1"),
]

# Wahlpflicht (SPO) – lsf=True: im LSF WiSe 2026/27 gelistet
# IDs without a B number (QC, SAI, IP): the LSF assigns none yet. Keep these IDs stable,
# saved profiles and exports store them as module IDs.
def wp(id, name, spec, ev, lsf, short=None):
    d = {"id": id, "name": name, "spec": spec, "ev": ev, "lsf": lsf}
    if short: d["short"] = short
    return d
FREI, SE, MS, DS = "Ohne Spezialisierung", "Software Engineering", "Mobile Systems", "Data Science"
WP = [
  wp("B100", "Freies Wahlpflichtmodul", FREI, [], False),
  wp("B101", "Ausgewählte Kapitel 1: Generative AI in Software Development", FREI, [], True, "GenAI in Software Development"),
  wp("B102", "Ausgewählte Kapitel 2: Agentische KI (Agentic AI)", FREI, [], True, "Agentische KI"),
  wp("SAI", "Spezielle Anwendungen der Informatik", FREI, [], False),
  wp("IP", "Interdisziplinäres Projekt", FREI, [], False),
  wp("B110", "Advanced Programming", SE, [], False),
  wp("B111", "Cloud Computing", SE, ["B43"], True),
  wp("B112", "Front-End Development", SE, ["B11", "B21", "B24", "B31"], True),
  wp("B113", "Softwarearchitekturen", SE, ["B11", "B21", "B31", "B32"], True),
  wp("B114", "Systemmodellierung", SE, ["B22", "B31", "B32"], False),
  wp("QC", "Quantencomputing Grundlagen", SE, [], False),
  wp("B210", "Decentralized Systems", MS, ["B23", "B35", "B211"], True),
  wp("B211", "Drahtlose Netzwerke", MS, ["B23"], True),
  wp("B212", "Internet of Things (IoT)", MS, [], True),
  wp("B213", "Semantic Search", MS, ["B24", "B31"], True),
  wp("B310", "Programmierkonzepte für Data Mining", DS, ["B11", "B21", "B31"], True),
  wp("B311", "Data Mining", DS, ["B11", "B21", "B24", "B31", "B310"], False),
  wp("B312", "Machine Learning 1", DS, ["B26", "B34"], True),
  wp("B313", "Machine Learning 2", DS, ["B312"], True),
]

# AWE (LSF Vorlesungsverzeichnis > AWE); bookable=False: im LSF ohne Belegung
AWE_RAW = """00310220|Schlüsselkompetenzen im interkulturellen Handlungsraum
00310223|Karrieremanagement für Frauen
00310690|Interdisziplinäre Teamarbeit im FormulaStudent Projekt - Konzeptphase
00310707|International Standardization
00310781|Wissenschaftliches Arbeiten mit LaTeX
00310798|Naturwissenschaftlich-technisches Projektlabor
00310855|Plastische 3 D - Übungen zum Verständnis von Körper und Raum
00310897|Buddyprogramm - Service Learning
00310956|Forschung und Entwicklung im Naturwissenschaftlich-technischen Projektlabor
00311114|Kreatives Zeichnen in der Natur / Creative Outdoor Drawing
00311420|Umweltphysik (SL)
00311539|Startschuss in den Job - Bewerbungen erfolgreich meistern!
00311680|Change-Management und Management komplexer Projekte
00311700|HTW hilft - Studierende für soziales Engagement
00311818|LaTeX für Fortgeschrittene
00311840|Mitarbeitergespräche (Feedback-, Kritik- und Abmahnungsgespräche)
00312147|Entscheidungskompetenz
00312230|Blue Engineering - Ingenieurinnen und Ingenieure mit sozialer und ökologischer Verantwortung
00312278|Orientierungswissen im Finanzbereich
00312663|Mentoring Studienstart am FB2|x
00312696|Rechtsfragen der Digitalisierung
00312753|Life-Hacking - Die Struktur des Erfolgs
00312775|Lichtsteuerung mit DMX
00312836|Digitalisierung und Prozessmanagement
00312837|Interkulturelle Kompetenz
00312946|Experimentelles Reisen
00312948|Hack the world a better place!
00312997|Social Impact of Digitalization
00313107|International Entrepreneurship
00313241|Unternehmensgründung
00313243|Authentische Kommunikation - Die Kunst der Personalkommunikation
00313245|Unternehmensgründung und -führung
00313435|Startup-Szene: Von der Idee zur Gründung
00313524|Futureskill Selbstkompetenz
00313748|Feministische Analysen von Design und Technik
00313785|Lebendiger Campus
00313905|Gesellschaftliche Privilegien - erkennen, verstehen, reflektieren
00313909|Lizenzkurs Amateurfunk für Einsteiger
00313912|Fernerkundungen und Geodatenauswertung
00313939|Agiles Coaching - Veränderungen erfolgreich begleiten
00313943|Authentisch und selbstbewusst ins Berufsleben
00313945|Konfliktmanagement
00313948|Künstliche Intelligenz und virtuelle Objekte
00313949|Agile Organisation - Komplexität erfolgreich begegnen
00313951|Selbstbewusst wissenschaftliche Texte verfassen
00313965|3D and 4D Printing with Sustainable Materials
00313967|Digital Architecture: Computational Tool for Sustainable Building Design
00314070|Brain Explain - Mental stark im Leben
00314081|Multimedia Learning Lab
00314109|Tech Justice
00314279|Kritisches Denken und KI in der Wissenschaft
00314288|AI Promptathon: Using Large Language Models - Way to Fun
00314292|Bildbearbeitung, Illustration und Layout mit Affinity - die moderne Alternative zu Adobe!
00314293|Digitale Bildung für Kinder gestalten
00314387|Kostümbild als erzählerisches Mittel im Film: Analyse, Konzeption und berufliche Praxis
00314408|Technologien und Gesellschaft. Kritische Theorien zur Digitalisierung des Lebens
00314410|Decoding Social Dynamics: Communication and Interaction in Organisations
00314411|Beyond Borders: Understanding and Experiencing Culture
00314446|Mein Ich in der Blackbox - Interdisziplinäre Perspektiven auf Macht, Selbstgestaltung und Verantwortung im digitalen Zeitalter
00314447|Grundlagen Fotografie: Kompetenzen visueller Gestaltung
00314519|Berufsbildung, Technik und Facharbeit
00314558|Greenwashing vs. Industrial Reality: A Boardroom Simulation
00314559|The end of cash? New payment systems and financial innovations
00314560|Kommunikation, Argumentation und überzeugende Präsentation im Berufsalltag
00314561|Transformationen in Organisationen gestalten: Strategie, Führung und Kommunikation
00314562|Klimakrise und Geschlecht: Politiken, Praktiken, Perspektiven
00314563|Von Tante Emma über Zalando zu Temu: Der digitale Wandel im Handel
00314574|Veranstaltungsplanung und -management: Praxisprojekt Computational Finance
0039037|Rhetorik
0039058|METROPOLIS - Städtebau und Architektur von der Antike bis zur Moderne am Beispiel Berlins
0039763|Wirtschaftlich-industrielle Entwicklung in China
0039952|Internationale Politik und Globalisierung
0310030|B27 P-AWE: Medienrecht"""
AWE = []
for line in AWE_RAW.splitlines():
    p = line.split("|")
    d = {"id": "A" + p[0], "no": p[0], "name": p[1]}
    if len(p) > 2: d["bookable"] = False
    AWE.append(d)

# Fremdsprachen (LSF: Fremdsprachen + Intensivkurse vorlesungsfreie Zeit); GER-Niveau im Namen
FS_RAW = [
 ("Englisch", "00201481", "English for Information Technology, M2Ts (GER B2.1)", "English for IT M2Ts (B2.1)"),
 ("Englisch", "00201483", "English for Information Technology, EnM3Ts (GER B2.2)", "English for IT EnM3Ts (B2.2)"),
 ("Englisch – Intensivkurse (vorlesungsfreie Zeit)", "00201473", "Business English, M2Ws (GER B2.1), Intensivkurs für Wiederholer", "Business English M2Ws (B2.1) Intensiv"),
 ("Englisch – Intensivkurse (vorlesungsfreie Zeit)", "00201474", "Business English, M3WS (GER B2.2), Intensivkurs für Wiederholer", "Business English M3Ws (B2.2) Intensiv"),
 ("Englisch – Intensivkurse (vorlesungsfreie Zeit)", "00201475", "Technical English, M2Ts (GER B2.1), Intensivkurs für Wiederholer", "Technical English M2Ts (B2.1) Intensiv"),
 ("Englisch – Intensivkurse (vorlesungsfreie Zeit)", "00201476", "Technical English, M3Ts (GER B2.2), Intensivkurs für Wiederholer", "Technical English M3Ts (B2.2) Intensiv"),
 ("Englisch – Intensivkurse (vorlesungsfreie Zeit)", "00201484", "English for Design, M2Gs (GER B2.1), Intensivkurs für Wiederholer", "English for Design M2Gs (B2.1) Intensiv"),
 ("Englisch – Intensivkurse (vorlesungsfreie Zeit)", "00201485", "English for Design, M3Gs (GER B2.2), Intensivkurs für Wiederholer", "English for Design M3Gs (B2.2) Intensiv"),
 ("Französisch", "00202001", "Französisch, Grundstufe 1, Allgemeinsprache (GER A1.2)", "Französisch Grundstufe 1 (A1.2)"),
 ("Französisch", "00202016", "Le français des affaires - introduction, M1Ws (GER B1.2)", "Français des affaires M1Ws (B1.2)"),
 ("Französisch", "00202040", "Le français des affaires - niveau intermédiaire 3, M3Ws (GER B2.2)", "Français des affaires M3Ws (B2.2)"),
 ("Spanisch", "00204001", "Spanisch, Grundstufe 1, Allgemeinsprache (GER A1.2)", "Spanisch Grundstufe 1 (A1.2)"),
 ("Spanisch", "00204084", "Español para los negocios - introducción, M1Ws (GER B1.2)", "Español negocios M1Ws (B1.2)"),
 ("Spanisch", "00204040", "Español para los negocios - nivel intermedio, M3Ws (GER B2.2)", "Español negocios M3Ws (B2.2)"),
 ("Russisch", "00206001", "Russisch, Grundstufe 1, Allgemeinsprache (GER A1.2)", "Russisch Grundstufe 1 (A1.2)"),
 ("Russisch", "00206016", "Russisch, Mittelstufe 1, Wirtschaft (GER B1.2)", "Russisch Mittelstufe 1 (B1.2)"),
 ("Russisch", "00206107", "Russisch, Mittelstufe 2, Wirtschaft (GER B2.1)", "Russisch Mittelstufe 2 (B2.1)"),
 ("Russisch", "00206040", "Russisch, Mittelstufe 3, Wirtschaft (GER B2.2)", "Russisch Mittelstufe 3 (B2.2)"),
 ("Italienisch", "00203001", "Italienisch, Grundstufe 1, Allgemeinsprache (GER A1)", "Italienisch Grundstufe 1 (A1)"),
 ("Japanisch", "00207008", "Japanisch, Grundstufe 1, Allgemeinsprache (GER A1.2)", "Japanisch Grundstufe 1 (A1.2)"),
 ("Deutsch", "00205040", "Deutsch, Mittelstufe 3, Wirtschaft (GER B2.2)", "Deutsch Mittelstufe 3 Wirtschaft (B2.2)"),
 ("Deutsch", "00205043", "Deutsch, Mittelstufe 3, Technik (GER B2.2)", "Deutsch Mittelstufe 3 Technik (B2.2)"),
]
FS = [{"id": "F" + no, "no": no, "grp": g, "name": n, "short": s} for g, no, n, s in FS_RAW]

# No currentSem here: the neutral build holds no personal values. The page falls back to semester 1
# until the study start decides the current semester (PRD A3).
# "catalog" names the source the catalog was checked against; exports carry it (PRD A7).
META = {"subtitle": "Angewandte Informatik (B), HTW Berlin", "catalog": "LSF WiSe 2026/27"}
CATALOG = {"cats": CATS, "slots": SLOTS, "wp": WP, "awe": AWE, "fs": FS, "meta": META}

WP_IDS = {w["id"] for w in WP}
FS_IDS = {f["id"] for f in FS}
SLOT_IDS = [s["id"] for s in SLOTS]


def validate():
    """Plausibilitaetspruefung des Katalogs, wirft AssertionError."""
    ids = SLOT_IDS
    assert len(ids) == len(set(ids)), "doppelte Slot-IDs"
    assert sum(s["lp"] for s in SLOTS) == 180, sum(s["lp"] for s in SLOTS)
    for sem in range(1, 7):
        assert sum(s["lp"] for s in SLOTS if s["sem"] == sem) == 30, sem
    for s in SLOTS:
        assert s["cat"] in CATS, s["id"]
        for k in ("ev", "nv"):
            for m in s.get(k, []):
                assert m in ids or m in WP_IDS, (s["id"], m)
    for w in WP:
        for m in w["ev"]:
            assert m in ids or m in WP_IDS, (w["id"], m)
    assert len({a["id"] for a in AWE}) == len(AWE)
    assert len(FS_IDS) == len(FS)
    assert isinstance(META.get("catalog"), str) and META["catalog"].strip(), "meta.catalog (catalog version)"


def apply_profile(profile):
    """Legt einen persoenlichen Stand ueber die neutralen Defaults.

    profile = {"meta": {"subtitle": str, "currentSem": 1..6},
               "slots": {slotId: {"s": status, "n": notiz, "mod": modulId (nur flexible Plaetze)}}}
    Gibt einen neuen Katalog zurueck, der Basis-Katalog bleibt unveraendert.
    """
    import copy
    cat = copy.deepcopy(CATALOG)
    by_id = {s["id"]: s for s in cat["slots"]}
    meta = profile.get("meta", {})
    if "subtitle" in meta: cat["meta"]["subtitle"] = str(meta["subtitle"])
    if "currentSem" in meta:
        assert 1 <= int(meta["currentSem"]) <= 6, "currentSem"
        cat["meta"]["currentSem"] = int(meta["currentSem"])
    for sid, st in profile.get("slots", {}).items():
        assert sid in by_id, "unbekannter Slot im Profil: " + sid
        slot = by_id[sid]
        assert st.get("s") in STATUS, (sid, st.get("s"))
        d = {"s": st["s"], "n": str(st.get("n", ""))}
        if slot["t"] != "fix":
            mod = st.get("mod")
            pool = {"wp": WP_IDS, "fs": FS_IDS, "awe": {a["id"] for a in AWE}}[slot["t"]]
            assert mod is None or mod in pool, (sid, mod)
            d["mod"] = mod
        slot["def"] = d
    return cat


def example_state(profile):
    """Start state of the example sandbox ("Beispiel ansehen") from a demo profile.

    The profile has the format of apply_profile() and must say in meta.currentSem (1..6) in which semester
    the example person is. Gives {"currentSem": n, "m": {slotId: {"s", "n", "mod"}}, "names": {}}.
    Raises AssertionError for anything that does not fit the catalog."""
    meta = profile.get("meta", {})
    assert "currentSem" in meta, "the demo profile needs meta.currentSem"
    cat = apply_profile(profile)
    by_id = {s["id"]: s for s in cat["slots"]}
    m = {}
    for sid in profile.get("slots", {}):
        d = dict(by_id[sid]["def"])
        d.setdefault("mod", None)
        m[sid] = d
    return {"currentSem": int(meta["currentSem"]), "m": m, "names": {}}


def to_json(catalog=None):
    return json.dumps(catalog or CATALOG, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


validate()

if __name__ == "__main__":
    print("ok", len(SLOTS), "Slots,", len(WP), "Wahlpflicht,", len(AWE), "AWE,", len(FS), "Sprachkurse, 180 LP")
