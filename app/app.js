'use strict';
// Mini App for the channel owner. All data comes from the Apps Script endpoint, which answers only to a valid Telegram
// signature (initData). Everything is drawn with textContent: no data is ever put in as HTML.
var ENDPOINT = 'https://script.google.com/macros/s/AKfycbxcSL9ORmrW9xwwMJo5xO6_0vxy50Rz9HURme91nAqNvxeYshOzQz5Mhv5kP1Tfo2jP/exec';
var tg = window.Telegram && window.Telegram.WebApp;
if (tg) { tg.ready(); tg.expand(); }

var view = document.getElementById('view');
var toastEl = document.getElementById('toast');
var cache = { episodes: null };

function el(tag, cls, text) {
  var e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text;
  return e;
}
function num(n) { return Number(n || 0).toLocaleString('en-US'); }
function toast(msg) {
  toastEl.textContent = msg;
  toastEl.className = 'show';
  setTimeout(function () { toastEl.className = ''; }, 2200);
}
function clear() { while (view.firstChild) view.removeChild(view.firstChild); }

function api(action, extra) {
  var body = Object.assign({ action: action, initData: tg ? tg.initData : '' }, extra || {});
  // a plain-text body keeps this a simple request (no preflight), which Apps Script accepts from another site
  return fetch(ENDPOINT, { method: 'POST', body: JSON.stringify(body) })
    .then(function (r) { return r.json(); })
    .catch(function () { return { ok: false, error: 'network' }; });
}

function fail(r) {
  clear();
  var msg = r && r.error === 'unauthorized' ? 'افتح هذي اللوحة من زر «اللوحة» داخل تلغرام.' :
    (r && r.error === 'network' ? 'ما قدرت أوصل للسيرفر. جرّب بعد شوي.' : 'صار خطأ، جرّب مرة ثانية.');
  view.appendChild(el('p', 'empty', msg));
}

function pageHead(title, sub) {
  view.appendChild(el('h1', '', title));
  if (sub) view.appendChild(el('p', 'sub', sub));
}

// ---------- screens

function renderHome(d) {
  clear();
  pageHead('أصل الحكاية', d.updated ? 'آخر تحديث للأرقام: ' + d.updated : '');
  var g = el('div', 'grid');
  d.platforms.forEach(function (p) {
    var c = el('div', 'card plat');
    c.appendChild(el('div', 'ic', p.icon));
    c.appendChild(el('div', 'n', num(p.followers)));
    c.appendChild(el('div', 't', p.name));
    c.appendChild(el('div', 'up', p.growth > 0 ? '▲ ' + num(p.growth) : ''));
    g.appendChild(c);
  });
  view.appendChild(g);
  if (d.last) {
    view.appendChild(el('h2', '', 'آخر حلقة'));
    var c = el('div', 'card');
    c.appendChild(el('div', 'nm', d.last.name));
    c.appendChild(el('div', 'mt', d.last.date));
    c.appendChild(el('div', 'big', num(d.last.total) + ' مشاهدة'));
    c.appendChild(el('div', 'chips', '▶️ ' + num(d.last.yt) + '   📘 ' + num(d.last.fb) + '   📷 ' + num(d.last.ig)));
    view.appendChild(c);
  }
  if (d.top && d.top.length) {
    view.appendChild(el('h2', '', 'أقوى الحلقات'));
    var t = el('div', 'card');
    d.top.forEach(function (e, i) {
      var r = el('div', 'row');
      r.appendChild(el('span', 'nm', (i + 1) + '. ' + e.name));
      r.appendChild(el('span', 'big', num(e.total)));
      t.appendChild(r);
    });
    view.appendChild(t);
  }
}

function bars(e, max) {
  var b = el('div', 'bars');
  [['b-yt', e.yt], ['b-fb', e.fb], ['b-ig', e.ig]].forEach(function (x) {
    var s = el('span', x[0]);
    s.style.width = Math.max(2, Math.round(x[1] / (max || 1) * 60)) + '%';
    b.appendChild(s);
  });
  return b;
}

