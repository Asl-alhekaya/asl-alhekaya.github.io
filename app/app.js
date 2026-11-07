'use strict';
// «الاستوديو»: the owner's Mini App (2026-11-07). One read («studio») feeds four tabs: the episode, the ideas, the numbers
// and the bank. The Apps Script endpoint answers only to a valid Telegram signature (initData). Everything is drawn with
// textContent: no data is ever put in as HTML. The publish words are never a button here; they stay in the chat.
var ENDPOINT = 'https://script.google.com/macros/s/AKfycbxcSL9ORmrW9xwwMJo5xO6_0vxy50Rz9HURme91nAqNvxeYshOzQz5Mhv5kP1Tfo2jP/exec';
var tg = window.Telegram && window.Telegram.WebApp;
if (tg) {
  try { tg.ready(); tg.expand(); } catch (e) { /* outside Telegram */ }
  try { if (tg.setHeaderColor) tg.setHeaderColor('#0B1416'); } catch (e) { /* older client */ }
  try { if (tg.setBackgroundColor) tg.setBackgroundColor('#0B1416'); } catch (e) { /* older client */ }
}

var view = document.getElementById('view');
var toastEl = document.getElementById('toast');
var stampEl = document.getElementById('stamp');
var refreshBtn = document.getElementById('refresh');
var TABS = ['job', 'ideas', 'stats', 'bank'];
var state = { tab: 'job', data: null, loading: false };
var toastTimer = null;

// ---------- small helpers

