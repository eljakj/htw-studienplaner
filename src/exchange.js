/* Export and import of a plan as a file (PRD A7). Pure functions: no DOM, no clock, no storage.
   The date is always passed in, so the result only depends on the arguments.
   parseImport() only checks the shape of a file. The content (slots, statuses, modules) is checked
   by the page with the same sane() that checks the stored plan. */

var EXPORT_APP = 'htw-studienplaner';
var EXPORT_VERSION = 2;           // same number as the storage schema (v2)
var EXPORT_NAME_MAX = 40;

function pad2(n){ return (n < 10 ? '0' : '') + n; }

// Local calendar date of `date` as YYYY-MM-DD
function exportDate(date){
  return date.getFullYear() + '-' + pad2(date.getMonth() + 1) + '-' + pad2(date.getDate());
}

/* File name: studienverlauf-<name>-<date>.json
   The name is made safe for every file system: umlauts become ae/oe/ue/ss, other accents are dropped,
   everything but letters and digits becomes "-", at most 40 characters, "plan" if nothing is left. */
function exportFileName(name, date){
  var s = String(name === undefined || name === null ? '' : name)
    .replace(/ä/g, 'ae').replace(/ö/g, 'oe').replace(/ü/g, 'ue').replace(/ß/g, 'ss')
    .replace(/Ä/g, 'Ae').replace(/Ö/g, 'Oe').replace(/Ü/g, 'Ue')
    .normalize('NFD').replace(/[̀-ͯ]/g, '')
    .toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+/, '')
    .slice(0, EXPORT_NAME_MAX).replace(/-+$/, '');
  return 'studienverlauf-' + (s || 'plan') + '-' + exportDate(date) + '.json';
}

/* The content of an export file: exactly one profile.
   profile: {name, start, subtitle}   state: {m, names}   catalogLabel: e.g. "LSF WiSe 2026/27"   now: a Date
   The profile's local id and revision are not exported; the import gives the plan new ones.
   The copy is made through JSON, so the file never shares objects with the running page. */
function buildExport(profile, state, catalogLabel, now){
  var out = {
    app: EXPORT_APP,
    v: EXPORT_VERSION,
    exportedAt: now.toISOString(),
    catalog: catalogLabel,
    profile: {name: profile.name, start: profile.start, m: state.m, names: state.names}
  };
  if (profile.subtitle) out.profile.subtitle = profile.subtitle;   // only a custom subtitle (PRD A12)
  return JSON.parse(JSON.stringify(out));
}

/* ---------- backup reminder (PRD A10) ---------- */

var BACKUP_DAYS = 30;

/* Is a backup due? The clock starts at the last export, or at the creation of the plan if it was never exported.
   lastExport, created: milliseconds since 1970, 0 or missing = unknown (then nothing is due)   now: a Date */
function backupDue(lastExport, created, now, days){
  var since = lastExport || created;
  if (!since) return false;
  return now.getTime() - since >= (days === undefined ? BACKUP_DAYS : days) * 86400000;
}

/* ---------- import ---------- */

var IMPORT_MAX_BYTES = 1024 * 1024;   // a full plan is far below 100 KB
var IMPORT_TOO_LARGE = 'Die Datei ist größer als 1 MB.';

function importTooLarge(size){ return size > IMPORT_MAX_BYTES; }

function isPlainObject(x){ return x !== null && typeof x === 'object' && !Array.isArray(x); }
function ownProp(o, k){ return Object.prototype.hasOwnProperty.call(o, k); }
function str(x){ return typeof x === 'string' ? x : ''; }

function importError(code, error){ return {ok: false, code: code, error: error}; }

/* Checks the shape of an import file; the text is the content of the file.
   Result: {ok: true, kind: 'v2' | 'v1', name, subtitle, start, m, names, catalog, exportedAt}
        or {ok: false, code: 'json' | 'shape' | 'app' | 'version', error: <German text>}
   Two kinds of file are accepted:
   - v2: what exportPlan() writes ({app, v: 2, profile: {...}})
   - v1: the old stored plan without app and v ({rev, m, names}); it has no name and no study start
   Everything else is rejected with a named reason. Values are returned as they are in the file
   (m, names and start are not checked here); a leading byte order mark is ignored. */
function parseImport(text){
  if (typeof text !== 'string') return importError('json', 'Das ist keine gültige JSON-Datei.');
  if (text.charCodeAt(0) === 0xFEFF) text = text.slice(1);
  var data;
  try { data = JSON.parse(text); }
  catch (e){ return importError('json', 'Das ist keine gültige JSON-Datei.'); }
  var noPlan = importError('shape', 'Die Datei hat nicht die erwartete Form: Es wurde kein Plan gefunden.');
  if (!isPlainObject(data)) return noPlan;

  if (ownProp(data, 'app') || ownProp(data, 'v')){
    if (data.app !== EXPORT_APP) return importError('app', 'Die Datei stammt nicht von dieser Seite.');
    if (data.v !== EXPORT_VERSION){
      var shown = (typeof data.v === 'number' || typeof data.v === 'string') ? String(data.v).slice(0, 20) : '?';
      return importError('version', 'Unbekannte Version (' + shown + '). Diese Seite kennt nur Version ' + EXPORT_VERSION + '.');
    }
    var p = data.profile;
    if (!isPlainObject(p) || !isPlainObject(p.m)) return noPlan;
    return {ok: true, kind: 'v2', name: str(p.name), subtitle: str(p.subtitle), start: p.start === undefined ? null : p.start,
            m: p.m, names: isPlainObject(p.names) ? p.names : {},
            catalog: str(data.catalog), exportedAt: str(data.exportedAt)};
  }
  if (!isPlainObject(data.m)) return noPlan;
  return {ok: true, kind: 'v1', name: '', subtitle: '', start: null, m: data.m,
          names: isPlainObject(data.names) ? data.names : {}, catalog: '', exportedAt: ''};
}
