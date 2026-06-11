/* Shared runtime for every page: theme toggle, mobile nav, scrollspy,
   back-to-top, reveal animations, analytics. No dependencies. */
(function () {
  'use strict';

  var root = document.documentElement;
  var THEME_KEY = 'wy-theme';
  var THEME_SOURCE_KEY = 'wy-theme-source';

  /* ---- Theme -------------------------------------------------------- */

  function currentTheme() {
    return root.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
  }

  function applyTheme(theme) {
    root.setAttribute('data-theme', theme);
    var toggle = document.querySelector('.theme-toggle');
    if (toggle) {
      toggle.setAttribute('aria-pressed', theme === 'dark' ? 'true' : 'false');
    }
    document.dispatchEvent(new CustomEvent('wy:themechange', { detail: { theme: theme } }));
  }

  function setupTheme() {
    var toggle = document.querySelector('.theme-toggle');
    if (toggle) {
      toggle.setAttribute('aria-pressed', currentTheme() === 'dark' ? 'true' : 'false');
      toggle.addEventListener('click', function () {
        var next = currentTheme() === 'dark' ? 'light' : 'dark';
        try {
          localStorage.setItem(THEME_KEY, next);
          localStorage.setItem(THEME_SOURCE_KEY, 'manual');
        } catch (error) { /* private mode */ }
        applyTheme(next);
      });
    }
    if (window.matchMedia) {
      var query = window.matchMedia('(prefers-color-scheme: dark)');
      var onSchemeChange = function (event) {
        var manual = false;
        try {
          manual = localStorage.getItem(THEME_SOURCE_KEY) === 'manual';
        } catch (error) { /* ignore */ }
        if (!manual) {
          applyTheme(event.matches ? 'dark' : 'light');
        }
      };
      if (query.addEventListener) {
        query.addEventListener('change', onSchemeChange);
      } else if (query.addListener) {
        query.addListener(onSchemeChange); // older Safari
      }
    }
  }

  /* ---- Mobile navigation --------------------------------------------- */

  function setupMenu() {
    var toggle = document.querySelector('.menu-toggle');
    var nav = document.getElementById('site-nav');
    if (!toggle || !nav) return;

    function setOpen(open) {
      nav.classList.toggle('open', open);
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    }

    toggle.addEventListener('click', function () {
      setOpen(!nav.classList.contains('open'));
    });
    nav.addEventListener('click', function (event) {
      if (event.target.closest('a')) setOpen(false);
    });
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape') setOpen(false);
    });
    document.addEventListener('click', function (event) {
      if (nav.classList.contains('open') && !event.target.closest('.nav-controls')) {
        setOpen(false);
      }
    });
  }

  /* ---- Scrollspy (home page sections) --------------------------------- */

  function setupScrollspy() {
    var links = Array.prototype.slice.call(document.querySelectorAll('.site-nav .nav-link'));
    var sections = links
      .map(function (link) {
        var hash = link.getAttribute('href') || '';
        var id = hash.indexOf('#') >= 0 ? hash.split('#')[1] : null;
        return id ? document.getElementById(id) : null;
      })
      .filter(Boolean);
    if (!sections.length || !('IntersectionObserver' in window)) return;

    var active = null;
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) active = entry.target.id;
        });
        links.forEach(function (link) {
          var href = link.getAttribute('href') || '';
          link.classList.toggle('active', !!active && href.indexOf('#' + active) >= 0);
        });
      },
      { rootMargin: '-30% 0px -60% 0px' }
    );
    sections.forEach(function (section) { observer.observe(section); });
  }

  /* ---- Back to top ------------------------------------------------------ */

  function setupBackToTop() {
    var button = document.querySelector('.back-to-top');
    if (!button) return;
    var onScroll = function () {
      button.classList.toggle('visible', window.scrollY > 480);
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
    button.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  /* ---- Reveal-on-scroll --------------------------------------------------- */

  function setupReveal() {
    var reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var targets = document.querySelectorAll('.section-header, .hero-grid, .spotlight, .panel, .controls');
    if (reduced || !('IntersectionObserver' in window)) return;
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add('in-view');
            observer.unobserve(entry.target);
          }
        });
      },
      { rootMargin: '0px 0px -8% 0px' }
    );
    Array.prototype.forEach.call(targets, function (el) {
      el.classList.add('reveal');
      observer.observe(el);
    });
  }

  /* ---- Analytics (Google Analytics 4) -------------------------------------- */

  function setupAnalytics() {
    var gaId = root.getAttribute('data-ga-id');
    if (!gaId || gaId === 'G-XXXXXXXXXX' || /^localhost$|^127\./.test(location.hostname)) return;
    var script = document.createElement('script');
    script.async = true;
    script.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(gaId);
    document.head.appendChild(script);
    window.dataLayer = window.dataLayer || [];
    function gtag() { window.dataLayer.push(arguments); }
    window.gtag = gtag;
    gtag('js', new Date());
    gtag('config', gaId);
  }

  /* ---- Boot ------------------------------------------------------------------ */

  function init() {
    // Note: papers carry data-year attributes; this must stay distinct.
    var year = document.querySelector('[data-footer-year]');
    if (year) year.textContent = String(new Date().getFullYear());
    setupTheme();
    setupMenu();
    setupScrollspy();
    setupBackToTop();
    setupReveal();
    setupAnalytics();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
