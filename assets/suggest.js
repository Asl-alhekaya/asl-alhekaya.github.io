/* «اقترح حكاية» box on the home page (asl-alhekaya.github.io). Plain script, no library, no cookie, no storage.
   Loaded only when build_site.py SUGGEST_WORKER_URL is set (the CSP then allows script-src 'self' and connect-src the Worker).
   Without this script the form still works: a normal POST, and the Worker answers 303 to /#thanks or /#suggest-error.
   Contract with the Worker (studio/site/proposal-2026-11-22/worker.js): POST form-urlencoded fields text, topic, src, website
   (honeypot, empty), t (ms since the page was ready); header Accept: application/json -> {ok:true} or {ok:false, code}.
   Source: studio/site/assets/suggest.js (one copy; install_pages.py ships it, build_site.py copies it on the PC). */
(function () {
  'use strict';
  var form = document.getElementById('sform');
  if (!form || !window.fetch || !window.URLSearchParams || !window.FormData)
    return; // old browser: the plain form stays
  var MAX = 200,
    MIN = 3,
    TIMEOUT_MS = 15000;
  var text = document.getElementById('stext'),
    count = document.getElementById('scount');
  var msg = document.getElementById('smsg'),
    btn = document.getElementById('sbtn'),
    label = document.getElementById('sbtn-label');
  var box = document.getElementById('suggest'),
    thanks = document.getElementById('thanks');
  var rendered = Date.now(),
    lastTopic = null;
  form.noValidate = true; // the script shows its own messages; without it the browser's required/minlength check runs

  // thinking prompts in the empty box; the first one is also the HTML placeholder (site_home.py PLACEHOLDER)
  var PROMPTS = [
    'شيء تستخدمه أو تأكله أو تقوله كل يوم، ولم تسأل يومًا من أين جاء؟',
    'كلمة نردّدها، أو عادة ورثناها، أو اختراع غيّر حياتنا…',
    'مدينة، أو أكلة، أو لعبة قديمة… ما الذي يثير فضولك؟',
  ];
  // keys = site_home.py TOPICS = worker.js TOPICS (a test checks the three)
  var HINTS = {
    daily: 'مثلًا: الساعة، المفتاح، النظارة…',
    food: 'مثلًا: القهوة، الخبز، الكنافة…',
    habit: 'مثلًا: من أين جاءت كلمة «صحتين»؟',
    invention: 'مثلًا: المصعد، الإشارة الضوئية، الدرج المتحرك…',
    place: 'مثلًا: مدينة تحب أن تعرف سرّ اسمها…',
    heritage: 'مثلًا: الدلّة، الفانوس، السدو…',
    home: 'مثلًا: الثلاجة، المكنسة، الوسادة…',
    other: 'اكتب ما يخطر لك، بكلمات قليلة.',
  };
  var ERRORS = {
    empty: 'اكتب اسم الشيء أولًا.',
    length: 'اكتب اسم الشيء بكلمة أو كلمتين على الأقل.',
    personal: 'احذف الروابط أو الأرقام من النص، ثم أرسله.',
    limit: 'أرسلت اقتراحات كثيرة الآن. جرّب بعد ساعة.',
    busy: 'وصلتنا اقتراحات كثيرة اليوم. جرّب غدًا.',
    server:
      'لم يصل الاقتراح، يبدو أن الاتصال انقطع. نصّك ما زال هنا، جرّب مرة أخرى.',
    later: 'الصندوق مزدحم الآن. نصّك ما زال هنا، جرّب بعد قليل.',
  };

  // ?src= attribution (ig-bio, ig-story, yt-desc, tt-bio...): whitelisted pattern only, sent with the suggestion, never stored here
  var src = (
    new URLSearchParams(location.search).get('src') || ''
  ).toLowerCase();
  document.getElementById('ssrc').value = /^[a-z0-9-]{1,24}$/.test(src)
    ? src
    : '';

  // rotate the thinking prompts slowly while the box is empty, unfocused and no topic is chosen (never with reduced motion)
  var p = 0,
    still =
      window.matchMedia &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (!still)
    setTimeout(function () {
      setInterval(rotate, 4500);
    }, 9000);
  function rotate() {
    if (lastTopic || text.value || document.activeElement === text) return;
    p = (p + 1) % PROMPTS.length;
    text.placeholder = PROMPTS[p];
  }

  // a second tap on the chosen chip clears it (the topic is optional)
  form.addEventListener('click', function (e) {
    var r = e.target;
    if (r.name !== 'topic') return;
    if (lastTopic === r.value) {
      r.checked = false;
      lastTopic = null;
      text.placeholder = PROMPTS[p];
    } else {
      lastTopic = r.value;
      text.placeholder = HINTS[r.value] || PROMPTS[p];
    }
  });
  text.addEventListener('input', function () {
    count.textContent = text.value.length + ' / ' + MAX;
    setMsg('');
    text.removeAttribute('aria-invalid');
  });

  function setMsg(s) {
    msg.textContent = s;
  }
  function setSending(on) {
    btn.disabled = on;
    btn.classList.toggle('sending', on);
    text.readOnly = on;
    label.textContent = on ? 'جارٍ الإرسال…' : 'أرسل الاقتراح';
  }
  function send() {
    var ctrl = window.AbortController ? new AbortController() : null;
    var timer = ctrl
      ? setTimeout(function () {
          ctrl.abort();
        }, TIMEOUT_MS)
      : null;
    return fetch(form.action, {
      method: 'POST',
      body: new URLSearchParams(new FormData(form)), // application/x-www-form-urlencoded: no CORS preflight
      headers: { Accept: 'application/json' },
      credentials: 'omit',
      signal: ctrl ? ctrl.signal : undefined,
    }).then(
      function (r) {
        if (timer) clearTimeout(timer);
        return r.json().catch(function () {
          return { ok: false, code: 'server' };
        });
      },
      function (err) {
        if (timer) clearTimeout(timer);
        throw err;
      },
    );
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var v = text.value.replace(/\s+/g, ' ').trim();
    if (!v) {
      setMsg(ERRORS.empty);
      text.setAttribute('aria-invalid', 'true');
      text.focus();
      return;
    }
    if (v.length < MIN) {
      setMsg(ERRORS.length);
      text.setAttribute('aria-invalid', 'true');
      text.focus();
      return;
    }
    document.getElementById('st').value = String(Date.now() - rendered);
    setMsg('');
    setSending(true);
    send()
      .then(function (res) {
        setSending(false);
        if (res && res.ok) {
          box.classList.add('done');
          thanks.focus();
          return;
        }
        setMsg(ERRORS[res && res.code] || ERRORS.server); // the text stays in the box
        if (res && (res.code === 'personal' || res.code === 'length'))
          text.setAttribute('aria-invalid', 'true');
      })
      .catch(function () {
        setSending(false);
        setMsg(ERRORS.server);
      });
  });

  document.getElementById('sagain').addEventListener('click', function (e) {
    e.preventDefault();
    box.classList.remove('done');
    if (location.hash === '#thanks')
      history.replaceState(
        null,
        '',
        location.pathname + location.search + '#suggest',
      );
    form.reset();
    lastTopic = null;
    text.placeholder = PROMPTS[p];
    count.textContent = '0 / ' + MAX;
    setMsg('');
    rendered = Date.now();
    text.focus();
  });
})();
