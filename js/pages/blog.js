(function (window) {
  var SiteApp = window.SiteApp || {};
  var SiteUtils = window.SiteUtils;

  function copyTextToClipboard(text) {
    if (navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
      return navigator.clipboard.writeText(text);
    }

    return new Promise(function (resolve, reject) {
      var textArea = document.createElement('textarea');
      textArea.value = text;
      textArea.setAttribute('readonly', '');
      textArea.style.position = 'fixed';
      textArea.style.top = '-9999px';
      textArea.style.left = '-9999px';
      document.body.appendChild(textArea);
      textArea.select();

      try {
        var copied = document.execCommand('copy');
        if (!copied) {
          reject(new Error('Copy command failed'));
          return;
        }
        resolve();
      } catch (error) {
        reject(error);
      } finally {
        textArea.remove();
      }
    });
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
        copyTextToClipboard(source)
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
  }

  function initRecentPosts() {
    var recentPostsRoot = document.getElementById('recentPosts');
    if (!recentPostsRoot) return;

    function formatDate(dateString) {
      var date = new Date(dateString + 'T00:00:00');
      if (Number.isNaN(date.getTime())) return dateString;
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    }

    function escapeHtml(value) {
      return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
    }

    function typesetMathIn(node) {
      if (!node) return;

      function tryTypeset() {
        if (!window.MathJax || typeof window.MathJax.typesetPromise !== 'function') return false;
        window.MathJax.typesetPromise([node]).catch(function () {});
        return true;
      }

      if (tryTypeset()) return;

      var attempts = 0;
      var timer = window.setInterval(function () {
        attempts += 1;
        if (tryTypeset() || attempts >= 12) {
          window.clearInterval(timer);
        }
      }, 150);
    }

    function renderRecentPosts(posts) {
      if (!posts.length) {
        recentPostsRoot.innerHTML = '<article class="blog-card"><h3>No posts yet</h3><p>Run `python3 scripts/build_site.py` after adding your first markdown post.</p></article>';
        return;
      }

      recentPostsRoot.innerHTML = posts
        .slice(0, 3)
        .map(function (post) {
          var tags = Array.isArray(post.tags) ? post.tags.slice(0, 2) : [];
          var tagMarkup = tags
            .map(function (tag) {
              return '<span class="blog-tag">' + tag + '</span>';
            })
            .join('');

          return (
            '<article class="blog-card">' +
            '<div class="blog-meta"><time datetime="' + post.date + '">' + formatDate(post.date) + '</time>' + tagMarkup + '</div>' +
            '<h3><a href="blogs/' + post.slug + '.html">' + escapeHtml(post.title) + '</a></h3>' +
            '<p>' + escapeHtml(post.summary) + '</p>' +
            '<a href="blogs/' + post.slug + '.html">Read post</a>' +
            '</article>'
          );
        })
        .join('');

      typesetMathIn(recentPostsRoot);
    }

    function loadPostsFromScriptTag() {
      if (!window.__BLOG_POSTS__ || !Array.isArray(window.__BLOG_POSTS__)) return [];
      return window.__BLOG_POSTS__;
    }

    function fetchPostsWithFallback() {
      var candidates = ['blogs/posts.json', './blogs/posts.json', '/blogs/posts.json'];
      var index = 0;

      function next() {
        if (index >= candidates.length) {
          return Promise.reject(new Error('No post index found'));
        }

        var url = candidates[index];
        index += 1;

        return fetch(url, { cache: 'no-store' })
          .then(function (response) {
            if (!response.ok) throw new Error('Fetch failed');
            return response.json();
          })
          .catch(function () {
            return next();
          });
      }

      return next();
    }

    var scriptPosts = loadPostsFromScriptTag();
    if (scriptPosts.length > 0) {
      renderRecentPosts(scriptPosts);
      return;
    }

    fetchPostsWithFallback()
      .then(function (posts) {
        renderRecentPosts(Array.isArray(posts) ? posts : []);
      })
      .catch(function () {
        recentPostsRoot.innerHTML = '<article class="blog-card"><h3>Blog unavailable</h3><p>The post index could not be loaded. Run `python3 scripts/build_site.py` and serve the site from the repository root.</p></article>';
      });
  }

  function initHighlighting() {
    var codeBlocks = SiteUtils.qsa('.post-body pre code');
    if (!codeBlocks.length) return Promise.resolve();

    SiteUtils.loadStylesheet(
      'https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.11.1/build/styles/atom-one-dark.min.css'
    );

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

        function readActiveTheme() {
          var explicitTheme = document.documentElement.getAttribute('data-theme');
          if (explicitTheme === 'light' || explicitTheme === 'dark') return explicitTheme;
          if (
            typeof window.matchMedia === 'function' &&
            window.matchMedia('(prefers-color-scheme: dark)').matches
          ) {
            return 'dark';
          }
          return 'light';
        }

        function getMermaidTheme(theme) {
          return theme === 'dark' ? 'dark' : 'default';
        }

        function readMermaidColor(token) {
          var rootStyle = window.getComputedStyle(document.documentElement);
          var value = rootStyle.getPropertyValue(token).trim();
          return value || MERMAID_COLOR_FALLBACKS[token] || '#000000';
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

          window.mermaid.initialize({
            startOnLoad: false,
            securityLevel: 'loose',
            theme: getMermaidTheme(theme),
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

        queueRender(readActiveTheme());

        SiteUtils.on(window, 'themechange', function (event) {
          var detailTheme = event && event.detail ? event.detail.theme : '';
          var nextTheme =
            detailTheme === 'light' || detailTheme === 'dark' ? detailTheme : readActiveTheme();
          queueRender(nextTheme);
        });
      })
      .catch(function () {
        // Ignore mermaid failures.
      });
  }

  SiteApp.initBlog = function initBlog() {
    initCodeCopyButtons();
    initPostTocScrollSpy();
    initRecentPosts();
    initHighlighting();
    initMermaid();
  };

  window.SiteApp = SiteApp;
})(window);
