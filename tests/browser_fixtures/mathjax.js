/* A deterministic loader/queue fixture. Layout verification uses --live-dependencies. */
window.__mathCalls = [];
window.__mathActive = 0;
window.__mathOverlap = false;
window.MathJax = Object.assign(window.MathJax || {}, {
  startup: { promise: Promise.resolve() },
  typesetPromise: function (elements) {
    window.__mathOverlap = window.__mathOverlap || window.__mathActive > 0;
    window.__mathActive += 1;
    window.__mathCalls.push(Array.from(elements || []).map(function (el) { return el.className; }));
    return new Promise(function (resolve) {
      setTimeout(function () { window.__mathActive -= 1; resolve(); }, 20);
    });
  }
});
