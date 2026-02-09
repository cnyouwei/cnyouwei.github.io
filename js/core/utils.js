(function (window) {
  var SiteUtils = window.SiteUtils || {};

  SiteUtils.qs = function (selector, root) {
    return (root || document).querySelector(selector);
  };

  SiteUtils.qsa = function (selector, root) {
    return Array.from((root || document).querySelectorAll(selector));
  };

  SiteUtils.on = function (target, eventName, handler, options) {
    if (!target || !target.addEventListener) return;
    target.addEventListener(eventName, handler, options || false);
  };

  SiteUtils.loadScript = function (src, attrs) {
    return new Promise(function (resolve, reject) {
      if (SiteUtils.qs('script[data-src="' + src + '"]')) {
        resolve();
        return;
      }

      var script = document.createElement('script');
      script.src = src;
      script.async = true;
      script.dataset.src = src;
      if (attrs) {
        Object.keys(attrs).forEach(function (key) {
          script.setAttribute(key, String(attrs[key]));
        });
      }
      script.onload = function () {
        resolve();
      };
      script.onerror = function () {
        reject(new Error('Failed to load script: ' + src));
      };
      document.head.appendChild(script);
    });
  };

  SiteUtils.loadStylesheet = function (href) {
    if (SiteUtils.qs('link[data-href="' + href + '"]')) return;
    var link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = href;
    link.dataset.href = href;
    document.head.appendChild(link);
  };

  window.SiteUtils = SiteUtils;
})(window);
