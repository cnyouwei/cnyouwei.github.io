/*
 * Site runtime shared by every page.
 *
 * Exposes two small globals for the per-page scripts in js/pages/:
 *   - SiteUtils: DOM/network helpers (qs, qsa, on, loadScript, ...)
 *   - SiteTheme: the active light/dark theme + a `themechange` event
 *
 * Loaded with `defer` before any page script, so the DOM is parsed and the
 * globals exist by the time research.js / blog_post.js run.
 */
(function (window) {
  var document = window.document;

  /* ---------------------------------------------------------------- utils */

  var SiteUtils = {
    qs: function (selector, root) {
      return (root || document).querySelector(selector);
    },
    qsa: function (selector, root) {
      return Array.prototype.slice.call((root || document).querySelectorAll(selector));
    },
    on: function (target, eventName, handler, options) {
      if (target && target.addEventListener) {
        target.addEventListener(eventName, handler, options || false);
      }
    },
    onMediaQueryChange: function (query, handler) {
      if (!query || typeof handler !== 'function') return;
      if (typeof query.addEventListener === 'function') {
        query.addEventListener('change', handler);
      } else if (typeof query.addListener === 'function') {
        query.addListener(handler);
      }
    },
    copyTextToClipboard: function (text) {
      if (navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
        return navigator.clipboard.writeText(text);
      }
      return new Promise(function (resolve, reject) {
        var textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.setAttribute('readonly', '');
        textArea.style.position = 'fixed';
        textArea.style.top = '-9999px';
        document.body.appendChild(textArea);
        textArea.select();
        try {
          if (document.execCommand('copy')) resolve();
          else reject(new Error('Copy command failed'));
        } catch (error) {
          reject(error);
        } finally {
          textArea.remove();
        }
      });
    },
    loadScript: function (src, attrs) {
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
        script.onload = function () { resolve(); };
        script.onerror = function () { reject(new Error('Failed to load script: ' + src)); };
        document.head.appendChild(script);
      });
    },
    loadStylesheet: function (href) {
      if (SiteUtils.qs('link[data-href="' + href + '"]')) return;
      var link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = href;
      link.dataset.href = href;
      document.head.appendChild(link);
    },
  };

  /* ---------------------------------------------------------------- theme */

  // Two themes only: a toggle, not a cycle. `data-theme` is set early by the
  // inline bootstrap in <head> to avoid a flash; this module owns it afterward.
  var root = document.documentElement;
  var THEME_KEY = 'wy-theme';
  var SOURCE_KEY = 'wy-theme-source';

  function systemTheme() {
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
      ? 'dark'
      : 'light';
  }

  function resolveActiveTheme() {
    var current = root.getAttribute('data-theme');
    return current === 'light' || current === 'dark' ? current : systemTheme();
  }

  function resolveThemeFromEvent(event) {
    var theme = event && event.detail ? event.detail.theme : '';
    return theme === 'light' || theme === 'dark' ? theme : resolveActiveTheme();
  }

  var SiteTheme = {
    resolveActiveTheme: resolveActiveTheme,
    resolveThemeFromEvent: resolveThemeFromEvent,
  };

  function readStored(key) {
    try {
      return window.localStorage.getItem(key) || '';
    } catch (error) {
      return '';
    }
  }

  function initTheme() {
    var toggle = SiteUtils.qs('.theme-toggle');
    var TRANSITION_CLASS = 'theme-transitioning';
    var transitionTimer = 0;
    var source = readStored(SOURCE_KEY) === 'manual' ? 'manual' : 'system';
    var stored = readStored(THEME_KEY);
    var activeTheme =
      source === 'manual' && (stored === 'light' || stored === 'dark') ? stored : systemTheme();

    function persist() {
      try {
        if (source === 'manual') window.localStorage.setItem(THEME_KEY, activeTheme);
        else window.localStorage.removeItem(THEME_KEY);
        window.localStorage.setItem(SOURCE_KEY, source);
      } catch (error) {
        /* ignore storage failures */
      }
    }

    function runTransition() {
      if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
      if (transitionTimer) window.clearTimeout(transitionTimer);
      root.classList.add(TRANSITION_CLASS);
      transitionTimer = window.setTimeout(function () {
        root.classList.remove(TRANSITION_CLASS);
      }, 240);
    }

    function updateToggle() {
      if (!toggle) return;
      var isDark = activeTheme === 'dark';
      var nextLabel = isDark ? 'Light' : 'Dark';
      toggle.setAttribute('aria-pressed', isDark ? 'true' : 'false');
      toggle.setAttribute('aria-label', 'Switch to ' + nextLabel + ' theme');
      toggle.setAttribute('title', 'Switch to ' + nextLabel + ' theme');
      toggle.setAttribute('data-active-icon', isDark ? 'moon' : 'sun');
      var textNode = toggle.querySelector('.theme-toggle__text');
      if (textNode) textNode.textContent = 'Switch to ' + nextLabel + ' theme';
    }

    function apply(theme, nextSource, animate) {
      if (animate && theme !== activeTheme) runTransition();
      activeTheme = theme === 'light' || theme === 'dark' ? theme : systemTheme();
      source = nextSource === 'manual' ? 'manual' : 'system';
      root.setAttribute('data-theme', activeTheme);
      persist();
      updateToggle();
      window.dispatchEvent(new CustomEvent('themechange', { detail: { theme: activeTheme } }));
    }

    apply(activeTheme, source, false);

    SiteUtils.on(toggle, 'click', function () {
      apply(activeTheme === 'dark' ? 'light' : 'dark', 'manual', true);
    });

    var query = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;
    SiteUtils.onMediaQueryChange(query, function () {
      if (source !== 'manual') apply(systemTheme(), 'system', true);
    });
  }

  /* ------------------------------------------------------------------ nav */

  function initNav() {
    var menuToggle = SiteUtils.qs('.menu-toggle');
    var siteNav = SiteUtils.qs('.site-nav');

    function setMenuOpen(open) {
      if (!menuToggle || !siteNav) return;
      siteNav.classList.toggle('open', open);
      menuToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    }

    if (menuToggle && siteNav) {
      setMenuOpen(false);
      SiteUtils.on(menuToggle, 'click', function () {
        setMenuOpen(!siteNav.classList.contains('open'));
      });
      SiteUtils.on(siteNav, 'click', function (event) {
        if (event.target instanceof Element && event.target.closest('a.nav-link[href]')) {
          setMenuOpen(false);
        }
      });
      SiteUtils.on(document, 'click', function (event) {
        if (!siteNav.classList.contains('open')) return;
        var target = event.target;
        if (target instanceof Node && !siteNav.contains(target) && !menuToggle.contains(target)) {
          setMenuOpen(false);
        }
      });
      SiteUtils.on(document, 'keydown', function (event) {
        if (event.key === 'Escape') setMenuOpen(false);
      });
      if (window.matchMedia) {
        SiteUtils.onMediaQueryChange(window.matchMedia('(max-width: 820px)'), function (event) {
          if (!event.matches) setMenuOpen(false);
        });
      }
    }

    initSectionRouter(function () { setMenuOpen(false); });
  }

  // The home page renders every section but shows one at a time, driven by the
  // URL hash (#research, #blog, ...). Subpages have no #section nav links, so
  // this is a no-op there.
  function initSectionRouter(closeMenu) {
    var main = SiteUtils.qs('main');
    if (!main) return;
    var sections = SiteUtils.qsa('section[id]', main);
    var navLinks = SiteUtils.qsa('.site-nav .nav-link[href^="#"]');
    if (!sections.length || !navLinks.length) return;

    var routes = {};
    sections.forEach(function (section) { routes['#' + section.id] = true; });
    var defaultHash = routes['#home'] ? '#home' : '#' + sections[0].id;

    function applyRoute(rawHash, keepScroll) {
      var hash = routes[rawHash] ? rawHash : defaultHash;
      root.classList.add('single-section-mode');
      sections.forEach(function (section) {
        section.classList.toggle('is-route-active', '#' + section.id === hash);
      });
      navLinks.forEach(function (link) {
        var active = link.getAttribute('href') === hash;
        link.classList.toggle('is-active', active);
        if (active) link.setAttribute('aria-current', 'page');
        else link.removeAttribute('aria-current');
      });
      if (rawHash !== hash && window.history && window.history.replaceState) {
        window.history.replaceState(null, '', window.location.pathname + window.location.search + hash);
      }
      if (!keepScroll && window.scrollTo) window.scrollTo({ top: 0, left: 0, behavior: 'auto' });
    }

    applyRoute(window.location.hash, false);
    SiteUtils.on(window, 'hashchange', function () {
      applyRoute(window.location.hash, false);
      if (typeof closeMenu === 'function') closeMenu();
    });
  }

  /* ------------------------------------------------------------ analytics */

  function initAnalytics() {
    var gaId = (root.dataset.gaId || '').trim();
    if (!gaId || gaId.toUpperCase() === 'G-XXXXXXXXXX' || !/^G-[A-Z0-9]+$/i.test(gaId)) return;

    window.dataLayer = window.dataLayer || [];
    if (typeof window.gtag !== 'function') {
      window.gtag = function () { window.dataLayer.push(arguments); };
    }
    window.gtag('js', new Date());
    window.gtag('config', gaId, { send_page_view: true });

    if (!SiteUtils.qs('script[data-ga-loader="true"]')) {
      var script = document.createElement('script');
      script.async = true;
      script.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(gaId);
      script.dataset.gaLoader = 'true';
      document.head.appendChild(script);
    }

    function clean(value) {
      return String(value || '').replace(/\s+/g, ' ').trim();
    }

    SiteUtils.on(document, 'click', function (event) {
      if (event.defaultPrevented || (event instanceof MouseEvent && event.button !== 0)) return;
      var target = event.target;
      if (!(target instanceof Element)) return;
      var link = target.closest('a[href]');
      if (!link) return;

      var href = clean(link.getAttribute('href'));
      if (!href || href.toLowerCase().indexOf('javascript:') === 0) return;

      var url = null;
      try { url = new URL(link.href, window.location.href); } catch (error) { url = null; }
      var section = link.closest('[id], section, article, header, footer, nav');

      window.gtag('event', 'link_click', {
        link_url: url ? url.href : href,
        link_text: clean(link.dataset.analyticsLabel || link.textContent) || '(no text)',
        link_type: (url ? url.origin !== window.location.origin : /^https?:\/\//i.test(href))
          ? 'external'
          : 'internal',
        link_host: url ? url.host : '',
        link_path: url ? url.pathname + url.search + url.hash : href,
        page_path: window.location.pathname,
        section: section ? section.id || section.tagName.toLowerCase() : 'unknown',
      });
    });
  }

  /* ----------------------------------------------------------- back to top */

  function initBackToTop() {
    var button = SiteUtils.qs('.back-to-top');
    if (!button) return;
    SiteUtils.on(button, 'click', function (event) {
      event.preventDefault();
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
    function update() {
      button.classList.toggle('is-visible', window.scrollY > 260);
    }
    SiteUtils.on(window, 'scroll', update, { passive: true });
    update();
  }

  /* -------------------------------------------------------------- bootstrap */

  window.SiteUtils = SiteUtils;
  window.SiteTheme = SiteTheme;

  var yearNode = document.getElementById('year');
  if (yearNode) yearNode.textContent = String(new Date().getFullYear());

  initTheme();
  initNav();
  initAnalytics();
  initBackToTop();
})(window);
