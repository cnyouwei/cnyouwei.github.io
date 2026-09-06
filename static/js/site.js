/* Shared, dependency-free enhancement; content works before this script runs. */
(function () {
  'use strict';

  var root = document.documentElement;
  var config = {};
  try { config = JSON.parse(document.getElementById('site-config').textContent); }
  catch (error) { /* Optional enhancements remain disabled without configuration. */ }

  function setupTheme() {
    var toggle = document.querySelector('.theme-toggle');
    var query = window.matchMedia('(prefers-color-scheme: dark)');
    var manual = false;
    try { manual = localStorage.getItem('wy-theme-source') === 'manual'; } catch (error) { /* Storage is optional. */ }
    function apply(theme) {
      root.setAttribute('data-theme', theme);
      if (toggle) toggle.setAttribute('aria-pressed', String(theme === 'dark'));
      document.dispatchEvent(new CustomEvent('wy:themechange', { detail: { theme: theme } }));
    }
    if (toggle) {
      toggle.hidden = false;
      toggle.setAttribute('aria-pressed', String(root.getAttribute('data-theme') === 'dark'));
      toggle.addEventListener('click', function () {
        var theme = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        manual = true;
        try {
          localStorage.setItem('wy-theme', theme);
          localStorage.setItem('wy-theme-source', 'manual');
        } catch (error) { /* Keep the preference in memory for this page. */ }
        apply(theme);
      });
    }
    query.addEventListener('change', function (event) {
      if (!manual) apply(event.matches ? 'dark' : 'light');
    });
  }

  function setupMenu() {
    var toggle = document.querySelector('.menu-toggle');
    var nav = document.getElementById('site-nav');
    if (!toggle || !nav) return;
    var media = window.matchMedia('(max-width: 760px)');
    function setOpen(open, restoreFocus) {
      nav.classList.toggle('open', open);
      toggle.setAttribute('aria-expanded', String(open));
      toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
      if (restoreFocus) toggle.focus();
    }
    toggle.addEventListener('click', function () { setOpen(!nav.classList.contains('open')); });
    nav.addEventListener('click', function (event) {
      if (event.target.closest('a')) setOpen(false);
    });
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && media.matches && nav.classList.contains('open')) {
        event.preventDefault();
        setOpen(false, true);
      }
    });
    document.addEventListener('click', function (event) {
      if (nav.classList.contains('open') && !event.target.closest('.nav-controls')) setOpen(false);
    });
    media.addEventListener('change', function () { setOpen(false); });
    toggle.hidden = false;
    toggle.closest('.nav-controls').classList.add('nav-ready');
    toggle.closest('.site-header').classList.add('header-ready');
  }

  /* Shared by section navigation and the blog TOC. Absolute heading positions
     also handle direct hash jumps and fast scrolling between distant sections. */
  function trackSections(links) {
    var pairs = Array.from(links).map(function (link) {
      if (link.pathname !== location.pathname) return null;
      var hash = link.hash;
      var target;
      try { target = hash && document.getElementById(decodeURIComponent(hash.slice(1))); }
      catch (error) { return null; }
      return target ? [target, link] : null;
    }).filter(Boolean);
    if (!pairs.length) return;
    var pending = false;
    function update() {
      pending = false;
      var header = document.querySelector('.site-header');
      var offset = (header ? header.getBoundingClientRect().height : 0) + 28;
      var current = pairs[0][1];
      pairs.forEach(function (pair) {
        if (pair[0].getBoundingClientRect().top <= offset) current = pair[1];
      });
      pairs.forEach(function (pair) {
        var active = pair[1] === current;
        pair[1].classList.toggle('active', active);
        if (active) pair[1].setAttribute('aria-current', 'location');
        else pair[1].removeAttribute('aria-current');
      });
    }
    function schedule() {
      if (!pending) { pending = true; requestAnimationFrame(update); }
    }
    window.addEventListener('scroll', schedule, { passive: true });
    window.addEventListener('resize', schedule);
    document.addEventListener('wy:layoutchange', schedule);
    update();
  }

  /* Focus only regions that actually overflow; preserve any MathJax semantics. */
  function setupScrollableRegions() {
    var originals = new WeakMap();
    var pending = false;
    function update() {
      pending = false;
      document.querySelectorAll('[data-scroll-label], div.arithmatex, mjx-container[display="true"]').forEach(function (element) {
        var overflowing = element.clientWidth > 0 && element.scrollWidth > element.clientWidth + 1;
        if (overflowing && !originals.has(element)) {
          originals.set(element, ['tabindex', 'role', 'aria-label'].map(function (name) { return element.getAttribute(name); }));
          element.tabIndex = 0;
          if (!element.hasAttribute('role')) element.setAttribute('role', 'region');
          if (!element.hasAttribute('aria-label')) element.setAttribute('aria-label', element.dataset.scrollLabel || 'Equation: scroll horizontally to explore');
        } else if (!overflowing && originals.has(element)) {
          var values = originals.get(element);
          ['tabindex', 'role', 'aria-label'].forEach(function (name, index) {
            if (values[index] === null) element.removeAttribute(name);
            else element.setAttribute(name, values[index]);
          });
          originals.delete(element);
        }
      });
    }
    function schedule() { if (!pending) { pending = true; requestAnimationFrame(update); } }
    window.addEventListener('resize', schedule);
    document.addEventListener('wy:layoutchange', schedule);
    document.fonts.addEventListener('loadingdone', schedule);
    schedule();
  }

  /* A single retryable loader and typesetting queue serve blogs and abstracts. */
  var mathEngine = null;
  var mathQueue = Promise.resolve();
  function mathConfig() {
    return {
      startup: { typeset: false },
      tex: {
        inlineMath: [['$', '$'], ['\\(', '\\)']],
        displayMath: [['$$', '$$'], ['\\[', '\\]']],
        processEscapes: true,
        macros: { bm: ['\\boldsymbol{#1}', 1] }
      },
      chtml: { mtextInheritFont: true, merrorInheritFont: true },
      options: { skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code'] }
    };
  }
  function ensureMath() {
    if (mathEngine) return mathEngine;
    var script;
    mathEngine = new Promise(function (resolve, reject) {
      if (!config.mathjax_url) { reject(new Error('MathJax URL is unavailable')); return; }
      window.MathJax = mathConfig();
      script = document.createElement('script');
      script.src = config.mathjax_url;
      script.async = true;
      script.dataset.mathjaxLoader = '';
      var completed = false;
      function finish(error, engine) {
        if (completed) return;
        completed = true;
        clearTimeout(timer);
        if (error) reject(error);
        else resolve(engine);
      }
      var timer = setTimeout(function () { finish(new Error('MathJax load timed out')); }, 15000);
      script.onerror = function () { finish(new Error('MathJax could not load')); };
      script.onload = function () {
        if (completed) return;
        var engine = window.MathJax;
        var startup = engine && engine.startup;
        if (!startup || !startup.promise) {
          finish(new Error('MathJax did not initialize'));
          return;
        }
        startup.promise.then(function () { finish(null, engine); }, function (error) { finish(error); });
      };
      document.head.appendChild(script);
    }).catch(function (error) {
      if (script) script.remove();
      mathEngine = null;
      throw error;
    });
    return mathEngine;
  }
  function typesetMath(elements) {
    mathQueue = mathQueue.catch(function () {}).then(ensureMath).then(function (math) {
      var connected = elements.filter(function (element) { return element.isConnected; });
      if (!connected.length) return;
      return math.typesetPromise(connected).then(function () {
        connected.forEach(function (element) {
          var status = element.querySelector('.math-load-status');
          if (status) status.remove();
        });
        document.dispatchEvent(new Event('wy:layoutchange'));
      });
    });
    return mathQueue;
  }
  function showMathRetry(container, elements) {
    if (container.querySelector('.math-load-status')) return;
    var status = document.createElement('div');
    status.className = 'math-load-status tex2jax_ignore';
    status.setAttribute('role', 'status');
    status.appendChild(document.createTextNode('Equations could not load.'));
    var button = document.createElement('button');
    button.type = 'button';
    button.textContent = 'Retry equations';
    button.addEventListener('click', function () {
      button.disabled = true;
      button.textContent = 'Loading equations…';
      typesetMath(elements).catch(function () {
        button.disabled = false;
        button.textContent = 'Retry equations';
      });
    });
    status.appendChild(button);
    container.prepend(status);
  }

  function setupAnalytics() {
    if (!config.ga_id || !config.production_hostname || location.protocol !== 'https:' || location.hostname !== config.production_hostname) return;
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    window.gtag('js', new Date());
    window.gtag('config', config.ga_id);
    var script = document.createElement('script');
    script.async = true;
    script.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(config.ga_id);
    document.head.appendChild(script);
  }

  window.WY = { config: config, typesetMath: typesetMath, showMathRetry: showMathRetry, trackSections: trackSections };
  setupTheme();
  setupMenu();
  setupScrollableRegions();
  trackSections(document.querySelectorAll('.site-nav .nav-link'));
  setupAnalytics();
})();
