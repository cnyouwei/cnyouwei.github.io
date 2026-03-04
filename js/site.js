(function (window) {
  var SiteApp = window.SiteApp || {};
  var root = document.documentElement;
  var pageId = root ? (root.getAttribute('data-page') || '').trim() : '';
  var yearNode = document.getElementById('year');
  if (yearNode) yearNode.textContent = String(new Date().getFullYear());

  var coreInitializers = [
    'initTheme',
    'initNav',
    'initAnalytics',
    'initBackToTop',
  ];
  var pageInitializers = {
    home: ['initResearch'],
    'blog-post': ['initBlogPost'],
    'teaching-course': [],
  };

  function runInitializers(names) {
    names.forEach(function (name) {
      if (typeof SiteApp[name] === 'function') {
        SiteApp[name]();
      }
    });
  }

  runInitializers(coreInitializers);
  runInitializers(pageInitializers[pageId] || []);

  // Optional in case generated/static pages define additional page hooks.
  ['initPage'].forEach(function (name) {
    if (typeof SiteApp[name] === 'function') {
      SiteApp[name]();
    }
  });
})(window);