function el(tag, cls, text) {
  var e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined && text !== null) e.textContent = String(text);
  return e;
}
function add(parent) {
  for (var i = 1; i < arguments.length; i++) if (arguments[i]) parent.appendChild(arguments[i]);
  return parent;
}
function btn(cls, text, onTap) {
  var b = el('button', 'btn ' + (cls || ''), text);
  b.type = 'button';
  b.onclick = function () { tap(); onTap(b); };
  return b;
}
function num(n) { return Number(n || 0).toLocaleString('en-US'); }
function usd(n) {
  return '$' + Number(n || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
// Arabic words + a dollar amount: the amount goes in an isolated <bdi> so the $ stays on the left of the number.
function withUsd(tag, cls, words, n, after) {
  var e = el(tag, cls, words);
  var b = el('bdi', '', usd(n));
  b.dir = 'ltr';
  e.appendChild(b);
  if (after) e.appendChild(document.createTextNode(after));
  return e;
}
function isNum(n) { return n !== null && n !== undefined && n !== '' && !isNaN(Number(n)); }
function pad(n) { return (n < 10 ? '0' : '') + n; }
// The bot sends job.label already escaped for Telegram HTML; turn the entities back into plain characters for textContent.
function unescapeHtml(s) {
  return String(s || '').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#39;/g, "'")
    .replace(/&amp;/g, '&');
}
function tap() {
  try { if (tg && tg.HapticFeedback) tg.HapticFeedback.impactOccurred('light'); } catch (e) { /* no haptics */ }
}
function toast(msg, bad) {
  toastEl.textContent = msg;
  toastEl.className = 'show' + (bad ? ' bad' : '');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(function () { toastEl.className = ''; }, 2600);
}
function clear() { while (view.firstChild) view.removeChild(view.firstChild); }
function saveTab(t) { try { sessionStorage.setItem('studio-tab', t); } catch (e) { /* storage blocked */ } }
function readTab() {
  try { var t = sessionStorage.getItem('studio-tab'); return TABS.indexOf(t) >= 0 ? t : 'job'; } catch (e) { return 'job'; }
}

// Confirm with Telegram's own popup when the client has it, otherwise with the in-page sheet (never window.confirm).
function confirmThen(text, fn) {
  var supported = tg && tg.showConfirm && (!tg.isVersionAtLeast || tg.isVersionAtLeast('6.2'));
  if (supported) {
    try { tg.showConfirm(text, function (yes) { if (yes) fn(); }); return; } catch (e) { /* fall back to the sheet */ }
  }
  var sheet = document.getElementById('sheet'), yes = document.getElementById('sheet-yes'), no = document.getElementById('sheet-no');
  var opener = document.activeElement;
  document.getElementById('sheet-text').textContent = text;
  sheet.hidden = false;
  var close = function () { sheet.hidden = true; yes.onclick = no.onclick = sheet.onclick = null; if (opener && opener.focus) opener.focus(); };
  yes.onclick = function () { tap(); close(); fn(); };
  no.onclick = function () { tap(); close(); };
  sheet.onclick = function (ev) { if (ev.target === sheet) close(); };
  yes.focus();
}

// ---------- server

function api(action, extra) {
  var body = Object.assign({ action: action, initData: tg ? tg.initData : '' }, extra || {});
  // a plain-text body keeps this a simple request (no preflight), which Apps Script accepts from another site
  return fetch(ENDPOINT, { method: 'POST', body: JSON.stringify(body) })
    .then(function (r) { return r.json(); })
    .catch(function () { return { ok: false, error: 'network' }; });
}

var ERRORS = {
  unauthorized: 'الصفحة قديمة. سكّرها وافتحها من جديد من زر «الاستوديو».',
  repeat: 'هذا انرسل قبل، ما يحتاج تعيده.',
  'not waiting': 'الحلقة مو منتظرتك الحين.',
  'not running': 'ما فيه حلقة شغالة الحين.',
  busy: 'البوت مشغول الحين، جرّب بعد شوي.',
  network: 'ما قدرت أوصل للسيرفر. جرّب بعد شوي.'
};
function writeError(r) { return ERRORS[r && r.error] || (r && r.msg) || 'ما تسجّل، جرّب مرة ثانية.'; }

// One write: send, toast the answer, then read the studio again (unless the caller keeps its own screen).
function write(action, extra, okText, button, opts) {
  opts = opts || {};
  if (button) button.disabled = true;
  return api(action, extra).then(function (r) {
    var ok = opts.loose ? (r && !r.error && r.ok !== false) : (r && r.ok);
    if (button) button.disabled = false;
    toast(ok ? (r.msg || okText) : writeError(r), !ok);
    if (ok && opts.onOk) opts.onOk(r);
    if (ok || (r && r.error === 'not waiting') || (r && r.error === 'not running')) load(opts.quiet);
    return ok;
  });
}

function fail(r) {
  clear();
  var msg = r && r.error === 'unauthorized' ? 'افتح الاستوديو من زر «الاستوديو» داخل تلغرام.' :
    (r && r.error === 'network' ? 'ما قدرت أوصل للسيرفر. جرّب بعد شوي.' : 'صار خطأ، جرّب مرة ثانية.');
  var c = add(el('div', 'card empty-state'), el('div', 'big-ic', '⚠️'), el('p', '', msg));
  if (!r || r.error !== 'unauthorized') c.appendChild(btn('ghost', '⟳ جرّب مرة ثانية', function () { load(); }));
  view.appendChild(c);
}

function skeleton() {
  clear();
  view.appendChild(el('p', 'loading', 'جاري التحميل…'));
  [96, 150, 220].forEach(function (h) { var s = el('div', 'sk'); s.style.height = h + 'px'; view.appendChild(s); });
}

function setStamp(d) {
  var t = d && d.at ? new Date(d.at) : new Date();
  if (isNaN(t.getTime())) t = new Date();
  stampEl.textContent = 'آخر تحديث ' + pad(t.getHours()) + ':' + pad(t.getMinutes());
}

// Read the studio. quiet = keep the current screen (used after an idea verdict, which already updated its card).
function load(quiet) {
  if (state.loading) return;
  state.loading = true;
  refreshBtn.classList.add('spin');
  if (!quiet || !state.data) skeleton();
  api('studio').then(function (r) {
    state.loading = false;
    refreshBtn.classList.remove('spin');
    if (!r || !r.ok) { if (!quiet || !state.data) fail(r); return; }
    state.data = r;
    setStamp(r);
    if (!quiet) render();
  });
}

// ---------- tab 1: the episode

var STEP_ICON = { done: '✅', now: '⏳', wait: '🎧', todo: '⬜' };

function stepLine(s) {
  var li = el('li', s.status || 'todo');
  add(li, el('span', 'si', STEP_ICON[s.status] || '⬜'), el('span', 'sn', s.name));
  var side = '';
  if (s.status === 'done') side = 'خلص';
  else if (s.status === 'now') side = isNum(s.done) && isNum(s.total) ? s.done + '/' + s.total : 'يشتغل الحين';
  else if (s.status === 'wait') side = 'ينتظرك';
  li.appendChild(el('span', 'ss', side));
  li.firstChild.setAttribute('aria-hidden', 'true');
  return li;
}

function fixForm(j) {
  var f = el('div', 'card form soft');
  f.hidden = true;
  var l1 = el('label', '', 'أرقام اللقطات، مثل: 3 و 7');
  var shots = el('input');
  shots.id = 'fix-shots'; l1.htmlFor = 'fix-shots';
  shots.inputMode = 'numeric'; shots.maxLength = 40; shots.placeholder = '3, 7'; shots.autocomplete = 'off';
  var l2 = el('label', '', 'شنو تبي يتغيّر؟');
  var note = el('input');
  note.id = 'fix-note'; l2.htmlFor = 'fix-note';
  note.maxLength = 250; note.placeholder = 'مثل: خل العملة ذهبية'; note.autocomplete = 'off';
  add(f, l1, shots, l2, note);
  f.appendChild(btn('primary', '🔁 أرسل التعديل', function (b) {
    var raw = shots.value.replace(/[٠-٩]/g, function (c) { return String(c.charCodeAt(0) - 0x660); })
      .replace(/[،\s]+/g, ',').replace(/,+/g, ',').replace(/^,|,$/g, '');
    if (!/^[0-9]+(,[0-9]+)*$/.test(raw)) { toast('اكتب أرقام اللقطات بس، مثل: 3، 7', true); shots.focus(); return; }
    if (!note.value.trim()) { toast('اكتب شنو تبي يتغيّر', true); note.focus(); return; }
    write('fixShots', { id: j.id, shots: raw, note: note.value.trim() }, 'وصل التعديل، البوت بيشتغل عليه', b);
  }));
  return f;
}

function renderJob(d) {
  var j = d.job;
  if (!j) {
    var e = add(el('div', 'card empty-state'), el('div', 'big-ic', '🌙'), el('div', 't', 'ما فيه حلقة شغالة'),
      el('p', 'muted', 'اكتب بالمحادثة: حلقة جديدة + الموضوع'));
    view.appendChild(e);
    var n = (d.ideas || []).length;
    var link = add(el('div', 'card soft'), el('div', 'nm', '💡 تبي فكرة؟'),
      el('p', 'muted small', n ? 'عندك ' + n + ' أفكار جديدة اليوم تنتظر رأيك.' : 'شوف الأفكار والطابور.'));
    link.appendChild(btn('', 'روح للأفكار', function () { go('ideas'); }));
    view.appendChild(link);
    return;
  }
  var head = el('div', 'card');
  var top = el('div', 'job-head');
  add(top, el('h1', '', unescapeHtml(j.label) || ('حلقة ' + j.id)), j.stateAr ? el('span', 'chip gold', j.stateAr) : null);
  head.appendChild(top);
  var pct = Math.max(0, Math.min(100, Number(j.pct) || 0));
  var bar = el('div', 'bar');
  bar.setAttribute('role', 'progressbar');
  bar.setAttribute('aria-valuemin', '0'); bar.setAttribute('aria-valuemax', '100'); bar.setAttribute('aria-valuenow', String(pct));
  bar.setAttribute('aria-label', 'وين وصلت الحلقة');
  var fill = el('span'); fill.style.width = pct + '%'; bar.appendChild(fill);
  var meta = el('div', 'bar-meta');
  add(meta, el('b', '', pct + '%'), isNum(j.eta_min) ? el('span', '', 'باقي تقريباً ' + Math.round(j.eta_min) + ' د') : el('span'));
  add(head, bar, meta);
  view.appendChild(head);

  var steps = el('ul', 'steps');
  (j.steps || []).forEach(function (s) { steps.appendChild(stepLine(s)); });
  view.appendChild(add(el('div', 'card'), steps));

  if (isNum(j.spent)) {
    var g = el('div', 'grid2');
    add(g, add(el('div', 'tile'), el('div', 'lab', '💵 صرف الحلقة'), el('div', 'val', usd(j.spent))));
    if (isNum(d.queue)) add(g, add(el('div', 'tile'), el('div', 'lab', '📋 بالطابور'), el('div', 'val', num(d.queue) + ' فكرة')));
    view.appendChild(g);
  }
  if (j.next) view.appendChild(add(el('div', 'card soft next'), el('span', 'lab', '👉 الخطوة الجاية'), el('span', '', j.next)));
  if (j.held) view.appendChild(add(el('div', 'card info'), el('div', 'nm', '⏸️ الحلقة واقفة: اكتب «كمل» بالمحادثة')));

  if (j.gate === 'voice') {
    view.appendChild(btn('primary', '🎙️ الصوت تمام', function (b) {
      confirmThen('سمعت الصوت وتمام؟ بعدها يبدأ الصرف على الصور والمقاطع.', function () {
        write('voiceOk', { id: j.id }, 'اعتمدت الصوت، كملنا', b);
      });
    }));
  } else if (j.gate === 'video') {
    var form = fixForm(j);
    view.appendChild(btn('primary', '✅ ممتاز', function (b) {
      confirmThen('الفيديو تمام؟ تصير جاهزة للنشر (النشر نفسه تكتبه بالمحادثة).', function () {
        write('approveVideo', { id: j.id }, 'تمام، صارت جاهزة للنشر', b);
      });
    }));
    var fb = btn('', '✏️ عدّل لقطات', function () {
      form.hidden = !form.hidden;
      fb.setAttribute('aria-expanded', String(!form.hidden));
      if (!form.hidden) form.querySelector('input').focus();
    });
    fb.setAttribute('aria-expanded', 'false');
    add(view, fb, form);
  }
  if (j.can_pause) {
    view.appendChild(btn('ghost', '⏸️ وقّف الحلقة', function (b) {
      confirmThen('توقف الحلقة الحين؟ ترجعها بكلمة «كمل» بالمحادثة.', function () {
        write('pause', { id: j.id }, 'وقفت الحلقة', b);
      });
    }));
  }
}

// ---------- tab 2: ideas

function ideaCard(i, d) {
  var c = el('div', 'card idea');
  var tl = el('div', 'tl');
  var badge = el('span', 'star-badge', '⭐');
  badge.setAttribute('aria-label', 'بالطابور');
  add(tl, el('span', '', i.title), i.star ? badge : null);
  c.appendChild(tl);
  if (i.hook) c.appendChild(el('p', 'hk', i.hook));
  var meta = [i.source, i.signal].filter(function (x) { return x; }).join(' · ');
  if (meta) c.appendChild(el('div', 'mt', meta));
  if (i.story || i.why) {
    var more = el('div', 'more');
    more.hidden = true;
    if (i.story) add(more, add(el('p', ''), el('b', '', 'القصة: '), document.createTextNode(i.story)));
    if (i.why) add(more, add(el('p', ''), el('b', '', 'ليش تنفع: '), document.createTextNode(i.why)));
    var tg2 = el('button', 'link', 'المزيد ▾');
    tg2.type = 'button';
    tg2.setAttribute('aria-expanded', 'false');
    tg2.onclick = function () {
      tap();
      more.hidden = !more.hidden;
      tg2.textContent = more.hidden ? 'المزيد ▾' : 'أقل ▴';
      tg2.setAttribute('aria-expanded', String(!more.hidden));
    };
    add(c, tg2, more);
  }
  var actions = el('div');
  if (i.star) {
    actions.appendChild(el('div', 'in-queue', '✅ بالطابور'));
  } else {
    var row = el('div', 'btn-row');
    var yes = btn('primary small', '⭐ للطابور', function (b) {
      write('ideaVerdict', { id: i.id, verdict: 'star' }, 'انضافت للطابور', b, { quiet: true, onOk: function () {
        i.star = true;
        tl.appendChild(badge);
        while (actions.firstChild) actions.removeChild(actions.firstChild);
        actions.appendChild(el('div', 'in-queue', '✅ بالطابور'));
      } });
    });
    var no = btn('ghost small', '✖ شيلها', function (b) {
      write('ideaVerdict', { id: i.id, verdict: 'no' }, 'انشالت', b, { quiet: true, onOk: function () {
        d.ideas = d.ideas.filter(function (x) { return x !== i; });
        c.classList.add('gone');
        setTimeout(function () {
          if (c.parentNode) c.parentNode.removeChild(c);
          var cnt = document.getElementById('idea-count');
          if (cnt) cnt.textContent = '(' + d.ideas.length + ')';
          if (!d.ideas.length) { var box = document.getElementById('idea-list'); if (box) box.appendChild(el('p', 'empty', 'ما فيه أفكار جديدة اليوم')); }
        }, 360);
      } });
    });
    add(row, yes, no);
    actions.appendChild(row);
  }
  c.appendChild(actions);
  return c;
}

function renderIdeas(d) {
  var ideas = d.ideas || [];
  var h = el('h1', '', 'أفكار اليوم ');
  var cnt = el('span', 'count', '(' + ideas.length + ')');
  cnt.id = 'idea-count';
  view.appendChild(add(h, cnt));
  view.appendChild(el('p', 'sub', '⭐ تروح للطابور، ✖ تنشال'));
  var list = el('div');
  list.id = 'idea-list';
  if (!ideas.length) list.appendChild(el('p', 'empty', 'ما فيه أفكار جديدة اليوم'));
  ideas.forEach(function (i) { list.appendChild(ideaCard(i, d)); });
  view.appendChild(list);

  if (isNum(d.queue)) view.appendChild(add(el('div', 'card soft'), el('div', 'nm', '📋 الطابور: ' + num(d.queue) + ' فكرة')));
  var f = el('div', 'card form');
  var lab = el('label', '', 'اكتب فكرتك');
  var inp = el('input');
  inp.id = 'idea-text'; lab.htmlFor = 'idea-text';
  inp.maxLength = 200; inp.placeholder = 'مثل: اختراع القلم'; inp.autocomplete = 'off'; inp.enterKeyHint = 'send';
  var row = el('div', 'add-row');
  var send = btn('primary', 'أضف', function (b) {
    var text = inp.value.trim();
    if (!text) { toast('اكتب الفكرة أول', true); inp.focus(); return; }
    write('addIdea', { text: text.substring(0, 200) }, 'انضافت فكرتك', b, { onOk: function () { inp.value = ''; } });
  });
  inp.onkeydown = function (ev) { if (ev.key === 'Enter') send.click(); };
  add(row, inp, send);
  add(f, lab, row);
  view.appendChild(f);
}

// ---------- tab 3: numbers

function chart(eps) {
  var list = eps.slice(0, 12);
  var max = Math.max.apply(null, list.map(function (e) { return Number(e.total) || 0; }).concat([1]));
  var box = el('div', 'chart');
  box.setAttribute('role', 'list');
  list.forEach(function (e) {
    var v = Number(e.total) || 0;
    var r = el('div', 'ch-row' + (v === max ? ' max' : ''));
    r.setAttribute('role', 'listitem');
    r.setAttribute('aria-label', e.name + ': ' + num(v) + ' مشاهدة');
    var track = el('div', 'ch-track');
    var fill = el('span');
    fill.style.width = (v / max * 100).toFixed(2) + '%';
    track.appendChild(fill);
    add(r, el('span', 'ch-name', e.name), track, el('span', 'ch-val', num(v)));
    box.appendChild(r);
  });
  return box;
}

function tiktokForm(eps) {
  var f = el('div', 'card form');
  f.appendChild(el('h2', '', '🎵 مشاهدات تيك توك'));
  f.appendChild(el('p', 'mt', 'تيك توك ما يعطينا الأرقام، تكتبها بنفسك.'));
  var l1 = el('label', '', 'الحلقة');
  var sel = el('select');
  sel.id = 'tt-ep'; l1.htmlFor = 'tt-ep';
  eps.forEach(function (e) { var o = el('option', '', e.name); o.value = e.id; sel.appendChild(o); });
  var l2 = el('label', '', 'عدد المشاهدات');
  var v = el('input');
  v.id = 'tt-val'; l2.htmlFor = 'tt-val';
  v.type = 'number'; v.inputMode = 'numeric'; v.min = '0'; v.step = '1'; v.placeholder = '0';
  add(f, l1, sel, l2, v);
  f.appendChild(btn('primary', '💾 احفظ', function (b) {
    var n = Number(v.value);
    if (v.value === '' || !(n >= 0) || Math.floor(n) !== n) { toast('اكتب رقم صحيح', true); v.focus(); return; }
    write('tiktok', { ep: sel.value, value: n }, 'انحفظ', b);
  }));
  return f;
}

function renderStats(d) {
  var s = d.stats;
  view.appendChild(el('h1', '', 'الأرقام'));
  if (!s) { view.appendChild(el('p', 'empty', 'الأرقام ما وصلت للحين. جرّب ⟳ بعد شوي.')); return; }
  if (s.updated) view.appendChild(el('p', 'sub', 'آخر تحديث: ' + s.updated));
  var g = el('div', 'grid3');
  (s.platforms || []).forEach(function (p) {
    add(g, add(el('div', 'tile center'), el('div', 'ic', p.icon), el('div', 'val', num(p.followers)), el('div', 'lab', p.name),
      el('div', 'up', Number(p.growth) > 0 ? '▲ ' + num(p.growth) : '')));
  });
  view.appendChild(g);
  if (s.last) {
    var L = s.last, c = el('div', 'card');
    add(c, el('div', 'mt', 'آخر حلقة'), el('div', 'nm', L.name), L.date ? el('div', 'mt', L.date) : null,
      el('div', 'last-total', num(L.total) + ' مشاهدة'));
    var pn = el('div', 'plat-nums');
    add(pn, el('span', '', '▶️ يوتيوب ' + num(L.yt)), el('span', '', '📘 فيسبوك ' + num(L.fb)), el('span', '', '📷 انستغرام ' + num(L.ig)),
      isNum(L.tiktok) ? el('span', '', '🎵 تيك توك ' + num(L.tiktok)) : null);
    c.appendChild(pn);
    view.appendChild(c);
  }
  var eps = s.episodes || [];
  if (eps.length) {
    view.appendChild(el('h2', '', 'مشاهدات الحلقات'));
    view.appendChild(add(el('div', 'card'), el('p', 'mt', 'الأحدث فوق، والأقوى بالذهبي'), chart(eps)));
  }
  if (s.top && s.top.length) {
    view.appendChild(el('h2', '', 'أقوى الحلقات'));
    var t = el('div', 'card');
    s.top.slice(0, 3).forEach(function (e, i) {
      add(t, add(el('div', 'row'), el('span', 'nm', ['🥇', '🥈', '🥉'][i] + ' ' + e.name), el('span', 'v', num(e.total))));
    });
    view.appendChild(t);
  }
  if (eps.length) view.appendChild(tiktokForm(eps));
}

// ---------- tab 4: bank

function meterTile(label, value, cap) {
  var t = add(el('div', 'tile'), el('div', 'lab', label), el('div', 'val', usd(value)));
  if (isNum(cap) && Number(cap) > 0) {
    var ratio = Number(value) / Number(cap);
    t.appendChild(withUsd('div', 'of', 'من ', cap));
    var m = el('div', 'meter' + (ratio >= 1 ? ' over' : ratio >= 0.8 ? ' warn' : ''));
    m.setAttribute('role', 'meter');
    m.setAttribute('aria-valuemin', '0'); m.setAttribute('aria-valuemax', String(cap)); m.setAttribute('aria-valuenow', String(value));
    m.setAttribute('aria-label', label);
    var f = el('span'); f.style.width = Math.min(100, ratio * 100).toFixed(1) + '%';
    t.appendChild(add(m, f));
  }
  return t;
}

function switchRow(label, hint, on, action) {
  var r = el('div', 'switch-row');
  var txt = add(el('div'), el('div', 'nm', label), hint ? el('div', 'mt', hint) : null);
  var b = el('button', 'toggle');
  b.type = 'button';
  b.setAttribute('aria-pressed', String(!!on));
  b.setAttribute('aria-label', label);
  b.onclick = function () {
    tap();
    write(action, { on: !on }, !on ? 'تشغّل' : 'انطفى', b, { loose: true });
  };
  return add(r, txt, b);
}

function renderBank(d) {
  var k = d.bank;
  view.appendChild(el('h1', '', 'البنك'));
  if (!k) {
    view.appendChild(el('p', 'empty', 'أرقام الصرف ما وصلت للحين.'));
  } else {
    var hero = add(el('div', 'card hero'), el('div', 'lab muted', 'باقي برصيد قوقل'), el('div', 'val', usd(k.google_left)));
    if (!k.google_real) hero.appendChild(el('span', 'chip', 'تقدير'));
    view.appendChild(hero);
    var caps = k.caps || {};
    view.appendChild(add(el('div', 'grid2'), meterTile('صرف هالشهر', k.month, caps.month), meterTile('صرف اليوم', k.day, caps.day)));
    if (k.eleven) {
      view.appendChild(add(el('div', 'card'), add(el('div', 'row'), el('span', 'nm', '🎙️ رصيد الصوت'),
        el('span', 'v', num(k.eleven.left) + ' من ' + num(k.eleven.limit)))));
    }
    view.appendChild(el('h2', '', 'الحلقات'));
    var list = el('div', 'card');
    if (!(k.episodes || []).length) list.appendChild(el('p', 'empty', 'ما فيه صرف مسجّل بعد.'));
    (k.episodes || []).forEach(function (e) {
      var left = add(el('div', 'nm'), el('div', '', e.name), Number(e.fix) > 0 ? withUsd('div', 'mt', 'منها تصليح ', e.fix) : null);
      add(list, add(el('div', 'row'), left, el('span', 'v', usd(e.usd))));
    });
    view.appendChild(list);
  }
  var sw = d.switches || {};
  view.appendChild(el('h2', '', 'الإعدادات'));
  var set = el('div', 'card');
  add(set, switchRow('اسمع الصوت قبل الصرف', 'البوت يوقف بعد الصوت لين تقول «تمام»', sw.voice_gate, 'setVoiceGate'),
    switchRow('ثبّت بطاقة الحلقة فوق المحادثة', 'تبقى بطاقة الحلقة ظاهرة فوق', sw.card_pin, 'setPin'));
  if (k && k.caps) {
    var c = k.caps;
    if (isNum(c.episode) || isNum(c.fix)) {
      var line = el('p', 'mt');
      if (isNum(c.episode)) line.appendChild(withUsd('span', '', 'سقف الحلقة ', c.episode, isNum(c.fix) ? ' · ' : ''));
      if (isNum(c.fix)) line.appendChild(withUsd('span', '', 'التصليح ', c.fix));
      set.appendChild(line);
    }
    set.appendChild(el('p', 'mt', 'تغيّرها بالمحادثة: سقف اليوم 30'));
  }
  view.appendChild(set);
}

// ---------- navigation

var RENDER = { job: renderJob, ideas: renderIdeas, stats: renderStats, bank: renderBank };

function render() {
  if (!state.data) return;
  clear();
  RENDER[state.tab](state.data);
}

function markTabs() {
  Array.prototype.forEach.call(document.querySelectorAll('#tabs button'), function (b) {
    if (b.getAttribute('data-tab') === state.tab) b.setAttribute('aria-current', 'page');
    else b.removeAttribute('aria-current');
  });
}

function go(tab) {
  state.tab = tab;
  saveTab(tab);
  markTabs();
  window.scrollTo(0, 0);
  if (state.data) render();
}

Array.prototype.forEach.call(document.querySelectorAll('#tabs button'), function (b) {
  b.onclick = function () { tap(); go(b.getAttribute('data-tab')); };
});
refreshBtn.onclick = function () { tap(); load(); };

state.tab = readTab();
markTabs();
load();
