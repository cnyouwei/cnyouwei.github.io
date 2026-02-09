(function () {
  const menuToggle = document.querySelector('.menu-toggle');
  const siteNav = document.querySelector('.site-nav');
  const themeToggle = document.querySelector('.theme-toggle');
  const themeAwareImages = Array.from(document.querySelectorAll('img[data-theme-src-dark]'));
  const root = document.documentElement;
  const THEME_STORAGE_KEY = 'wy-theme';
  const THEME_SOURCE_KEY = 'wy-theme-source';

  function readStoredThemePreference() {
    try {
      const value = window.localStorage.getItem(THEME_STORAGE_KEY);
      if (value === 'light' || value === 'dark') return value;
      return '';
    } catch (error) {
      return '';
    }
  }

  function readThemeSource() {
    try {
      const value = window.localStorage.getItem(THEME_SOURCE_KEY);
      return value === 'manual' ? 'manual' : 'system';
    } catch (error) {
      return 'system';
    }
  }

  function saveThemePreference(theme, source) {
    const themeSource = source === 'manual' ? 'manual' : 'system';

    try {
      if (theme === 'light' || theme === 'dark') {
        window.localStorage.setItem(THEME_STORAGE_KEY, theme);
      } else {
        window.localStorage.removeItem(THEME_STORAGE_KEY);
      }

      window.localStorage.setItem(THEME_SOURCE_KEY, themeSource);
    } catch (error) {
      // Ignore storage failures (private mode, disabled storage, etc.).
    }
  }

  function getSystemThemePreference() {
    if (typeof window.matchMedia !== 'function') return 'light';
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  function getActiveTheme() {
    const explicitTheme = root.dataset.theme;
    if (explicitTheme === 'light' || explicitTheme === 'dark') {
      return explicitTheme;
    }
    return getSystemThemePreference();
  }

  function updateThemeToggleState() {
    if (!themeToggle) return;

    const activeTheme = getActiveTheme();
    const nextTheme = activeTheme === 'dark' ? 'light' : 'dark';
    const nextThemeLabel = nextTheme === 'dark' ? 'Dark' : 'Light';

    themeToggle.setAttribute('aria-pressed', activeTheme === 'dark' ? 'true' : 'false');
    themeToggle.setAttribute('aria-label', 'Switch to ' + nextTheme + ' theme');
    themeToggle.setAttribute('title', 'Switch to ' + nextTheme + ' theme');

    const textNode = themeToggle.querySelector('.theme-toggle__text');
    if (textNode) {
      textNode.textContent = nextThemeLabel;
    }
  }

  function emitThemeChange() {
    const activeTheme = getActiveTheme();
    window.dispatchEvent(
      new CustomEvent('themechange', {
        detail: { theme: activeTheme },
      })
    );
  }

  function syncThemeAwareImages() {
    if (!themeAwareImages.length) return;

    const activeTheme = getActiveTheme();
    themeAwareImages.forEach(function (image) {
      const darkSrc = (image.getAttribute('data-theme-src-dark') || '').trim();
      const lightSrc = (image.getAttribute('data-theme-src-light') || image.getAttribute('src') || '').trim();
      const nextSrc = activeTheme === 'dark' ? darkSrc : lightSrc;

      if (nextSrc && image.getAttribute('src') !== nextSrc) {
        image.setAttribute('src', nextSrc);
      }
    });
  }

  function applyThemePreference(theme, persist, source) {
    if (theme === 'light' || theme === 'dark') {
      root.dataset.theme = theme;
    } else {
      delete root.dataset.theme;
    }

    if (persist) {
      saveThemePreference(theme, source);
    }

    updateThemeToggleState();
    emitThemeChange();
    syncThemeAwareImages();
  }

  const storedThemePreference = readStoredThemePreference();
  const storedThemeSource = readThemeSource();

  if (storedThemeSource === 'manual' && storedThemePreference) {
    applyThemePreference(storedThemePreference, false);
  } else {
    applyThemePreference('', false);
    saveThemePreference('', 'system');
  }

  if (themeToggle) {
    themeToggle.addEventListener('click', function () {
      const nextTheme = getActiveTheme() === 'dark' ? 'light' : 'dark';
      applyThemePreference(nextTheme, true, 'manual');
    });
  }

  const colorSchemeQuery =
    typeof window.matchMedia === 'function'
      ? window.matchMedia('(prefers-color-scheme: dark)')
      : null;

  if (colorSchemeQuery) {
    const handleColorSchemeChange = function () {
      if (readThemeSource() === 'manual') return;
      updateThemeToggleState();
      emitThemeChange();
      syncThemeAwareImages();
    };

    if (typeof colorSchemeQuery.addEventListener === 'function') {
      colorSchemeQuery.addEventListener('change', handleColorSchemeChange);
    } else if (typeof colorSchemeQuery.addListener === 'function') {
      colorSchemeQuery.addListener(handleColorSchemeChange);
    }
  }

  window.addEventListener('themechange', syncThemeAwareImages);

  const navDropdowns = Array.from(document.querySelectorAll('.nav-dropdown'));
  const navDropdownCloseTimers = new WeakMap();
  const navDropdownCloseDelayMs = 100;
  const navDropdownCanHover =
    typeof window.matchMedia === 'function' &&
    window.matchMedia('(hover: hover) and (pointer: fine)').matches;

  function setNavDropdownOpen(dropdown, shouldOpen) {
    dropdown.classList.toggle('is-open', shouldOpen);
    const toggle = dropdown.querySelector('.nav-dropdown__toggle');
    if (toggle) {
      toggle.setAttribute('aria-expanded', shouldOpen ? 'true' : 'false');
    }
  }

  function clearNavDropdownCloseTimer(dropdown) {
    const timerId = navDropdownCloseTimers.get(dropdown);
    if (typeof timerId === 'number') {
      window.clearTimeout(timerId);
      navDropdownCloseTimers.delete(dropdown);
    }
  }

  function scheduleNavDropdownClose(dropdown) {
    clearNavDropdownCloseTimer(dropdown);
    const timerId = window.setTimeout(function () {
      if (dropdown.dataset.pinned === 'true') return;
      if (dropdown.matches(':hover') || dropdown.matches(':focus-within')) return;
      setNavDropdownOpen(dropdown, false);
    }, navDropdownCloseDelayMs);
    navDropdownCloseTimers.set(dropdown, timerId);
  }

  function closeNavDropdowns(exceptDropdown) {
    navDropdowns.forEach(function (dropdown) {
      clearNavDropdownCloseTimer(dropdown);
      const shouldStayOpen = Boolean(exceptDropdown) && dropdown === exceptDropdown;
      setNavDropdownOpen(dropdown, shouldStayOpen);
      if (!shouldStayOpen) delete dropdown.dataset.pinned;
    });
  }

  if (navDropdowns.length > 0) {
    navDropdowns.forEach(function (dropdown) {
      const toggle = dropdown.querySelector('.nav-dropdown__toggle');
      if (!toggle) return;

      toggle.addEventListener('click', function (event) {
        event.preventDefault();
        const nextIsOpen = !dropdown.classList.contains('is-open');
        if (!nextIsOpen) {
          closeNavDropdowns(null);
          return;
        }

        closeNavDropdowns(dropdown);
        dropdown.dataset.pinned = 'true';
      });

      if (navDropdownCanHover) {
        dropdown.addEventListener('mouseenter', function () {
          if (dropdown.dataset.pinned === 'true') return;
          closeNavDropdowns(dropdown);
        });

        dropdown.addEventListener('mouseleave', function () {
          if (dropdown.dataset.pinned === 'true') return;
          scheduleNavDropdownClose(dropdown);
        });
      }
    });

    document.addEventListener('click', function (event) {
      const target = event.target;
      if (!(target instanceof Node)) return;

      const clickedInsideDropdown = navDropdowns.some(function (dropdown) {
        return dropdown.contains(target);
      });
      if (clickedInsideDropdown) return;

      closeNavDropdowns(null);
    });

    document.addEventListener('keydown', function (event) {
      if (event.key !== 'Escape') return;
      closeNavDropdowns(null);
    });
  }

  if (menuToggle && siteNav) {
    menuToggle.addEventListener('click', function () {
      const isOpen = siteNav.classList.toggle('open');
      menuToggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
      if (!isOpen) closeNavDropdowns(null);
    });

    siteNav.addEventListener('click', function (event) {
      const target = event.target;
      if (!(target instanceof Element)) return;

      const clickedLink = target.closest('a.nav-link[href], a.nav-dropdown__item[href]');
      if (!clickedLink) return;

      closeNavDropdowns(null);
      siteNav.classList.remove('open');
      menuToggle.setAttribute('aria-expanded', 'false');
    });

    document.addEventListener('click', function (event) {
      const target = event.target;
      if (!(target instanceof Node)) return;
      if (!siteNav.classList.contains('open')) return;
      if (siteNav.contains(target) || menuToggle.contains(target)) return;
      closeNavDropdowns(null);
      siteNav.classList.remove('open');
      menuToggle.setAttribute('aria-expanded', 'false');
    });
  }

  function readGaMeasurementId() {
    const root = document.documentElement;
    if (!root) return '';
    return (root.dataset.gaId || '').trim();
  }

  function isValidGaMeasurementId(value) {
    if (!value) return false;
    if (value.toUpperCase() === 'G-XXXXXXXXXX') return false;
    return /^G-[A-Z0-9]+$/i.test(value);
  }

  function initAnalytics() {
    const gaId = readGaMeasurementId();
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

    if (!document.querySelector('script[data-ga-loader="true"]')) {
      const script = document.createElement('script');
      script.async = true;
      script.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(gaId);
      script.dataset.gaLoader = 'true';
      document.head.appendChild(script);
    }

    return gaId;
  }

  function getLinkTrackingSection(link) {
    const sectionNode = link.closest('[id], section, article, header, footer, nav');
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

    const href = normalizeTrackingText(link.getAttribute('href'));
    if (!href || href.toLowerCase().startsWith('javascript:')) return;

    let resolvedUrl = null;
    try {
      resolvedUrl = new URL(link.href, window.location.href);
    } catch (error) {
      resolvedUrl = null;
    }

    const linkText = normalizeTrackingText(link.dataset.analyticsLabel || link.textContent);
    const isExternal = resolvedUrl
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

  const analyticsMeasurementId = initAnalytics();
  if (analyticsMeasurementId) {
    document.addEventListener('click', function (event) {
      if (event.defaultPrevented) return;
      if (event instanceof MouseEvent && event.button !== 0) return;

      const target = event.target;
      if (!(target instanceof Element)) return;

      const link = target.closest('a[href]');
      if (!link) return;

      trackLinkClick(link);
    });
  }

  const backToTopLink = document.querySelector('.back-to-top');
  if (backToTopLink) {
    backToTopLink.addEventListener('click', function (event) {
      event.preventDefault();
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    function updateBackToTopVisibility() {
      const showThreshold = 260;
      const shouldShow = window.scrollY > showThreshold;
      backToTopLink.classList.toggle('is-visible', shouldShow);
    }

    window.addEventListener('scroll', updateBackToTopVisibility, { passive: true });
    updateBackToTopVisibility();
  }

  function copyTextToClipboard(text) {
    if (navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
      return navigator.clipboard.writeText(text);
    }

    return new Promise(function (resolve, reject) {
      const textArea = document.createElement('textarea');
      textArea.value = text;
      textArea.setAttribute('readonly', '');
      textArea.style.position = 'fixed';
      textArea.style.top = '-9999px';
      textArea.style.left = '-9999px';
      document.body.appendChild(textArea);
      textArea.select();

      try {
        const copied = document.execCommand('copy');
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
    const codeBlocks = Array.from(document.querySelectorAll('.post-body pre:not(.mermaid) > code'));
    if (!codeBlocks.length) return;

    codeBlocks.forEach(function (codeBlock) {
      const pre = codeBlock.parentElement;
      if (!(pre instanceof HTMLElement)) return;
      if (pre.querySelector('.code-copy-btn')) return;

      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'code-copy-btn';
      button.textContent = 'Copy';
      button.setAttribute('aria-label', 'Copy code to clipboard');

      let resetTimer = 0;

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

      button.addEventListener('click', function () {
        const source = codeBlock.textContent || '';
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

  initCodeCopyButtons();

  // Active nav link while scrolling sections.
  const navLinks = Array.from(document.querySelectorAll('.nav-link[href^="#"]'));
  const sections = navLinks
    .map(function (link) {
      const id = link.getAttribute('href');
      if (!id) return null;
      return document.querySelector(id);
    })
    .filter(Boolean);

  if (sections.length > 0 && navLinks.length > 0) {
    const observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          const id = '#' + entry.target.id;
          navLinks.forEach(function (link) {
            link.classList.toggle('is-active', link.getAttribute('href') === id);
          });
        });
      },
      {
        rootMargin: '-35% 0px -55% 0px',
        threshold: 0,
      }
    );

    sections.forEach(function (section) {
      observer.observe(section);
    });
  }

  // Blog post table-of-contents scrollspy.
  const tocLinks = Array.from(document.querySelectorAll('.post-toc__link[href^="#"]'));
  const tocTargets = tocLinks
    .map(function (link) {
      const href = link.getAttribute('href');
      if (!href || href.charAt(0) !== '#') return null;
      const id = href.slice(1);
      if (!id) return null;
      return document.getElementById(id);
    })
    .filter(Boolean);

  if (tocLinks.length > 0 && tocTargets.length > 0) {
    function setActiveTocLink(hash) {
      tocLinks.forEach(function (link) {
        const isActive = link.getAttribute('href') === hash;
        link.classList.toggle('is-active', isActive);
        if (isActive) {
          link.setAttribute('aria-current', 'true');
        } else {
          link.removeAttribute('aria-current');
        }
      });
    }

    function getBestVisibleHeadingId() {
      const marker = 120;
      let candidate = null;

      tocTargets.forEach(function (target) {
        const rect = target.getBoundingClientRect();
        if (rect.top <= marker) {
          candidate = target;
        }
      });

      if (!candidate) candidate = tocTargets[0];
      return candidate && candidate.id ? '#' + candidate.id : '';
    }

    const tocObserver = new IntersectionObserver(
      function () {
        const hash = getBestVisibleHeadingId();
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
      link.addEventListener('click', function () {
        const hash = link.getAttribute('href') || '';
        if (hash) setActiveTocLink(hash);
      });
    });

    const initialHash = window.location.hash;
    if (initialHash && tocLinks.some(function (link) { return link.getAttribute('href') === initialHash; })) {
      setActiveTocLink(initialHash);
    } else {
      const fallbackHash = getBestVisibleHeadingId();
      if (fallbackHash) setActiveTocLink(fallbackHash);
    }
  }

  // Paper filter and search.
  const filterButtons = Array.from(document.querySelectorAll('.filter-btn'));
  const orderButtons = Array.from(document.querySelectorAll('.order-btn'));
  const paperLists = Array.from(document.querySelectorAll('.paper-list'));
  const paperCards = Array.from(document.querySelectorAll('.paper'));
  const paperSearch = document.getElementById('paperSearch');
  const paperSections = Array.from(document.querySelectorAll('[data-paper-section]'));
  const workingSection = document.querySelector('[data-paper-section="working"]');
  const publicationSection = document.querySelector('[data-paper-section="pub"]');
  let paperOrderMode = 'chronological';

  function setPaperExpanded(card, expanded) {
    const abstract = card.querySelector('.paper-abstract');
    if (!abstract) return;
    card.classList.toggle('is-expanded', expanded);
    card.setAttribute('aria-expanded', expanded ? 'true' : 'false');
    abstract.hidden = !expanded;
  }

  function setupPaperExpansion() {
    if (!paperLists.length) return;

    paperCards.forEach(function (card) {
      setPaperExpanded(card, false);
    });

    paperLists.forEach(function (list) {
      list.addEventListener('click', function (event) {
        const target = event.target;
        if (!(target instanceof HTMLElement)) return;
        if (target.closest('a')) return;

        const card = target.closest('.paper.paper-collapsible');
        if (!card) return;

        setPaperExpanded(card, !card.classList.contains('is-expanded'));
      });

      list.addEventListener('keydown', function (event) {
        if (event.key !== 'Enter' && event.key !== ' ') return;
        const target = event.target;
        if (!(target instanceof HTMLElement)) return;

        const card = target.closest('.paper.paper-collapsible');
        if (!card || target !== card) return;

        event.preventDefault();
        setPaperExpanded(card, !card.classList.contains('is-expanded'));
      });
    });
  }

  function initPaperSorting() {
    paperSections.forEach(function (section) {
      const sectionKey = section.dataset.paperSection || '';
      const title = section.querySelector('.subsection-title');
      if (title && !title.dataset.defaultHeading) {
        title.dataset.defaultHeading = title.textContent || '';
      }
    });

    paperLists.forEach(function (list) {
      const parentSection = list.closest('[data-paper-section]');
      const sectionKey = parentSection ? parentSection.dataset.paperSection || '' : '';
      Array.from(list.querySelectorAll('.paper')).forEach(function (card, index) {
        card.dataset.originalIndex = String(index);
        card.dataset.originalSection = sectionKey;
      });
    });
  }

  function removeTopicSubsections(list) {
    Array.from(list.querySelectorAll('.topic-subsection')).forEach(function (item) {
      item.remove();
    });
  }

  function clearPaperList(list) {
    while (list.firstChild) {
      list.removeChild(list.firstChild);
    }
  }

  function compareByChronological(left, right) {
    const leftYear = Number(left.dataset.year || 0);
    const rightYear = Number(right.dataset.year || 0);
    const leftIndex = Number(left.dataset.originalIndex || 0);
    const rightIndex = Number(right.dataset.originalIndex || 0);
    if (leftYear !== rightYear) return rightYear - leftYear;
    return leftIndex - rightIndex;
  }

  function applyDefaultSectionHeadings() {
    paperSections.forEach(function (section) {
      const title = section.querySelector('.subsection-title');
      if (!title) return;
      if (title.dataset.defaultHeading) {
        title.textContent = title.dataset.defaultHeading;
      }
    });
  }

  function renderChronologicalLayout() {
    if (paperLists.length < 2) return;

    const workingList = paperLists[0];
    const publicationList = paperLists[1];

    removeTopicSubsections(workingList);
    removeTopicSubsections(publicationList);
    clearPaperList(workingList);
    clearPaperList(publicationList);

    const workingCards = paperCards
      .filter(function (card) {
        return (card.dataset.originalSection || '') === 'working';
      })
      .sort(compareByChronological);

    const publicationCards = paperCards
      .filter(function (card) {
        return (card.dataset.originalSection || '') === 'pub';
      })
      .sort(compareByChronological);

    workingCards.forEach(function (card) {
      workingList.appendChild(card);
    });
    publicationCards.forEach(function (card) {
      publicationList.appendChild(card);
    });

    applyDefaultSectionHeadings();
  }

  function renderTopicLayout() {
    if (paperLists.length < 2) return;

    const workingList = paperLists[0];
    const publicationList = paperLists[1];

    removeTopicSubsections(workingList);
    removeTopicSubsections(publicationList);
    clearPaperList(workingList);
    clearPaperList(publicationList);

    const cards = paperCards.slice().sort(function (left, right) {
      const leftTopic = (left.dataset.topic || 'Other').toLowerCase();
      const rightTopic = (right.dataset.topic || 'Other').toLowerCase();
      const byTopic = leftTopic.localeCompare(rightTopic);
      if (byTopic !== 0) return byTopic;
      return compareByChronological(left, right);
    });

    const groups = [];
    cards.forEach(function (card) {
      const topicName = (card.dataset.topic || 'Other').trim() || 'Other';
      const currentGroup = groups[groups.length - 1];
      if (!currentGroup || currentGroup.topic !== topicName) {
        groups.push({ topic: topicName, cards: [card] });
        return;
      }
      currentGroup.cards.push(card);
    });

    const title = workingSection ? workingSection.querySelector('.subsection-title') : null;
    if (title) {
      title.textContent = 'Papers by Topic';
    }

    const fragment = document.createDocumentFragment();
    groups.forEach(function (group) {
      const heading = document.createElement('div');
      heading.className = 'topic-subsection';
      heading.textContent = group.topic;
      heading.hidden = group.cards.every(function (card) {
        return card.classList.contains('hidden');
      });
      fragment.appendChild(heading);

      group.cards.forEach(function (card) {
        fragment.appendChild(card);
      });
    });

    workingList.appendChild(fragment);
  }

  function updateResearchSectionVisibility() {
    if (!paperSections.length) return;

    if (paperOrderMode === 'topic') {
      if (publicationSection) publicationSection.classList.add('hidden');
      if (workingSection) {
        const hasVisible = Array.from(workingSection.querySelectorAll('.paper')).some(function (paper) {
          return !paper.classList.contains('hidden');
        });
        workingSection.classList.toggle('hidden', !hasVisible);
      }
      return;
    }

    paperSections.forEach(function (section) {
      const hasVisibleItems = Array.from(section.querySelectorAll('.paper')).some(function (paper) {
        return !paper.classList.contains('hidden');
      });
      section.classList.toggle('hidden', !hasVisibleItems);
    });
  }

  function applyPaperFilters() {
    if (!paperCards.length) return;

    const activeButton = filterButtons.find(function (button) {
      return button.classList.contains('active');
    });

    const activeFilter = activeButton ? activeButton.dataset.filter : 'all';
    const query = paperSearch ? paperSearch.value.trim().toLowerCase() : '';

    paperCards.forEach(function (card) {
      const cardType = card.dataset.type || '';
      const text = card.textContent.toLowerCase();
      const matchType = activeFilter === 'all' || activeFilter === cardType;
      const matchQuery = query.length === 0 || text.includes(query);
      card.classList.toggle('hidden', !(matchType && matchQuery));
    });

    if (paperOrderMode === 'topic') {
      renderTopicLayout();
    } else {
      renderChronologicalLayout();
    }

    updateResearchSectionVisibility();
  }

  filterButtons.forEach(function (button) {
    button.addEventListener('click', function () {
      filterButtons.forEach(function (item) {
        item.classList.remove('active');
      });
      button.classList.add('active');
      applyPaperFilters();
    });
  });

  if (paperSearch) {
    paperSearch.addEventListener('input', applyPaperFilters);
  }

  orderButtons.forEach(function (button) {
    button.addEventListener('click', function () {
      orderButtons.forEach(function (item) {
        item.classList.remove('active');
      });
      button.classList.add('active');
      paperOrderMode = button.dataset.order || 'chronological';
      applyPaperFilters();
    });
  });

  setupPaperExpansion();
  initPaperSorting();
  applyPaperFilters();

  // Load the three latest blog posts into the home page section.
  const recentPostsRoot = document.getElementById('recentPosts');

  function formatDate(dateString) {
    const date = new Date(dateString + 'T00:00:00');
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

    let attempts = 0;
    const timer = window.setInterval(function () {
      attempts += 1;
      if (tryTypeset() || attempts >= 12) {
        window.clearInterval(timer);
      }
    }, 150);
  }

  function renderRecentPosts(posts) {
    if (!recentPostsRoot) return;

    if (!posts.length) {
      recentPostsRoot.innerHTML = '<article class="blog-card"><h3>No posts yet</h3><p>Run `python3 scripts/build_site.py` after adding your first markdown post.</p></article>';
      return;
    }

    recentPostsRoot.innerHTML = posts
      .slice(0, 3)
      .map(function (post) {
        const tags = Array.isArray(post.tags) ? post.tags.slice(0, 2) : [];
        const tagMarkup = tags
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
    const candidates = ['blogs/posts.json', './blogs/posts.json', '/blogs/posts.json'];
    let index = 0;

    function next() {
      if (index >= candidates.length) {
        return Promise.reject(new Error('No post index found'));
      }

      const url = candidates[index];
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

  if (recentPostsRoot) {
    const scriptPosts = loadPostsFromScriptTag();
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
})();
