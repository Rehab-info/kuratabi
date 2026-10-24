/* 旅のしおりの地図。蔵・駅・見どころに印を置き、全部が収まるように表示する */
(function () {
  var box = document.getElementById('kt-map');
  if (!box || !window.L || !window.KT_MARKERS) return;
  box.innerHTML = '';
  var map = L.map(box, { scrollWheelZoom: false, tap: true });
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
  }).addTo(map);
  var pts = [];
  window.KT_MARKERS.forEach(function (m) {
    var icon = L.divIcon({ className: 'kt-pin-wrap', html: '<i class="kt-pin kt-pin-' + m.t + '">' + m.label + '</i>', iconSize: [30, 30], iconAnchor: [15, 15] });
    var mk = L.marker([m.lat, m.lng], { icon: icon, title: m.name, keyboard: true }).addTo(map);
    mk.bindTooltip(m.name, { direction: 'top', offset: [0, -14] });
    if (m.t === 'spot') mk.on('click', function () { var el = document.getElementById('spot' + m.label); if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' }); });
    pts.push([m.lat, m.lng]);
  });
  map.fitBounds(pts, { padding: [36, 36], maxZoom: 16 });
})();