function renderEpisodes(d) {
  cache.episodes = d.episodes;
  clear();
  pageHead('الحلقات', 'مشاهدات كل حلقة على المنصات');
  var max = Math.max.apply(null, d.episodes.map(function (e) { return e.total; }).concat([1]));
  var box = el('div', 'card');
  if (!d.episodes.length) box.appendChild(el('p', 'empty', 'ما فيه حلقات بعد.'));
  d.episodes.forEach(function (e) {
    var r = el('div', 'row');
    var left = el('div');
    left.appendChild(el('div', 'nm', e.name));
    left.appendChild(el('div', 'mt', e.date + (e.tiktok !== null ? ' · تيك توك ' + num(e.tiktok) : '')));
    left.appendChild(bars(e, max));
    r.appendChild(left);
    r.appendChild(el('span', 'big', num(e.total)));
    box.appendChild(r);
  });
  view.appendChild(box);
  view.appendChild(el('h2', '', 'لقطات بعد النشر'));
  var sn = el('div', 'card');
  if (!d.snaps.length) sn.appendChild(el('p', 'empty', 'تظهر هنا بعد ساعتين و24 ساعة و7 أيام من نشر أي حلقة جديدة.'));
  d.snaps.forEach(function (s) {
    var r = el('div', 'row');
    var left = el('div');
    left.appendChild(el('div', 'nm', s.name + ' · ' + s.label));
    left.appendChild(el('div', 'mt', '▶️ ' + num(s.yt) + '  📘 ' + num(s.fb) + '  📷 ' + num(s.ig)));
    r.appendChild(left);
    r.appendChild(el('span', 'big', num(s.total)));
    sn.appendChild(r);
  });
  view.appendChild(sn);
}

function renderQueue(d) {
  clear();
  pageHead('الطابور', 'أفكارك ومراحل كل حلقة');
  var add = el('div', 'card');
  var inp = el('input');
  inp.placeholder = 'فكرة جديدة، مثل: اختراع القلم';
  inp.maxLength = 120;
  var btn = el('button', 'act', 'أضف للطابور');
  btn.className = 'act';
  btn.onclick = function () {
    var text = inp.value.trim();
    if (!text) return;
    btn.disabled = true;
    api('addIdea', { text: text }).then(function (r) {
      btn.disabled = false;
      if (r.ok) { toast('انضافت'); load('queue'); } else toast('ما انضافت');
    });
  };
  add.appendChild(inp);
  add.appendChild(btn);
  view.appendChild(add);
  var box = el('div', 'card');
  var items = d.items.filter(function (i) { return i.stage !== 'منشورة'; });
  if (!items.length) box.appendChild(el('p', 'empty', 'الطابور فاضي.'));
  items.forEach(function (i) {
    var r = el('div', 'row');
    var left = el('div');
    left.appendChild(el('div', 'nm', i.idea));
    if (i.note) left.appendChild(el('div', 'mt', i.note));
    r.appendChild(left);
    var sel = el('select', 'stage');
    d.stages.forEach(function (s) {
      var o = el('option', '', s);
      o.value = s;
      if (s === i.stage) o.selected = true;
      sel.appendChild(o);
    });
    sel.onchange = function () {
      api('setStage', { id: i.id, stage: sel.value }).then(function (res) { toast(res.ok ? 'تحدثت المرحلة' : 'ما تحدثت'); });
    };
    r.appendChild(sel);
    box.appendChild(r);
  });
  view.appendChild(box);
}

function episodeSelect(eps) {
  var sel = el('select');
  eps.forEach(function (e) {
    var o = el('option', '', e.name);
    o.value = e.id;
    sel.appendChild(o);
  });
  return sel;
}

