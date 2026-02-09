(function (window) {
  var SiteApp = window.SiteApp || {};
  var SiteUtils = window.SiteUtils;

  SiteApp.initTheme = function initTheme() {
    var root = document.documentElement;
    var themeToggle = SiteUtils.qs('.theme-toggle');
    var themeAwareImages = SiteUtils.qsa('img[data-theme-src-dark]');
    var THEME_STORAGE_KEY = 'wy-theme';
    var THEME_SOURCE_KEY = 'wy-theme-source';

    function readStoredThemePreference() {
      try {
        var value = window.localStorage.getItem(THEME_STORAGE_KEY);
        if (value === 'light' || value === 'dark') return value;
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
      var themeSource = source === 'manual' ? 'manual' : 'system';
      try {
        if (theme === 'light' || theme === 'dark') {
          window.localStorage.setItem(THEME_STORAGE_KEY, theme);
        } else {
          window.localStorage.removeItem(THEME_STORAGE_KEY);
        }
        window.localStorage.setItem(THEME_SOURCE_KEY, themeSource);
      } catch (error) {
        // Ignore storage failures.
      }
    }

    function getSystemThemePreference() {
      if (typeof window.matchMedia !== 'function') return 'light';
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    function getActiveTheme() {
      var explicitTheme = root.dataset.theme;
      if (explicitTheme === 'light' || explicitTheme === 'dark') return explicitTheme;
      return getSystemThemePreference();
    }

    function updateThemeToggleState() {
      if (!themeToggle) return;

      var activeTheme = getActiveTheme();
      var nextTheme = activeTheme === 'dark' ? 'light' : 'dark';
      var activeIcon = activeTheme === 'dark' ? 'moon' : 'sun';

      themeToggle.setAttribute('aria-pressed', activeTheme === 'dark' ? 'true' : 'false');
      themeToggle.setAttribute('aria-label', 'Switch to ' + nextTheme + ' theme');
      themeToggle.setAttribute('title', 'Switch to ' + nextTheme + ' theme');
      themeToggle.setAttribute('data-active-icon', activeIcon);

      var textNode = themeToggle.querySelector('.theme-toggle__text');
      if (textNode) textNode.textContent = 'Switch to ' + nextTheme + ' theme';
    }

    function emitThemeChange() {
      window.dispatchEvent(
        new CustomEvent('themechange', {
          detail: { theme: getActiveTheme() },
        })
      );
    }

    function syncThemeAwareImages() {
      if (!themeAwareImages.length) return;

      var activeTheme = getActiveTheme();
      themeAwareImages.forEach(function (image) {
        var darkSrc = (image.getAttribute('data-theme-src-dark') || '').trim();
        var lightSrc = (image.getAttribute('data-theme-src-light') || image.getAttribute('src') || '').trim();
        var nextSrc = activeTheme === 'dark' ? darkSrc : lightSrc;

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

      if (persist) saveThemePreference(theme, source);

      updateThemeToggleState();
      emitThemeChange();
      syncThemeAwareImages();
    }

    var storedThemePreference = readStoredThemePreference();
    var storedThemeSource = readThemeSource();

    if (storedThemeSource === 'manual' && storedThemePreference) {
      applyThemePreference(storedThemePreference, false);
    } else {
      applyThemePreference('', false);
      saveThemePreference('', 'system');
    }

    SiteUtils.on(themeToggle, 'click', function () {
      var nextTheme = getActiveTheme() === 'dark' ? 'light' : 'dark';
      applyThemePreference(nextTheme, true, 'manual');
    });

    var colorSchemeQuery =
      typeof window.matchMedia === 'function'
        ? window.matchMedia('(prefers-color-scheme: dark)')
        : null;

    if (colorSchemeQuery) {
      var handleColorSchemeChange = function () {
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

    SiteUtils.on(window, 'themechange', syncThemeAwareImages);
  };

  window.SiteApp = SiteApp;
})(window);
