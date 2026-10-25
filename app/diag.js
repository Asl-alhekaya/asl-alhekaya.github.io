'use strict';
// Shows script errors and blocked resources on screen, so a blank Mini App says why.
(function () {
  
  function say(t) { var box = document.getElementById('diag'); if (box) { box.hidden = false; box.textContent += t + '\n'; } }
  window.addEventListener('error', function (e) { say('خطأ: ' + (e.message || e.target && e.target.src || '?')); }, true);
  window.addEventListener('securitypolicyviolation', function (e) { say('محجوب: ' + e.blockedURI + ' (' + e.violatedDirective + ')'); });
  window.addEventListener('unhandledrejection', function (e) { say('وعد مرفوض: ' + (e.reason && e.reason.message || e.reason)); });
})();
