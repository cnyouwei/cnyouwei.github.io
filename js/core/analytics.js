(function (window) {
  var SiteApp = window.SiteApp || {};
  var SiteUtils = window.SiteUtils;

  SiteApp.initAnalytics = function initAnalytics() {
    function readGaMeasurementId() {
      var root = document.documentElement;
      if (!root) return '';
      return (root.dataset.gaId || '').trim();
    }

    function isValidGaMeasurementId(value) {
      if (!value) return false;
      if (value.toUpperCase() === 'G-XXXXXXXXXX') return false;
      return /^G-[A-Z0-9]+$/i.test(value);
    }

    function setupAnalytics() {
      var gaId = readGaMeasurementId();
      if (!isValidGaMeasurementId(gaId)) return '';

      window.dataLayer = window.dataLayer || [];

      if (typeof window.gtag !== 'function') {
        window.gtag = function () {
          window.dataLayer.push(arguments);
        };
      }

      if (window.__GA_TRACKING_ID__ !== gaId) {
        window.gtag('js', new Date());
        window.gtag('config', gaId, { send_page_view: true });
        window.__GA_TRACKING_ID__ = gaId;
      }

      if (!SiteUtils.qs('script[data-ga-loader="true"]')) {
        var script = document.createElement('script');
        script.async = true;
        script.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(gaId);
        script.dataset.gaLoader = 'true';
        document.head.appendChild(script);
      }

      return gaId;
    }

    function getLinkTrackingSection(link) {
      var sectionNode = link.closest('[id], section, article, header, footer, nav');
      if (!sectionNode) return 'unknown';
      if (sectionNode.id) return sectionNode.id;
      return sectionNode.tagName.toLowerCase();
    }

    function normalizeTrackingText(value) {
      return String(value || '')
        .replace(/\s+/g, ' ')
        .trim();
    }

    function trackLinkClick(link) {
      if (typeof window.gtag !== 'function') return;

      var href = normalizeTrackingText(link.getAttribute('href'));
      if (!href || href.toLowerCase().startsWith('javascript:')) return;

      var resolvedUrl = null;
      try {
        resolvedUrl = new URL(link.href, window.location.href);
      } catch (error) {
        resolvedUrl = null;
      }

      var linkText = normalizeTrackingText(link.dataset.analyticsLabel || link.textContent);
      var isExternal = resolvedUrl
        ? resolvedUrl.origin !== window.location.origin
        : /^https?:\/\//i.test(href);

      window.gtag('event', 'link_click', {
        link_url: resolvedUrl ? resolvedUrl.href : href,
        link_text: linkText || '(no text)',
        link_type: isExternal ? 'external' : 'internal',
        link_host: resolvedUrl ? resolvedUrl.host : '',
        link_path: resolvedUrl ? resolvedUrl.pathname + resolvedUrl.search + resolvedUrl.hash : href,
        page_path: window.location.pathname,
        section: getLinkTrackingSection(link),
      });
    }

    var analyticsMeasurementId = setupAnalytics();
    if (!analyticsMeasurementId) return;

    SiteUtils.on(document, 'click', function (event) {
      if (event.defaultPrevented) return;
      if (event instanceof MouseEvent && event.button !== 0) return;

      var target = event.target;
      if (!(target instanceof Element)) return;

      var link = target.closest('a[href]');
      if (!link) return;
      trackLinkClick(link);
    });
  };

  window.SiteApp = SiteApp;
})(window);
