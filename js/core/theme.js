(function (window) {
  var SiteApp = window.SiteApp || {};
  var SiteUtils = window.SiteUtils;
  var PRIMARY_THEME_ORDER = ['light', 'dark'];
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
  };
  var THEME_FALLBACK = 'light';

  function isValidTheme(theme) {
    return (
      typeof theme === 'string' &&
      Object.prototype.hasOwnProperty.call(THEME_METADATA, theme)
    );
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

  function resolveThemeFromEvent(event) {
    var detailTheme = event && event.detail ? event.detail.theme : '';
    if (isValidTheme(detailTheme)) return detailTheme;
    return resolveActiveTheme();
  }

  function getThemeMeta(theme) {
    var resolvedTheme = isValidTheme(theme) ? theme : resolveActiveTheme();
    return THEME_METADATA[resolvedTheme] || THEME_METADATA[THEME_FALLBACK];
  }

  function nextTheme(theme) {
    var resolvedTheme = isValidTheme(theme) ? theme : resolveActiveTheme();
    var index = PRIMARY_THEME_ORDER.indexOf(resolvedTheme);
    if (index < 0) return PRIMARY_THEME_ORDER[0];
    return PRIMARY_THEME_ORDER[(index + 1) % PRIMARY_THEME_ORDER.length];
  }

  window.SiteTheme = {
    isValidTheme: isValidTheme,
    getSystemThemePreference: getSystemThemePreference,
    resolveActiveTheme: resolveActiveTheme,
    resolveThemeFromEvent: resolveThemeFromEvent,
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
    var transitionTimerId = 0;
    var activeTheme = resolveActiveTheme();
    var themeSource = 'system';

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
      var nextSource = source === 'manual' ? 'manual' : 'system';
      try {
        if (nextSource === 'manual' && isValidTheme(theme)) {
          window.localStorage.setItem(THEME_STORAGE_KEY, theme);
        } else {
          window.localStorage.removeItem(THEME_STORAGE_KEY);
        }
        window.localStorage.setItem(THEME_SOURCE_KEY, nextSource);
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

    function emitThemeChange() {
      window.dispatchEvent(
        new CustomEvent('themechange', {
          detail: { theme: activeTheme },
        })
      );
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
      themeToggle.setAttribute('aria-expanded', 'false');

      var textNode = themeToggle.querySelector('.theme-toggle__text');
      if (textNode) textNode.textContent = 'Switch to ' + nextThemeLabel + ' theme';
    }

    function applyThemePreference(theme, source, options) {
      var settings = options || {};
      var previousTheme = activeTheme;
      var resolvedTheme = isValidTheme(theme) ? theme : getSystemThemePreference();

      root.dataset.theme = resolvedTheme;
      activeTheme = resolvedTheme;
      themeSource = source === 'manual' ? 'manual' : 'system';

      if (settings.persist !== false) {
        saveThemePreference(activeTheme, themeSource);
      }

      if (settings.animate) startThemeTransition(previousTheme, activeTheme);
      updateThemeToggleState();
      emitThemeChange();
      syncThemeAwareImages();
    }

    var storedThemePreference = readStoredThemePreference();
    var storedThemeSource = readThemeSource();

    if (storedThemeSource === 'manual' && isValidTheme(storedThemePreference)) {
      applyThemePreference(storedThemePreference, 'manual', { animate: false, persist: false });
    } else {
      applyThemePreference('', 'system', { animate: false, persist: false });
      saveThemePreference('', 'system');
    }

    if (themeToggle) {
      SiteUtils.on(themeToggle, 'click', function () {
        var nextThemeName = nextTheme(activeTheme);
        applyThemePreference(nextThemeName, 'manual', { animate: true });
      });
    }

    var colorSchemeQuery =
      typeof window.matchMedia === 'function'
        ? window.matchMedia('(prefers-color-scheme: dark)')
        : null;

    if (colorSchemeQuery) {
      var handleColorSchemeChange = function () {
        if (themeSource === 'manual') return;
        applyThemePreference('', 'system', { animate: true });
      };
      SiteUtils.onMediaQueryChange(colorSchemeQuery, handleColorSchemeChange);
    }

    SiteUtils.on(window, 'themechange', syncThemeAwareImages);
  };

  window.SiteApp = SiteApp;
})(window);
