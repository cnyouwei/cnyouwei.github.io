(function (window) {
  var SiteApp = window.SiteApp || {};
  var SiteUtils = window.SiteUtils;

  SiteApp.initBackToTop = function initBackToTop() {
    var backToTopLink = SiteUtils.qs('.back-to-top');
    if (!backToTopLink) return;

    SiteUtils.on(backToTopLink, 'click', function (event) {
      event.preventDefault();
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    function updateBackToTopVisibility() {
      var showThreshold = 260;
      var shouldShow = window.scrollY > showThreshold;
      backToTopLink.classList.toggle('is-visible', shouldShow);
    }

    SiteUtils.on(window, 'scroll', updateBackToTopVisibility, { passive: true });
    updateBackToTopVisibility();
  };

  window.SiteApp = SiteApp;
})(window);
