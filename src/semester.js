/* Semester arithmetic for the study plan. Pure functions: no DOM, no clock.
   The date is always passed in, so the result only depends on the arguments.

   Terms follow the semester periods of the HTW academic calendar:
   Sommersemester (SoSe) 1 April - 30 September, Wintersemester (WiSe) 1 October - 31 March.
   A WiSe is named after the year it starts in: WiSe 2025 = WiSe 2025/26. */

var REGULAR_SEMESTERS = 6;

function termIndex(term, year){ return 2 * year + (term === 'WiSe' ? 1 : 0); }

// The term that a date (a Date object, local time) falls into: {term, year}
function termOfDate(date){
  var month = date.getMonth(), year = date.getFullYear();   // month: 0 = January
  if (month >= 3 && month <= 8) return {term: 'SoSe', year: year};
  return {term: 'WiSe', year: month >= 9 ? year : year - 1};
}

function termLabel(t){
  return t.term === 'WiSe' ? 'WiSe ' + t.year + '/' + String(t.year + 1).slice(-2) : 'SoSe ' + t.year;
}

/* Which semester of the plan is "now"?
   start: {term: 'SoSe' | 'WiSe', year: 4-digit number} or null
   today: a Date
   Result: {state, sem, label}
     'none'    no start given            sem null
     'future'  start is still ahead      sem null, label = the start term
     'running' 1st to 6th semester       sem 1..6
     'over'    7th semester or later     sem 6 (stays at the last semester of the plan) */
function currentSemester(start, today){
  if (!start) return {state: 'none', sem: null, label: ''};
  var now = termOfDate(today);
  var diff = termIndex(now.term, now.year) - termIndex(start.term, start.year);
  if (diff < 0) return {state: 'future', sem: null, label: termLabel(start)};
  if (diff >= REGULAR_SEMESTERS) return {state: 'over', sem: REGULAR_SEMESTERS, label: ''};
  return {state: 'running', sem: diff + 1, label: ''};
}

/* The start term that makes `sem` (1..6) the running semester on `today`.
   Inverse of currentSemester(): currentSemester(startForSemester(n, d), d).sem === n.
   Used by the example plan, which describes "the 4th semester" and not a fixed date. */
function startForSemester(sem, today){
  var now = termOfDate(today);
  var idx = termIndex(now.term, now.year) - (sem - 1);
  return {term: idx % 2 === 1 ? 'WiSe' : 'SoSe', year: Math.floor(idx / 2)};
}
