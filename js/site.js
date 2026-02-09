(function (window) {
  var SiteApp = window.SiteApp || {};
  var yearNode = document.getElementById('year');
  if (yearNode) yearNode.textContent = String(new Date().getFullYear());

  [
    'initTheme',
    'initNav',
    'initAnalytics',
    'initBackToTop',
    'initResearch',
    'initBlog',
  ].forEach(function (name) {
    if (typeof SiteApp[name] === 'function') {
      SiteApp[name]();
    }
  });
})(window);