function renderLog(eps) {
  clear();
  pageHead('تسجيل', 'أرقام تحتاج تكتبها بنفسك');
  var tt = el('div', 'card');
  tt.appendChild(el('h2', '', 'مشاهدات تيك توك'));
  tt.appendChild(el('label', '', 'الحلقة'));
  var s1 = episodeSelect(eps);
  tt.appendChild(s1);
  tt.appendChild(el('label', '', 'عدد المشاهدات'));
  var v1 = el('input');
  v1.type = 'number'; v1.inputMode = 'numeric'; v1.min = '0';
  tt.appendChild(v1);
  var b1 = el('button', 'act', 'احفظ');
  b1.onclick = function () {
    if (v1.value === '') return;
    b1.disabled = true;
    api('tiktok', { ep: s1.value, value: Number(v1.value) }).then(function (r) {
      b1.disabled = false;
      toast(r.ok ? 'انحفظ' : 'ما انحفظ');
      if (r.ok) v1.value = '';
    });
  };
  tt.appendChild(b1);
  view.appendChild(tt);

  var cs = el('div', 'card');
  cs.appendChild(el('h2', '', 'تكلفة الحلقة (رصيد)'));
  cs.appendChild(el('label', '', 'الحلقة'));
  var s2 = episodeSelect(eps);
  cs.appendChild(s2);
  cs.appendChild(el('label', '', 'النوع'));
  var k = el('select');
  [['kling', 'كلنق'], ['voice', 'صوت']].forEach(function (x) {
    var o = el('option', '', x[1]);
    o.value = x[0];
    k.appendChild(o);
  });
  cs.appendChild(k);
  cs.appendChild(el('label', '', 'الرصيد المصروف'));
  var v2 = el('input');
  v2.type = 'number'; v2.inputMode = 'numeric'; v2.min = '0';
  cs.appendChild(v2);
  var b2 = el('button', 'act', 'احفظ');
  b2.onclick = function () {
    if (v2.value === '') return;
    b2.disabled = true;
    api('cost', { ep: s2.value, kind: k.value, value: Number(v2.value) }).then(function (r) {
      b2.disabled = false;
      toast(r.ok ? 'انحفظ' : 'ما انحفظ');
      if (r.ok) v2.value = '';
    });
  };
  cs.appendChild(b2);
  view.appendChild(cs);
}

// Production (order 6, 2026-10-28): open jobs, the video waiting for your opinion (gate 2) and the credits.
// «ممتاز» and «عدّل لقطات» here do exactly what the chat buttons do; the bot confirms in the chat.
function money(cents) { return '$' + (Number(cents || 0) / 100).toFixed(2); }

function reviewCard(j) {
  var c = el('div', 'card');
  c.appendChild(el('h2', '', 'فيديو ينتظر رأيك'));
  c.appendChild(el('div', 'nm', j.episode || ('مهمة ' + j.id)));
  c.appendChild(el('div', 'mt', 'الفيديو والصورة اللي فيها اللقطات مرقمة وصلتك بالمحادثة.'));
  var ok = el('button', 'act', 'ممتاز ✅ (جاهزة للنشر)');
  ok.onclick = function () {
    var go = function (yes) {
      if (!yes) return;
      ok.disabled = true;
      api('approveVideo', { id: j.id }).then(function (r) {
        toast(r.ok ? 'تمام، صارت جاهزة للنشر' : 'ما تسجلت، جرّب من المحادثة');
        load('prod');
      });
    };
    if (tg && tg.showConfirm) tg.showConfirm('أكيد الفيديو ممتاز؟ (النشر يبقى يحتاج «اعتمد النشر»)', go);
    else go(window.confirm('أكيد الفيديو ممتاز؟'));
  };
  c.appendChild(ok);
  c.appendChild(el('label', '', 'أرقام اللقطات اللي تبي تتعدل'));
  var shots = el('input');
  shots.placeholder = 'مثل: 3, 7';
  shots.maxLength = 40;
  c.appendChild(shots);
  c.appendChild(el('label', '', 'ملاحظتك'));
  var note = el('input');
  note.placeholder = 'مثل: خل العملة ذهبية';
  note.maxLength = 250;
  c.appendChild(note);
  var fix = el('button', 'act', 'رجّعها للكمبيوتر 🔁');
  fix.onclick = function () {
    if (!/[0-9٠-٩]/.test(shots.value)) { toast('اكتب رقم لقطة وحدة على الأقل'); return; }
    fix.disabled = true;
    api('fixShots', { id: j.id, shots: shots.value, note: note.value.trim() }).then(function (r) {
      toast(r.ok ? 'رجعت للكمبيوتر' : 'ما رجعت، جرّب من المحادثة');
      load('prod');
    });
  };
  c.appendChild(fix);
  return c;
}

