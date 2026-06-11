/* Blog post enhancements: copy buttons on code blocks, active-TOC highlight,
   lazy Mermaid diagrams (theme-aware), lazy highlight.js syntax colors. */
(function () {
  'use strict';

  /* ---- Copy buttons ---------------------------------------------------- */

  function setupCopyButtons() {
    if (!navigator.clipboard) return; // insecure context (e.g. http preview)
    document.querySelectorAll('.post-body pre').forEach(function (pre) {
      if (pre.classList.contains('mermaid')) return;
      var code = pre.querySelector('code');
      if (!code) return;
      var button = document.createElement('button');
      button.type = 'button';
      button.className = 'copy-button';
      button.textContent = 'Copy';
      button.setAttribute('aria-label', 'Copy code to clipboard');
      button.addEventListener('click', function () {
        navigator.clipboard.writeText(code.textContent || '').then(
          function () {
            button.textContent = 'Copied';
            setTimeout(function () { button.textContent = 'Copy'; }, 1600);
          },
          function () {
            button.textContent = 'Failed';
            setTimeout(function () { button.textContent = 'Copy'; }, 1600);
          }
        );
      });
      pre.appendChild(button);
    });
  }

  /* ---- Active TOC highlight ------------------------------------------- */

  function setupToc() {
    var links = document.querySelectorAll('.post-toc__item a');
    if (!links.length) return;
    var pairs = [];
    links.forEach(function (link) {
      var heading = document.getElementById((link.getAttribute('href') || '').slice(1));
      if (heading) pairs.push([heading, link]);
    });
    if (!pairs.length) return;
    // "Last heading at or above the reading line" — recomputed from absolute
    // positions each frame, so instant jumps (hash links, reduced motion) and
    // fast scrolling cannot leave a stale highlight.
    var OFFSET = 96; /* header (64) + scroll-margin (16) + slack */
    var ticking = false;
    function update() {
      ticking = false;
      var current = null;
      pairs.forEach(function (pair) {
        if (pair[0].getBoundingClientRect().top <= OFFSET) current = pair[1];
      });
      links.forEach(function (link) { link.classList.remove('active'); });
      if (current) current.classList.add('active');
    }
    window.addEventListener('scroll', function () {
      if (!ticking) { ticking = true; requestAnimationFrame(update); }
    }, { passive: true });
    update();
  }

  /* ---- Anchor restore after lazy reflow -------------------------------- */

  /* The browser does the #hash jump on initial layout, before MathJax and
     the lazy highlight.js / Mermaid assets arrive; when those reflow content
     above the anchor the heading drifts out of view while scrollY stays
     fixed. Re-align the target each time a late asset settles. 'instant'
     overrides the page's smooth scroll-behavior — an animated correction
     would race the remaining reflows. */
  function restoreAnchor() {
    if (!location.hash) return;
    var target;
    try {
      target = document.getElementById(decodeURIComponent(location.hash.slice(1)));
    } catch (e) {
      return; // malformed percent-encoding in the hash
    }
    if (target) target.scrollIntoView({ behavior: 'instant' });
  }

  /* ---- Mermaid (lazy, theme-aware) --------------------------------------- */

  function setupMermaid() {
    var blocks = document.querySelectorAll('pre.mermaid');
    if (!blocks.length) return;
    // Keep each diagram's source: mermaid replaces the element content with
    // SVG, and we re-render from source when the theme toggles.
    var sources = new Map();
    blocks.forEach(function (block) { sources.set(block, block.textContent); });
    // KaTeX styles for $$...$$ math inside diagram labels (rendered by
    // mermaid's KaTeX integration, which requires the ESM build). Mermaid
    // must not measure labels before this stylesheet applies, or the math
    // spans end up wider than the boxes sized for them.
    var css = document.createElement('link');
    css.rel = 'stylesheet';
    css.href = 'https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css';
    var cssReady = new Promise(function (done) {
      css.onload = done;
      css.onerror = done;
      setTimeout(done, 2000); // fallback so a CDN hiccup can't block rendering
    });
    document.head.appendChild(css);
    var importModule;
    try {
      // Indirect dynamic import: keeps this file parseable on old browsers.
      importModule = new Function('url', 'return import(url)');
    } catch (error) {
      return; // no dynamic import support; the diagram stays as source text
    }
    Promise.all([
      importModule('https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs'),
      cssReady
    ])
      .then(function (loaded) {
        var mod = loaded[0];
        var mermaid = mod.default;
        function render() {
          var dark = document.documentElement.getAttribute('data-theme') === 'dark';
          mermaid.initialize({
            startOnLoad: false,
            theme: dark ? 'dark' : 'default',
            securityLevel: 'loose',
            // Render label math with KaTeX's HTML output (we ship its CSS):
            // browser MathML Core drops \mathbb / \mathcal styling.
            forceLegacyMathML: true
          });
          blocks.forEach(function (block) {
            block.removeAttribute('data-processed');
            block.textContent = sources.get(block);
          });
          return mermaid.run({ nodes: blocks });
        }
        var run = render();
        if (run && run.then) run.then(restoreAnchor);
        document.addEventListener('wy:themechange', render);
      })
      .catch(function () { /* CDN unavailable; leave the source text visible */ });
  }

  /* ---- Syntax highlighting (lazy highlight.js) ------------------------------ */

  var HLJS_CDN = 'https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/';

  function loadScript(src, onload) {
    var script = document.createElement('script');
    script.src = src;
    script.async = true;
    script.onload = onload;
    document.head.appendChild(script);
  }

  function setupHighlight() {
    var blocks = document.querySelectorAll('.post-body pre code[class*="language-"]');
    if (!blocks.length) return;
    var css = document.createElement('link');
    css.rel = 'stylesheet';
    css.href = HLJS_CDN + 'styles/github-dark-dimmed.min.css';
    css.onload = restoreAnchor;
    document.head.appendChild(css);
    loadScript(HLJS_CDN + 'highlight.min.js', function () {
      // LaTeX is not in the common bundle; load it before highlighting.
      loadScript(HLJS_CDN + 'languages/latex.min.js', function () {
        blocks.forEach(function (block) {
          var match = /language-([\w-]+)/.exec(block.className);
          // Skip languages hljs doesn't know (e.g. mermaid, bibtex).
          if (match && window.hljs.getLanguage(match[1])) {
            window.hljs.highlightElement(block);
          }
        });
        restoreAnchor();
      });
    });
  }

  function init() {
    setupCopyButtons();
    setupToc();
    setupMermaid();
    setupHighlight();
    // MathJax typesetting is the largest late reflow on math-heavy posts.
    if (window.MathJax && window.MathJax.startup && window.MathJax.startup.promise) {
      window.MathJax.startup.promise.then(restoreAnchor);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
