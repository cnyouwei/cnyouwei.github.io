(function (window) {
  var SiteApp = window.SiteApp || {};
  var SiteUtils = window.SiteUtils;
  var PRIMARY_THEME_ORDER = ['light', 'dark'];
  var HIDDEN_THEME_ORDER = ['cyberpunk', 'solarized'];
  var THEME_METADATA = {
    light: {
      icon: 'sun',
      isDark: false,
      highlightVariant: 'light',
      mermaidVariant: 'default',
      imageVariant: 'light',
      label: 'Light',
    },
    dark: {
      icon: 'moon',
      isDark: true,
      highlightVariant: 'dark',
      mermaidVariant: 'dark',
      imageVariant: 'dark',
      label: 'Dark',
    },
    cyberpunk: {
      icon: 'moon',
      isDark: true,
      highlightVariant: 'dark',
      mermaidVariant: 'dark',
      imageVariant: 'dark',
      label: 'Cyberpunk',
    },
    solarized: {
      icon: 'sun',
      isDark: false,
      highlightVariant: 'light',
      mermaidVariant: 'default',
      imageVariant: 'light',
      label: 'Solarized',
    },
  };
  var THEME_FALLBACK = 'light';

  function isValidTheme(theme) {
    return (
      typeof theme === 'string' &&
      Object.prototype.hasOwnProperty.call(THEME_METADATA, theme)
    );
  }

  function isPersistentManualTheme(theme) {
    return theme === 'cyberpunk' || theme === 'solarized';
  }

  function isSystemFollowTheme(theme) {
    return theme === 'light' || theme === 'dark';
  }

  function getSystemThemePreference() {
    if (typeof window.matchMedia !== 'function') return THEME_FALLBACK;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : THEME_FALLBACK;
  }

  function resolveActiveTheme() {
    var explicitTheme = document.documentElement.getAttribute('data-theme');
    if (isValidTheme(explicitTheme)) return explicitTheme;
    return getSystemThemePreference();
  }

  function getThemeMeta(theme) {
    var resolvedTheme = isValidTheme(theme) ? theme : resolveActiveTheme();
    return THEME_METADATA[resolvedTheme] || THEME_METADATA[THEME_FALLBACK];
  }

  function resolvePrimaryTheme(theme) {
    var resolvedTheme = isValidTheme(theme) ? theme : resolveActiveTheme();
    if (isSystemFollowTheme(resolvedTheme)) return resolvedTheme;
    return getThemeMeta(resolvedTheme).isDark ? 'dark' : 'light';
  }

  function nextTheme(theme) {
    var resolvedTheme = resolvePrimaryTheme(theme);
    var index = PRIMARY_THEME_ORDER.indexOf(resolvedTheme);
    if (index < 0) return PRIMARY_THEME_ORDER[0];
    return PRIMARY_THEME_ORDER[(index + 1) % PRIMARY_THEME_ORDER.length];
  }

  window.SiteTheme = {
    isValidTheme: isValidTheme,
    resolveActiveTheme: resolveActiveTheme,
    getThemeMeta: getThemeMeta,
    nextTheme: nextTheme,
  };

  SiteApp.initTheme = function initTheme() {
    var root = document.documentElement;
    var themeToggle = SiteUtils.qs('.theme-toggle');
    var themeAwareImages = SiteUtils.qsa('img[data-theme-src-dark]');
    var THEME_STORAGE_KEY = 'wy-theme';
    var THEME_SOURCE_KEY = 'wy-theme-source';
    var THEME_TRANSITION_CLASS = 'theme-transitioning';
    var THEME_TRANSITION_MS = 240;
    var HIDDEN_MENU_LONG_PRESS_MS = 550;
    var transitionTimerId = 0;
    var longPressTimerId = 0;
    var longPressTriggered = false;
    var suppressNextClick = false;
    var hiddenThemeMenu = null;
    var hiddenThemeMenuOpen = false;
    var activeTheme = resolveActiveTheme();

    if (themeToggle) {
      themeToggle.setAttribute('aria-haspopup', 'menu');
      themeToggle.setAttribute('aria-expanded', 'false');
    }

    function readStoredThemePreference() {
      try {
        var value = window.localStorage.getItem(THEME_STORAGE_KEY);
        if (isValidTheme(value)) return value;
        return '';
      } catch (error) {
        return '';
      }
    }

    function readThemeSource() {
      try {
        var value = window.localStorage.getItem(THEME_SOURCE_KEY);
        return value === 'manual' ? 'manual' : 'system';
      } catch (error) {
        return 'system';
      }
    }

    function saveThemePreference(theme, source) {
      var themeSource =
        source === 'manual' && isPersistentManualTheme(theme) ? 'manual' : 'system';
      try {
        if (themeSource === 'manual' && isValidTheme(theme)) {
          window.localStorage.setItem(THEME_STORAGE_KEY, theme);
        } else {
          window.localStorage.removeItem(THEME_STORAGE_KEY);
        }
        window.localStorage.setItem(THEME_SOURCE_KEY, themeSource);
      } catch (error) {
        // Ignore storage failures.
      }
    }

    function startThemeTransition(previousTheme, nextThemeName) {
      if (previousTheme === nextThemeName) return;
      if (
        typeof window.matchMedia === 'function' &&
        window.matchMedia('(prefers-reduced-motion: reduce)').matches
      ) {
        return;
      }

      if (transitionTimerId) window.clearTimeout(transitionTimerId);
      root.classList.add(THEME_TRANSITION_CLASS);
      transitionTimerId = window.setTimeout(function () {
        root.classList.remove(THEME_TRANSITION_CLASS);
      }, THEME_TRANSITION_MS);
    }

    function updateThemeToggleState() {
      if (!themeToggle) return;

      var nextThemeName = nextTheme(activeTheme);
      var activeMeta = getThemeMeta(activeTheme);
      var nextThemeMeta = getThemeMeta(nextThemeName);
      var nextThemeLabel = nextThemeMeta.label || nextThemeName;

      themeToggle.setAttribute('aria-pressed', activeMeta.isDark ? 'true' : 'false');
      themeToggle.setAttribute('aria-label', 'Switch to ' + nextThemeLabel + ' theme');
      themeToggle.setAttribute('title', 'Switch to ' + nextThemeLabel + ' theme');
      themeToggle.setAttribute('data-active-icon', activeMeta.icon);
      themeToggle.setAttribute('aria-expanded', hiddenThemeMenuOpen ? 'true' : 'false');

      var textNode = themeToggle.querySelector('.theme-toggle__text');
      if (textNode) textNode.textContent = 'Switch to ' + nextThemeLabel + ' theme';
    }

    function emitThemeChange() {
      window.dispatchEvent(
        new CustomEvent('themechange', {
          detail: { theme: activeTheme },
        })
      );
    }

    function syncThemeAwareImages() {
      if (!themeAwareImages.length) return;

      var imageVariant = getThemeMeta(activeTheme).imageVariant;
      themeAwareImages.forEach(function (image) {
        var darkSrc = (image.getAttribute('data-theme-src-dark') || '').trim();
        var lightSrc = (image.getAttribute('data-theme-src-light') || image.getAttribute('src') || '').trim();
        var nextSrc = imageVariant === 'dark' ? darkSrc || lightSrc : lightSrc || darkSrc;

        if (nextSrc && image.getAttribute('src') !== nextSrc) {
          image.setAttribute('src', nextSrc);
        }
      });
    }

    function syncHiddenThemeMenuState() {
      if (!hiddenThemeMenu) return;
      SiteUtils.qsa('.theme-hidden-menu__item', hiddenThemeMenu).forEach(function (item) {
        var optionTheme = (item.getAttribute('data-theme-option') || '').trim();
        var isCurrentTheme = optionTheme === activeTheme;
        item.classList.toggle('is-active', isCurrentTheme);
        if (isCurrentTheme) {
          item.setAttribute('aria-current', 'true');
        } else {
          item.removeAttribute('aria-current');
        }
      });
    }

    function buildHiddenThemeMenu() {
      if (hiddenThemeMenu) return hiddenThemeMenu;

      hiddenThemeMenu = document.createElement('div');
      hiddenThemeMenu.className = 'theme-hidden-menu';
      hiddenThemeMenu.setAttribute('role', 'menu');
      hiddenThemeMenu.setAttribute('aria-label', 'Theme menu');
      hiddenThemeMenu.hidden = true;

      HIDDEN_THEME_ORDER.forEach(function (themeName) {
        var item = document.createElement('button');
        var label = getThemeMeta(themeName).label || themeName;
        item.type = 'button';
        item.className = 'theme-hidden-menu__item';
        item.setAttribute('role', 'menuitem');
        item.setAttribute('data-theme-option', themeName);
        item.textContent = label;
        hiddenThemeMenu.appendChild(item);
      });

      SiteUtils.on(hiddenThemeMenu, 'click', function (event) {
        var target = event.target;
        if (!(target instanceof Element)) return;
        var item = target.closest('.theme-hidden-menu__item');
        if (!(item instanceof HTMLElement)) return;

        var selectedTheme = (item.getAttribute('data-theme-option') || '').trim();
        if (!isPersistentManualTheme(selectedTheme)) return;

        event.preventDefault();
        closeHiddenThemeMenu({ returnFocus: true });
        applyThemePreference(selectedTheme, true, 'manual', { animate: true });
      });

      document.body.appendChild(hiddenThemeMenu);
      return hiddenThemeMenu;
    }

    function positionHiddenThemeMenu() {
      if (!themeToggle) return;
      var menu = buildHiddenThemeMenu();

      var toggleRect = themeToggle.getBoundingClientRect();
      var viewportWidth = window.innerWidth || document.documentElement.clientWidth;
      var viewportHeight = window.innerHeight || document.documentElement.clientHeight;
      var gap = 8;
      var horizontalPadding = 8;

      var menuWidth = menu.offsetWidth || 172;
      var menuHeight = menu.offsetHeight || 92;

      var left = toggleRect.left + (toggleRect.width - menuWidth) / 2;
      var maxLeft = viewportWidth - menuWidth - horizontalPadding;
      if (left < horizontalPadding) left = horizontalPadding;
      if (left > maxLeft) left = Math.max(horizontalPadding, maxLeft);

      var top = toggleRect.bottom + gap;
      var maxTop = viewportHeight - menuHeight - horizontalPadding;
      if (top > maxTop) {
        var aboveTop = toggleRect.top - menuHeight - gap;
        if (aboveTop >= horizontalPadding) {
          top = aboveTop;
        } else {
          top = Math.max(horizontalPadding, maxTop);
        }
      }

      menu.style.left = Math.round(left) + 'px';
      menu.style.top = Math.round(top) + 'px';
    }

    function openHiddenThemeMenu() {
      if (!themeToggle) return;
      var menu = buildHiddenThemeMenu();

      syncHiddenThemeMenuState();
      menu.hidden = false;
      positionHiddenThemeMenu();
      window.requestAnimationFrame(function () {
        menu.classList.add('is-open');
      });

      hiddenThemeMenuOpen = true;
      updateThemeToggleState();

      var firstItem = menu.querySelector('.theme-hidden-menu__item');
      if (firstItem instanceof HTMLElement) firstItem.focus();
    }

    function closeHiddenThemeMenu(options) {
      var settings = options || {};
      if (!hiddenThemeMenu || !hiddenThemeMenuOpen) return;

      hiddenThemeMenu.classList.remove('is-open');
      hiddenThemeMenu.hidden = true;
      hiddenThemeMenuOpen = false;
      updateThemeToggleState();

      if (settings.returnFocus && themeToggle) themeToggle.focus();
    }

    function clearLongPressTimer() {
      if (!longPressTimerId) return;
      window.clearTimeout(longPressTimerId);
      longPressTimerId = 0;
    }

    function handleThemeTogglePointerDown(event) {
      if (event.pointerType === 'mouse' && event.button !== 0) return;
      longPressTriggered = false;
      clearLongPressTimer();
      longPressTimerId = window.setTimeout(function () {
        longPressTimerId = 0;
        longPressTriggered = true;
        suppressNextClick = true;
        openHiddenThemeMenu();
      }, HIDDEN_MENU_LONG_PRESS_MS);
    }

    function handleThemeTogglePointerEnd() {
      clearLongPressTimer();
    }

    function applyThemePreference(theme, persist, source, options) {
      var settings = options || {};
      var previousTheme = activeTheme;

      if (isValidTheme(theme)) {
        root.dataset.theme = theme;
      } else {
        delete root.dataset.theme;
      }

      if (persist) saveThemePreference(theme, source);

      activeTheme = resolveActiveTheme();
      syncHiddenThemeMenuState();
      if (hiddenThemeMenuOpen) positionHiddenThemeMenu();
      if (settings.animate) startThemeTransition(previousTheme, activeTheme);
      updateThemeToggleState();
      emitThemeChange();
      syncThemeAwareImages();
    }

    var storedThemePreference = readStoredThemePreference();
    var storedThemeSource = readThemeSource();

    if (
      storedThemeSource === 'manual' &&
      storedThemePreference &&
      isSystemFollowTheme(storedThemePreference)
    ) {
      storedThemeSource = 'system';
      storedThemePreference = '';
      saveThemePreference('', 'system');
    }

    if (
      storedThemeSource === 'manual' &&
      storedThemePreference &&
      isPersistentManualTheme(storedThemePreference)
    ) {
      applyThemePreference(storedThemePreference, false, 'manual', { animate: false });
    } else {
      applyThemePreference('', false, 'system', { animate: false });
      saveThemePreference('', 'system');
    }

    if (themeToggle) {
      SiteUtils.on(themeToggle, 'pointerdown', handleThemeTogglePointerDown);
      SiteUtils.on(window, 'pointerup', handleThemeTogglePointerEnd, true);
      SiteUtils.on(window, 'pointercancel', handleThemeTogglePointerEnd, true);
      SiteUtils.on(themeToggle, 'pointerleave', handleThemeTogglePointerEnd);
      SiteUtils.on(themeToggle, 'contextmenu', function (event) {
        if (longPressTriggered || hiddenThemeMenuOpen) event.preventDefault();
      });

      SiteUtils.on(themeToggle, 'click', function (event) {
        if (suppressNextClick) {
          suppressNextClick = false;
          longPressTriggered = false;
          event.preventDefault();
          return;
        }

        if (event.shiftKey) {
          event.preventDefault();
          openHiddenThemeMenu();
          return;
        }

        closeHiddenThemeMenu({ returnFocus: false });
        longPressTriggered = false;
        var nextThemeName = nextTheme(activeTheme);
        applyThemePreference(nextThemeName, true, 'manual', { animate: true });
      });
    }

    SiteUtils.on(document, 'pointerdown', function (event) {
      if (!hiddenThemeMenuOpen) return;
      var target = event.target;
      if (!(target instanceof Node)) return;
      if (themeToggle && themeToggle.contains(target)) return;
      if (hiddenThemeMenu && hiddenThemeMenu.contains(target)) return;
      closeHiddenThemeMenu({ returnFocus: false });
    }, true);

    SiteUtils.on(document, 'keydown', function (event) {
      if (!hiddenThemeMenuOpen) return;
      if (event.key !== 'Escape') return;
      event.preventDefault();
      closeHiddenThemeMenu({ returnFocus: true });
    });

    SiteUtils.on(window, 'resize', function () {
      if (!hiddenThemeMenuOpen) return;
      closeHiddenThemeMenu({ returnFocus: false });
    });

    SiteUtils.on(window, 'scroll', function () {
      if (!hiddenThemeMenuOpen) return;
      closeHiddenThemeMenu({ returnFocus: false });
    }, true);

    var colorSchemeQuery =
      typeof window.matchMedia === 'function'
        ? window.matchMedia('(prefers-color-scheme: dark)')
        : null;

    if (colorSchemeQuery) {
      var handleColorSchemeChange = function () {
        applyThemePreference('', true, 'system', { animate: true });
      };
      SiteUtils.onMediaQueryChange(colorSchemeQuery, handleColorSchemeChange);
    }

    SiteUtils.on(window, 'themechange', syncThemeAwareImages);
  };

  window.SiteApp = SiteApp;
})(window);
