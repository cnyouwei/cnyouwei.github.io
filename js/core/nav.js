(function (window) {
  var SiteApp = window.SiteApp || {};
  var SiteUtils = window.SiteUtils;

  function initNavigation() {
    var menuToggle = SiteUtils.qs('.menu-toggle');
    var siteNav = SiteUtils.qs('.site-nav');

    function setMobileNavOpen(shouldOpen) {
      if (!menuToggle || !siteNav) return;
      siteNav.classList.toggle('open', shouldOpen);
      menuToggle.setAttribute('aria-expanded', shouldOpen ? 'true' : 'false');
    }

    function closeNavUi() {
      setMobileNavOpen(false);
    }

    if (menuToggle && siteNav) {
      setMobileNavOpen(false);

      SiteUtils.on(menuToggle, 'click', function () {
        var isOpen = !siteNav.classList.contains('open');
        setMobileNavOpen(isOpen);
      });

      SiteUtils.on(siteNav, 'click', function (event) {
        var target = event.target;
        if (!(target instanceof Element)) return;

        var clickedLink = target.closest('a.nav-link[href]');
        if (!clickedLink) return;

        closeNavUi();
      });

      SiteUtils.on(document, 'click', function (event) {
        var target = event.target;
        if (!(target instanceof Node)) return;
        if (!siteNav.classList.contains('open')) return;
        if (siteNav.contains(target) || menuToggle.contains(target)) return;
        closeNavUi();
      });

      SiteUtils.on(document, 'keydown', function (event) {
        if (event.key !== 'Escape') return;
        closeNavUi();
      });

      if (typeof window.matchMedia === 'function') {
        var mobileMedia = window.matchMedia('(max-width: 820px)');
        var closeWhenDesktop = function (event) {
          if (event.matches) return;
          closeNavUi();
        };
        SiteUtils.onMediaQueryChange(mobileMedia, closeWhenDesktop);
      }
    }

    return {
      closeNavUi: closeNavUi,
    };
  }

  function initSectionRouter(closeNavUi) {
    var main = SiteUtils.qs('main');
    if (!main) return;

    var sections = SiteUtils.qsa('section[id]', main);
    var navLinks = SiteUtils.qsa('.site-nav .nav-link[href^="#"]');
    if (!sections.length || !navLinks.length) return;

    var routeMap = {};
    sections.forEach(function (section) {
      routeMap['#' + section.id] = section;
    });

    var defaultHash = routeMap['#home'] ? '#home' : '#' + sections[0].id;

    function normalizeHash(hash) {
      if (!hash || hash === '#') return defaultHash;
      return routeMap[hash] ? hash : defaultHash;
    }

    function replaceHash(hash) {
      if (window.location.hash === hash) return;

      if (window.history && typeof window.history.replaceState === 'function') {
        var nextUrl = window.location.pathname + window.location.search + hash;
        window.history.replaceState(null, '', nextUrl);
        return;
      }

      window.location.hash = hash;
    }

    function setActiveSection(hash) {
      sections.forEach(function (section) {
        var isActive = '#' + section.id === hash;
        section.classList.toggle('is-route-active', isActive);
      });
    }

    function setActiveNavLink(hash) {
      navLinks.forEach(function (link) {
        var isActive = link.getAttribute('href') === hash;
        link.classList.toggle('is-active', isActive);
        if (isActive) {
          link.setAttribute('aria-current', 'page');
        } else {
          link.removeAttribute('aria-current');
        }
      });
    }

    function applyRoute(rawHash, options) {
      var opts = options || {};
      var resolvedHash = normalizeHash(rawHash);
      var shouldNormalize = rawHash !== resolvedHash;

      document.documentElement.classList.add('single-section-mode');
      setActiveSection(resolvedHash);
      setActiveNavLink(resolvedHash);

      if (shouldNormalize) {
        replaceHash(resolvedHash);
      }

      if (!opts.keepScrollPosition && typeof window.scrollTo === 'function') {
        window.scrollTo({ top: 0, left: 0, behavior: 'auto' });
      }

      if (opts.closeNavUi !== false && typeof closeNavUi === 'function') {
        closeNavUi();
      }
    }

    applyRoute(window.location.hash, {
      keepScrollPosition: false,
      closeNavUi: false,
    });

    SiteUtils.on(window, 'hashchange', function () {
      applyRoute(window.location.hash);
    });
  }

  SiteApp.initNav = function initNav() {
    var navApi = initNavigation();
    initSectionRouter(navApi && navApi.closeNavUi);
  };

  window.SiteApp = SiteApp;
})(window);
