/* Progressive reading enhancements. Source text survives unavailable services. */
(function () {
  'use strict';
  var site = window.WY;
  if (!site) return;
  var body = document.querySelector('.post-body');
  if (!body) return;
  var config = site.config;

  function setupCopyButtons() {
    if (!navigator.clipboard) return;
    body.querySelectorAll('pre:not(.mermaid)').forEach(function (pre) {
      var code = pre.querySelector('code');
      if (!code) return;
      var button = document.createElement('button');
      button.type = 'button';
      button.className = 'copy-button';
      button.textContent = 'Copy';
      button.setAttribute('aria-label', 'Copy code to clipboard');
      var announcement = document.createElement('span');
      announcement.className = 'sr-only';
      announcement.setAttribute('role', 'status');
      var timer;
      button.addEventListener('click', function () {
        navigator.clipboard.writeText(code.textContent || '').then(function () {
          button.textContent = 'Copied';
          announcement.textContent = 'Code copied to clipboard.';
        }, function () {
          button.textContent = 'Try again';
          announcement.textContent = 'Copy failed. Select and copy the code manually.';
        }).then(function () {
          clearTimeout(timer);
          timer = setTimeout(function () { button.textContent = 'Copy'; announcement.textContent = ''; }, 2000);
        });
      });
      pre.append(button, announcement);
    });
  }

  function setupToc() {
    var toc = document.querySelector('.post-toc');
    if (!toc) return;
    var wide = window.matchMedia('(min-width: 881px)');
    function updateLayout() { toc.open = wide.matches; }
    updateLayout();
    wide.addEventListener('change', updateLayout);
    site.trackSections(toc.querySelectorAll('a'));
  }

  function loadStyle(url) {
    return new Promise(function (resolve, reject) {
      var link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = url;
      var timer = setTimeout(function () { reject(new Error('Stylesheet load timed out')); }, 15000);
      link.onload = function () { clearTimeout(timer); resolve(); };
      link.onerror = function () { clearTimeout(timer); reject(new Error('Stylesheet could not load')); };
      document.head.appendChild(link);
    });
  }
  function loadScript(url) {
    return new Promise(function (resolve, reject) {
      var script = document.createElement('script');
      script.src = url;
      script.async = true;
      var timer = setTimeout(function () { reject(new Error('Script load timed out')); }, 15000);
      script.onload = function () { clearTimeout(timer); resolve(); };
      script.onerror = function () { clearTimeout(timer); reject(new Error('Script could not load')); };
      document.head.appendChild(script);
    });
  }

  function setupMermaid() {
    var blocks = Array.from(body.querySelectorAll('pre.mermaid'));
    if (!blocks.length || !config.mermaid_url) return Promise.resolve();
    blocks.forEach(function (block, index) {
      block.tabIndex = 0;
      block.setAttribute('role', 'region');
      block.setAttribute('aria-label', 'Diagram ' + (index + 1) + ': scroll horizontally to explore');
      block.setAttribute('aria-busy', 'true');
    });
    var sources = new Map(blocks.map(function (block) { return [block, block.textContent]; }));
    return import(config.mermaid_url).then(function (module) {
      var mermaid = module.default;
      var queue = Promise.resolve();
      function render() {
        queue = queue.catch(function () {}).then(function () {
          mermaid.initialize({
            startOnLoad: false,
            theme: document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'default',
            securityLevel: 'strict'
          });
          blocks.forEach(function (block) {
            block.setAttribute('aria-busy', 'true');
            block.removeAttribute('data-processed');
            block.textContent = sources.get(block);
          });
          return mermaid.run({ nodes: blocks });
        }).then(function () {
          blocks.forEach(function (block) { block.setAttribute('aria-busy', 'false'); });
          document.dispatchEvent(new Event('wy:layoutchange'));
        });
        return queue;
      }
      document.addEventListener('wy:themechange', function () { render().catch(restoreSources); });
      return render();
    }).catch(restoreSources);
    function restoreSources() {
      blocks.forEach(function (block) {
        block.textContent = sources.get(block);
        block.removeAttribute('data-processed');
        block.setAttribute('aria-busy', 'false');
      });
    }
  }

  function setupHighlight() {
    var blocks = Array.from(body.querySelectorAll('pre code[class*="language-"]'));
    if (!blocks.length || !config.hljs_base_url) return Promise.resolve();
    var base = config.hljs_base_url;
    return Promise.all([
      loadStyle(base + 'styles/github-dark-dimmed.min.css'),
      loadScript(base + 'highlight.min.js')
    ]).then(function () {
      var needsLatex = blocks.some(function (block) { return /language-(latex|tex)\b/.test(block.className); });
      return needsLatex ? loadScript(base + 'languages/latex.min.js').catch(function () {}) : undefined;
    }).then(function () {
      if (!window.hljs) return;
      blocks.forEach(function (block) {
        var match = /language-([\w-]+)/.exec(block.className);
        if (match && window.hljs.getLanguage(match[1])) window.hljs.highlightElement(block);
      });
      document.dispatchEvent(new Event('wy:layoutchange'));
    }).catch(function () { /* Code remains readable and copyable. */ });
  }

  /* Correct the initial deep link once assets settle, only while the reader
     has not expressed navigation intent. Never pull a reader back mid-scroll. */
  var initialHash = location.hash;
  var interacted = false;
  function markInteraction() { interacted = true; }
  ['wheel', 'touchstart', 'pointerdown', 'keydown'].forEach(function (type) {
    window.addEventListener(type, markInteraction, { passive: true, once: true });
  });
  function settleInitialAnchor() {
    if (interacted || !initialHash || location.hash !== initialHash) return;
    var target;
    try { target = document.getElementById(decodeURIComponent(initialHash.slice(1))); }
    catch (error) { return; }
    if (target) target.scrollIntoView({ behavior: 'instant' });
  }

  setupCopyButtons();
  setupToc();
  var math = body.querySelector('.arithmatex') ? site.typesetMath([body]).catch(function () {
    site.showMathRetry(body, [body]);
  }) : Promise.resolve();
  Promise.allSettled([math, setupMermaid(), setupHighlight(), document.fonts.ready])
    .then(settleInitialAnchor);
})();