function creditsCard(cr) {
  var c = el('div', 'card');
  c.appendChild(el('h2', '', 'الرصيد'));
  if (!cr || !cr.ok) { c.appendChild(el('p', 'empty', 'ما قدرت أقرا الرصيد.')); return c; }
  var row = function (name, value) {
    var r = el('div', 'row');
    r.appendChild(el('span', 'nm', name));
    r.appendChild(el('span', 'big', value));
    c.appendChild(r);
  };
  row('كلود (كتابة النصوص)', '$' + cr.claude.left.toFixed(2) + ' من $' + cr.claude.start);
  c.appendChild(el('div', 'mt', 'هالشهر ' + '$' + cr.claude.usd.toFixed(2) + ' في ' + cr.claude.calls + ' طلب'));
  var pc = cr.pc || {};
  if (pc.vertex_month_cents !== undefined) {
    row('قوقل (الفيديو) هالشهر', money(pc.vertex_month_cents) + (pc.vertex_cap_cents ? ' من ' + money(pc.vertex_cap_cents) : ''));
  }
  if (pc.eleven_left !== undefined) {
    row('إلفن لابز (الصوت) الباقي', num(pc.eleven_left) + (pc.eleven_limit ? ' من ' + num(pc.eleven_limit) : ''));
  }
  c.appendChild(el('div', 'mt', pc.at ? 'أرقام الكمبيوتر من آخر مسودة: ' + pc.at.substring(0, 16).replace('T', ' ') :
    'أرقام قوقل وإلفن لابز تظهر بعد أول مسودة من الكمبيوتر.'));
  return c;
}

// The worker card (phase 4, 2026-10-27): one big switch for the PC worker, its status, the job it holds, the caps and the
// «اسمع الصوت» gate. Every change is confirmed and the bot writes it in the chat too, so the chat keeps the record.
function confirmThen(text, fn) {
  if (tg && tg.showConfirm) tg.showConfirm(text, function (yes) { if (yes) fn(); });
  else if (window.confirm(text)) fn();
}

function workerCard(w) {
  var c = el('div', 'card');
  c.appendChild(el('h2', '', 'العامل (الكمبيوتر)'));
  if (!w || !w.ok) { c.appendChild(el('p', 'empty', 'ما قدرت أقرا حالة العامل.')); return c; }
  var pc = w.pc || {};
  c.appendChild(el('div', 'state ' + (w.enabled ? 'on' : 'off'), w.enabled ? '▶️ شغّال' : '⏸️ واقف'));
  c.appendChild(el('div', 'mt', pc.online ? '🟢 الكمبيوتر متصل (قبل ' + pc.seen_min + ' د)' :
    (pc.seen_min === null ? '🔴 الكمبيوتر ما اتصل للحين' : '🔴 الكمبيوتر طافي (آخر مرة قبل ' + pc.seen_min + ' د)')));
  var sw = el('button', 'act big-btn', w.enabled ? '⏸️ وقّف العامل' : '▶️ شغّل العامل');
  sw.onclick = function () {
    confirmThen(w.enabled ? 'توقف العامل؟ الحلقة الشغالة الحين تكمل، والجديد ما يبدأ.' :
      'تشغّل العامل؟ الكمبيوتر بياخذ الحلقات اللي بالطابور ويصرف من الرصيد حسب السقف.', function () {
      sw.disabled = true;
      api('setWorker', { on: !w.enabled }).then(function (r) {
        toast(r.ok ? (r.enabled ? 'العامل شغّال' : 'العامل واقف') : 'ما تغيّر، جرّب مرة ثانية');
        load('prod');
      });
    });
  };
  c.appendChild(sw);
  if (w.job) {
    var j = w.job, line = j.name + ' — ' + j.stateAr + (j.stageAr ? ' · ' + j.stageAr : '');
    if (j.total) line += ' ' + j.done + '/' + j.total;
    c.appendChild(el('div', 'nm', line));
    var meta = [];
    if (j.spent_cents !== undefined) meta.push('صرفنا ' + money(j.spent_cents));
    if (j.eta_min) meta.push('باقي تقريباً ' + Math.round(j.eta_min) + ' د');
    meta.push('آخر تحديث قبل ' + j.minutes + ' د');
    c.appendChild(el('div', 'mt', meta.join(' · ')));
  } else {
    c.appendChild(el('div', 'mt', 'ما فيه حلقة عند الكمبيوتر الحين.'));
  }
  if (w.last_stop) {
    c.appendChild(el('div', 'mt warn', 'آخر توقف: ' + (w.last_stop.episode || '') + ' — ' + w.last_stop.text +
      ' (' + String(w.last_stop.at || '').substring(0, 16).replace('T', ' ') + ')'));
  }
  var gate = el('button', 'act ghost', '🎙️ اسمع الصوت قبل الصرف: ' + (w.voice_gate ? 'مفعّل ✅' : 'طافي'));
  gate.onclick = function () {
    gate.disabled = true;
    api('setVoiceGate', { on: !w.voice_gate }).then(function (r) {
      toast(r.ok ? 'تم' : 'ما تغيّر');
      load('prod');
    });
  };
  c.appendChild(gate);
  var caps = w.caps || {};
  c.appendChild(el('label', '', 'سقف الشهر بالدولار (0 = يوقف الصرف، فاضي = سقف الكمبيوتر ' + caps.max + ')'));
  var month = el('input');
  month.inputMode = 'decimal';
  month.value = caps.month === null || caps.month === undefined ? '' : String(caps.month);
  c.appendChild(month);
  c.appendChild(el('label', '', 'سقف اليوم بالدولار (0 = يوقف الصرف، فاضي = سقف الكمبيوتر)'));
  var day = el('input');
  day.inputMode = 'decimal';
  day.value = caps.day === null || caps.day === undefined ? '' : String(caps.day);
  c.appendChild(day);
  var save = el('button', 'act', 'احفظ السقف 💾');
  save.onclick = function () {
    var bad = [month.value, day.value].some(function (v) {
      var t = v.trim();
      return t !== '' && !(Number(t) >= 0 && Number(t) <= caps.max);
    });
    if (bad) { toast('الرقم لازم من 0 إلى ' + caps.max); return; }
    save.disabled = true;
    api('setCaps', { month: month.value.trim(), day: day.value.trim() }).then(function (r) {
      toast(r.ok ? 'انحفظ السقف' : 'ما انحفظ');
      load('prod');
    });
  };
  c.appendChild(save);
  return c;
}

