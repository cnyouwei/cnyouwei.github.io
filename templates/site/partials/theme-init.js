/* Apply the saved or system theme before first paint to avoid flashing. */
(function () {
  try {
    var root = document.documentElement;
    var stored = localStorage.getItem('wy-theme');
    var source = localStorage.getItem('wy-theme-source');
    if (source === 'manual' && (stored === 'light' || stored === 'dark')) {
      root.setAttribute('data-theme', stored);
      return;
    }
    var dark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    root.setAttribute('data-theme', dark ? 'dark' : 'light');
  } catch (error) {
    document.documentElement.setAttribute('data-theme', 'light');
  }
})();
