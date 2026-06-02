(function (window) {
  var SiteUtils = window.SiteUtils;
  var SiteTheme = window.SiteTheme;

  function activeTheme() {
    return SiteTheme ? SiteTheme.resolveActiveTheme() : 'light';
  }

  function eventTheme(event) {
    return SiteTheme ? SiteTheme.resolveThemeFromEvent(event) : activeTheme();
  }

  function initCodeCopyButtons() {
    var codeBlocks = SiteUtils.qsa('.post-body pre:not(.mermaid) > code');
    if (!codeBlocks.length) return;

    codeBlocks.forEach(function (codeBlock) {
      var pre = codeBlock.parentElement;
      if (!(pre instanceof HTMLElement)) return;
      if (pre.querySelector('.code-copy-btn')) return;

      var button = document.createElement('button');
      button.type = 'button';
      button.className = 'code-copy-btn';
      button.textContent = 'Copy';
      button.setAttribute('aria-label', 'Copy code to clipboard');

      var resetTimer = 0;

      function setButtonState(label, stateClass) {
        button.textContent = label;
        button.classList.remove('is-copied', 'is-failed');
        if (stateClass) button.classList.add(stateClass);
        if (resetTimer) window.clearTimeout(resetTimer);
        resetTimer = window.setTimeout(function () {
          button.textContent = 'Copy';
          button.classList.remove('is-copied', 'is-failed');
        }, 1600);
      }

      SiteUtils.on(button, 'click', function () {
        var source = codeBlock.textContent || '';
        var copyPromise =
          typeof SiteUtils.copyTextToClipboard === 'function'
            ? SiteUtils.copyTextToClipboard(source)
            : Promise.reject(new Error('Clipboard helper unavailable'));
        copyPromise
          .then(function () {
            setButtonState('Copied', 'is-copied');
          })
          .catch(function () {
            setButtonState('Failed', 'is-failed');
          });
      });

      pre.appendChild(button);
    });
  }

  function initPostTocScrollSpy() {
    var tocNav = SiteUtils.qs('.post-toc__nav');
    var tocLinks = SiteUtils.qsa('.post-toc__link[href^="#"]');
    var tocTargets = tocLinks
      .map(function (link) {
        var href = link.getAttribute('href');
        if (!href || href.charAt(0) !== '#') return null;
        var id = href.slice(1);
        if (!id) return null;
        return document.getElementById(id);
      })
      .filter(Boolean);

    if (!tocLinks.length || !tocTargets.length) return;

    var tocGroupByHash = {};
    var tocGroups = [];
    var activeGroupIndex = -1;
    var hoveredGroupIndex = -1;

    if (tocNav instanceof HTMLElement) {
      var currentGroup = null;

      SiteUtils.qsa('.post-toc__item', tocNav).forEach(function (item) {
        var link = item.querySelector('.post-toc__link[href^="#"]');
        if (!(link instanceof HTMLAnchorElement)) return;

        var hash = link.getAttribute('href') || '';
        if (!hash) return;

        if (item.classList.contains('post-toc__item--sub')) {
          if (!currentGroup) return;
          item.dataset.tocGroup = String(currentGroup.index);
          currentGroup.subItems.push(item);
          tocGroupByHash[hash] = currentGroup.index;
          return;
        }

        var nextGroup = {
          index: tocGroups.length,
          parentItem: item,
          subItems: [],
        };
        item.dataset.tocGroup = String(nextGroup.index);
        tocGroupByHash[hash] = nextGroup.index;
        tocGroups.push(nextGroup);
        currentGroup = nextGroup;
      });
    }

    var hasSubHeadings = tocGroups.some(function (group) {
      return group.subItems.length > 0;
    });

    function syncExpandedGroups() {
      if (!hasSubHeadings) return;
      tocGroups.forEach(function (group) {
        var expanded = group.index === activeGroupIndex || group.index === hoveredGroupIndex;
        group.parentItem.classList.toggle('is-expanded', expanded);
        group.subItems.forEach(function (item) {
          item.classList.toggle('is-expanded', expanded);
        });
      });
    }

    function setActiveGroup(hash) {
      if (!hasSubHeadings) return;
      var nextGroupIndex = -1;
      if (Object.prototype.hasOwnProperty.call(tocGroupByHash, hash)) {
        nextGroupIndex = tocGroupByHash[hash];
      }
      if (nextGroupIndex === activeGroupIndex) return;
      activeGroupIndex = nextGroupIndex;
      syncExpandedGroups();
    }

    function setActiveTocLink(hash) {
      tocLinks.forEach(function (link) {
        var isActive = link.getAttribute('href') === hash;
        link.classList.toggle('is-active', isActive);
        if (isActive) {
          link.setAttribute('aria-current', 'true');
        } else {
          link.removeAttribute('aria-current');
        }
      });
      setActiveGroup(hash);
    }

    function getBestVisibleHeadingId() {
      var marker = 120;
      var candidate = null;

      tocTargets.forEach(function (target) {
        var rect = target.getBoundingClientRect();
        if (rect.top <= marker) {
          candidate = target;
        }
      });

      if (!candidate) candidate = tocTargets[0];
      return candidate && candidate.id ? '#' + candidate.id : '';
    }

    var tocObserver = new IntersectionObserver(
      function () {
        var hash = getBestVisibleHeadingId();
        if (hash) setActiveTocLink(hash);
      },
      {
        rootMargin: '-15% 0px -70% 0px',
        threshold: [0, 1],
      }
    );

    tocTargets.forEach(function (target) {
      tocObserver.observe(target);
    });

    tocLinks.forEach(function (link) {
      SiteUtils.on(link, 'click', function () {
        var hash = link.getAttribute('href') || '';
        if (hash) setActiveTocLink(hash);
      });
    });

    var initialHash = window.location.hash;
    if (
      initialHash &&
      tocLinks.some(function (link) {
        return link.getAttribute('href') === initialHash;
      })
    ) {
      setActiveTocLink(initialHash);
    } else {
      var fallbackHash = getBestVisibleHeadingId();
      if (fallbackHash) setActiveTocLink(fallbackHash);
    }

    if (hasSubHeadings && tocNav instanceof HTMLElement) {
      tocNav.classList.add('post-toc__nav--grouped');
      syncExpandedGroups();

      SiteUtils.on(tocNav, 'mouseover', function (event) {
        var target = event.target;
        if (!(target instanceof Element)) return;
        var item = target.closest('.post-toc__item');
        if (!(item instanceof HTMLElement)) return;
        var groupId = Number(item.dataset.tocGroup || '');
        if (Number.isNaN(groupId)) return;
        if (hoveredGroupIndex === groupId) return;
        hoveredGroupIndex = groupId;
        syncExpandedGroups();
      });

      SiteUtils.on(tocNav, 'mouseleave', function () {
        if (hoveredGroupIndex === -1) return;
        hoveredGroupIndex = -1;
        syncExpandedGroups();
      });
    }
  }

  function initPostTocMobileToggle() {
    var toc = SiteUtils.qs('.post-toc');
    if (!(toc instanceof HTMLElement)) return;

    var title = toc.querySelector('.post-toc__title');
    var nav = toc.querySelector('.post-toc__nav');
    if (!(title instanceof HTMLElement) || !(nav instanceof HTMLElement)) return;

    var head = toc.querySelector('.post-toc__head');
    if (!(head instanceof HTMLElement)) {
      head = document.createElement('div');
      head.className = 'post-toc__head';
      toc.insertBefore(head, title);
      head.appendChild(title);
    } else if (title.parentElement !== head) {
      head.insertBefore(title, head.firstChild);
    }

    var toggle = toc.querySelector('.post-toc__toggle');
    if (!(toggle instanceof HTMLButtonElement)) {
      toggle = document.createElement('button');
      toggle.type = 'button';
      toggle.className = 'post-toc__toggle';
      toggle.setAttribute('aria-label', 'Toggle table of contents');
      head.appendChild(toggle);
    } else if (toggle.parentElement !== head) {
      head.appendChild(toggle);
    }

    if (!nav.id) nav.id = 'post-toc-nav';
    toggle.setAttribute('aria-controls', nav.id);

    var mobileQuery =
      typeof window.matchMedia === 'function' ? window.matchMedia('(max-width: 1024px)') : null;

    function isMobileViewport() {
      return !!mobileQuery && mobileQuery.matches;
    }

    function setOpen(isOpen) {
      var open = !!isOpen;
      toc.classList.toggle('is-open', open);
      toggle.classList.toggle('is-open', open);
      nav.classList.toggle('is-open', open);
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      toggle.textContent = open ? 'Close' : 'Contents';
    }

    function setViewportState() {
      if (isMobileViewport()) {
        toc.classList.add('is-collapsible');
        setOpen(toc.classList.contains('is-open'));
        return;
      }

      toc.classList.remove('is-collapsible');
      setOpen(true);
    }

    SiteUtils.on(toggle, 'click', function () {
      setOpen(!toc.classList.contains('is-open'));
    });

    SiteUtils.on(document, 'keydown', function (event) {
      if (event.key === 'Escape' && toc.classList.contains('is-open') && isMobileViewport()) {
        setOpen(false);
      }
    });

    SiteUtils.qsa('.post-toc__link[href^="#"]', toc).forEach(function (link) {
      SiteUtils.on(link, 'click', function () {
        if (isMobileViewport()) setOpen(false);
      });
    });

    setViewportState();

    if (mobileQuery) {
      SiteUtils.onMediaQueryChange(mobileQuery, function () {
        setViewportState();
      });
    }
  }

  function initHighlighting() {
    var codeBlocks = SiteUtils.qsa('.post-body pre code');
    if (!codeBlocks.length) return Promise.resolve();

    var hljsThemeHref = {
      light: 'https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.11.1/build/styles/atom-one-light.min.css',
      dark: 'https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.11.1/build/styles/atom-one-dark.min.css',
    };

    function applyHighlightTheme(theme) {
      var nextHref = hljsThemeHref[theme === 'dark' ? 'dark' : 'light'];
      var link = SiteUtils.qs('link[data-hljs-theme="true"]');
      if (!(link instanceof HTMLLinkElement)) {
        link = document.createElement('link');
        link.rel = 'stylesheet';
        link.setAttribute('data-hljs-theme', 'true');
        document.head.appendChild(link);
      }
      if (link.getAttribute('href') !== nextHref) {
        link.setAttribute('href', nextHref);
      }
    }

    applyHighlightTheme(activeTheme());

    return SiteUtils.loadScript(
      'https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.11.1/build/highlight.min.js'
    )
      .then(function () {
        if (!window.hljs) return;

        var languageAlias = {
          latex: 'tex',
          plain: 'plaintext',
          text: 'plaintext',
          shell: 'bash',
          sh: 'bash',
          zsh: 'bash',
        };

        codeBlocks.forEach(function (block) {
          var languageClass = '';
          Array.from(block.classList).forEach(function (name) {
            if (name.indexOf('language-') === 0) languageClass = name;
          });

          var language = languageClass ? languageClass.slice(9).toLowerCase() : '';
          if (language === 'latex' || language === 'tex') {
            if (languageClass) block.classList.remove(languageClass);
            block.classList.add('language-plaintext');
            return;
          }

          var mappedLanguage = languageAlias[language] || language;

          if (mappedLanguage && window.hljs.getLanguage(mappedLanguage)) {
            if (languageClass && mappedLanguage !== language) {
              block.classList.remove(languageClass);
              block.classList.add('language-' + mappedLanguage);
            }
            window.hljs.highlightElement(block);
            return;
          }

          var source = block.textContent || '';
          var auto = window.hljs.highlightAuto(source);
          block.innerHTML = auto.value;
          block.classList.add('hljs');
          if (auto.language) block.classList.add('language-' + auto.language);
        });

        SiteUtils.on(window, 'themechange', function (event) {
          applyHighlightTheme(eventTheme(event));
        });
      })
      .catch(function () {
        // Ignore highlighting failures.
      });
  }

  function initMermaid() {
    var diagramNodes = SiteUtils.qsa('pre.mermaid');
    if (!diagramNodes.length) return Promise.resolve();

    SiteUtils.loadStylesheet('https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css');

    return SiteUtils.loadScript('https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js')
      .then(function () {
        if (!window.mermaid) return;

        var MERMAID_COLOR_FALLBACKS = {
          '--mermaid-ch1-fill': '#e0f2fe',
          '--mermaid-ch1-stroke': '#0369a1',
          '--mermaid-ch1-text': '#0c4a6e',
          '--mermaid-ch2-fill': '#dcfce7',
          '--mermaid-ch2-stroke': '#15803d',
          '--mermaid-ch2-text': '#14532d',
          '--mermaid-ch3-fill': '#fef3c7',
          '--mermaid-ch3-stroke': '#b45309',
          '--mermaid-ch3-text': '#78350f',
          '--mermaid-ch4-fill': '#ede9fe',
          '--mermaid-ch4-stroke': '#6d28d9',
          '--mermaid-ch4-text': '#4c1d95',
          '--mermaid-ch5-fill': '#fee2e2',
          '--mermaid-ch5-stroke': '#b91c1c',
          '--mermaid-ch5-text': '#7f1d1d',
          '--mermaid-support-fill': '#f8fafc',
          '--mermaid-support-stroke': '#475569',
          '--mermaid-support-text': '#0f172a',
          '--mermaid-littlewood-fill': '#fff7ed',
          '--mermaid-littlewood-stroke': '#ea580c',
          '--mermaid-littlewood-text': '#7c2d12',
        };

        function getMermaidTheme(theme) {
          return theme === 'dark' ? 'dark' : 'default';
        }

        function readMermaidColor(token) {
          var rootStyle = window.getComputedStyle(document.documentElement);
          var value = rootStyle.getPropertyValue(token).trim();
          return value || MERMAID_COLOR_FALLBACKS[token] || '#000000';
        }

        function readThemeFontFamily() {
          var rootStyle = window.getComputedStyle(document.documentElement);
          var value = rootStyle.getPropertyValue('--font-sans').trim();
          return value || '"Google Sans Flex", "Avenir Next", "Segoe UI", sans-serif';
        }

        function resolveMermaidCssVars(sourceText) {
          var resolved = sourceText;
          Object.keys(MERMAID_COLOR_FALLBACKS).forEach(function (token) {
            var replacement = readMermaidColor(token);
            var marker = 'var(' + token + ')';
            resolved = resolved.split(marker).join(replacement);
          });
          return resolved;
        }

        function renderMermaid(theme) {
          diagramNodes.forEach(function (node) {
            if (!node.dataset.mermaidSource) {
              node.dataset.mermaidSource = node.textContent || '';
            }
            var resolvedSource = resolveMermaidCssVars(node.dataset.mermaidSource);
            node.removeAttribute('data-processed');
            node.textContent = resolvedSource;
          });

          var mermaidFontFamily = readThemeFontFamily();

          window.mermaid.initialize({
            startOnLoad: false,
            securityLevel: 'loose',
            theme: getMermaidTheme(theme),
            fontFamily: mermaidFontFamily,
            themeVariables: {
              fontFamily: mermaidFontFamily,
            },
            flowchart: { htmlLabels: true },
          });

          return window.mermaid.run({ nodes: diagramNodes }).catch(function () {});
        }

        var renderQueue = Promise.resolve();

        function queueRender(theme) {
          renderQueue = renderQueue.then(function () {
            return renderMermaid(theme);
          });
          return renderQueue;
        }

        queueRender(activeTheme());

        SiteUtils.on(window, 'themechange', function (event) {
          queueRender(eventTheme(event));
        });
      })
      .catch(function () {
        // Ignore mermaid failures.
      });
  }

  initCodeCopyButtons();
  initPostTocMobileToggle();
  initPostTocScrollSpy();
  initHighlighting();
  initMermaid();
})(window);
