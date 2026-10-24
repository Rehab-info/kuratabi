/* 入口の旅のしおりを、目的と所要時間で絞り込む */
(function () {
  var cards = Array.prototype.slice.call(document.querySelectorAll('#kt-trips .kt-trip'));
  var count = document.getElementById('kt-count');
  var empty = document.getElementById('kt-empty');
  var tags = [], len = '';
  function apply() {
    var shown = 0;
    cards.forEach(function (c) {
      var ct = (c.getAttribute('data-tags') || '').split('|');
      var ok = tags.every(function (t) { return ct.indexOf(t) >= 0; }) && (!len || c.getAttribute('data-length') === len);
      c.hidden = !ok;
      if (ok) shown++;
    });
    count.textContent = shown + '編の旅' + (tags.length || len ? '(絞り込み中)' : '');
    empty.hidden = shown > 0;
  }
  document.addEventListener('click', function (ev) {
    var b = ev.target.closest('.kt-filter .chip');
    if (!b) return;
    var on = b.getAttribute('aria-pressed') !== 'true';
    if (b.hasAttribute('data-tag')) {
      var t = b.getAttribute('data-tag');
      tags = on ? tags.concat(t) : tags.filter(function (x) { return x !== t; });
      b.setAttribute('aria-pressed', String(on));
    } else {
      document.querySelectorAll('.kt-filter [data-len]').forEach(function (x) { x.setAttribute('aria-pressed', 'false'); });
      len = on ? b.getAttribute('data-len') : '';
      b.setAttribute('aria-pressed', String(on));
    }
    apply();
  });
  apply();
})();