function renderProd(d, cr, w) {
  clear();
  pageHead('الإنتاج', 'وين وصلت كل حلقة');
  view.appendChild(workerCard(w));
  var waiting = d.jobs.filter(function (j) { return j.review; });
  if (waiting.length) view.appendChild(reviewCard(waiting[waiting.length - 1]));
  var box = el('div', 'card');
  if (!d.jobs.length) box.appendChild(el('p', 'empty', 'ما فيه حلقة شغالة الحين.'));
  d.jobs.forEach(function (j) {
    var r = el('div', 'row');
    var left = el('div');
    left.appendChild(el('div', 'nm', j.episode || ('مهمة ' + j.id)));
    left.appendChild(el('div', 'mt', j.stateAr + ' · من ' + j.minutes + ' د'));
    if (j.note) left.appendChild(el('div', 'mt', j.note));
    if (j.voice) {  // voice gate: the audio and the numbered lines came in the chat; fixes go there («عدّل سطر 3: …»)
      var ok = el('button', 'act', 'الصوت تمام 🎙️✅');
      ok.onclick = function () {
        confirmThen('سمعت الصوت وتمام؟ بعدها يبدأ الصرف على الصور والمقاطع.', function () {
          ok.disabled = true;
          api('voiceOk', { id: j.id }).then(function (res) { toast(res.ok ? 'اعتمدت الصوت' : 'ما تسجل، جرّب من المحادثة'); load('prod'); });
        });
      };
      left.appendChild(ok);
    }
    r.appendChild(left);
    box.appendChild(r);
  });
  view.appendChild(box);
  view.appendChild(creditsCard(cr));
}

// ---------- navigation

function load(tab) {
  clear();
  view.appendChild(el('p', 'empty', 'لحظة...'));
  if (tab === 'home') api('home').then(function (r) { r.ok ? renderHome(r) : fail(r); });
  else if (tab === 'episodes') api('episodes').then(function (r) { r.ok ? renderEpisodes(r) : fail(r); });
  else if (tab === 'queue') api('queue').then(function (r) { r.ok ? renderQueue(r) : fail(r); });
  else if (tab === 'prod') {
    Promise.all([api('jobs'), api('credits'), api('worker')]).then(function (r) {
      r[0].ok ? renderProd(r[0], r[1], r[2]) : fail(r[0]);
    });
  }
  else if (tab === 'log') {
    var go = function (eps) { renderLog(eps); };
    if (cache.episodes) go(cache.episodes);
    else api('episodes').then(function (r) { if (r.ok) { cache.episodes = r.episodes; go(r.episodes); } else fail(r); });
  }
}

Array.prototype.forEach.call(document.querySelectorAll('#tabs button'), function (b) {
  b.onclick = function () {
    Array.prototype.forEach.call(document.querySelectorAll('#tabs button'), function (x) { x.className = x === b ? 'on' : ''; });
    load(b.getAttribute('data-tab'));
  };
});
load('home');
