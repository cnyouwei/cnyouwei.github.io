/* Home research section: type/topic filters, search, chronological/by-topic
   ordering, and lazy MathJax for abstracts (engine loads on first open). */
(function () {
  'use strict';

  function init() {
    var list = document.getElementById('papersList');
    if (!list) return;

    var typeFilter = document.getElementById('typeFilter');
    var topicFilter = document.getElementById('topicFilter');
    var sortOrder = document.getElementById('sortOrder');
    var search = document.getElementById('paperSearch');
    var emptyNote = list.querySelector('.papers-empty');

    var papers = Array.prototype.slice.call(list.querySelectorAll('.paper'));
    var originalGroups = Array.prototype.slice.call(list.querySelectorAll('.paper-group'));
    var originalParent = new Map();
    papers.forEach(function (paper) {
      originalParent.set(paper, paper.parentElement);
    });
    var topicContainer = null;

    /* ---- Filtering ---------------------------------------------------- */

    function matches(paper) {
      var type = typeFilter ? typeFilter.value : 'all';
      var topic = topicFilter ? topicFilter.value : 'all';
      var query = search ? search.value.trim().toLowerCase() : '';
      if (type !== 'all' && paper.getAttribute('data-type') !== type) return false;
      if (topic !== 'all' && paper.getAttribute('data-topic') !== topic) return false;
      if (query && (paper.getAttribute('data-search') || '').indexOf(query) === -1) return false;
      return true;
    }

    function applyChronological() {
      if (topicContainer) {
        topicContainer.remove();
        topicContainer = null;
      }
      // Re-append every paper unconditionally: `papers` holds the original
      // document order, so this rebuilds each group's order even after a
      // partial regroup (appendChild moves already-attached nodes).
      papers.forEach(function (paper) {
        originalParent.get(paper).appendChild(paper);
        paper.hidden = !matches(paper);
      });
      var anyVisible = false;
      originalGroups.forEach(function (group) {
        group.hidden = false;
        var visible = group.querySelectorAll('.paper:not([hidden])').length;
        group.hidden = visible === 0;
        if (visible > 0) anyVisible = true;
      });
      if (emptyNote) emptyNote.hidden = anyVisible;
    }

    function applyByTopic() {
      originalGroups.forEach(function (group) { group.hidden = true; });
      if (topicContainer) topicContainer.remove();
      topicContainer = document.createElement('div');
      topicContainer.className = 'topic-groups';

      var visible = papers.filter(matches);
      var byTopic = {};
      visible.forEach(function (paper) {
        var topic = paper.getAttribute('data-topic') || 'Other';
        (byTopic[topic] = byTopic[topic] || []).push(paper);
      });

      Object.keys(byTopic).sort().forEach(function (topic) {
        var section = document.createElement('section');
        section.className = 'paper-group';
        var title = document.createElement('h3');
        title.className = 'paper-group-title';
        title.textContent = topic;
        var wrap = document.createElement('div');
        wrap.className = 'paper-list';
        byTopic[topic]
          .sort(function (a, b) {
            return Number(b.getAttribute('data-year')) - Number(a.getAttribute('data-year'));
          })
          .forEach(function (paper) {
            paper.hidden = false;
            wrap.appendChild(paper);
          });
        section.appendChild(title);
        section.appendChild(wrap);
        topicContainer.appendChild(section);
      });

      list.insertBefore(topicContainer, emptyNote);
      if (emptyNote) emptyNote.hidden = visible.length > 0;
    }

    function apply() {
      if (sortOrder && sortOrder.value === 'topic') {
        applyByTopic();
      } else {
        applyChronological();
      }
    }

    [typeFilter, topicFilter, sortOrder].forEach(function (control) {
      if (control) control.addEventListener('change', apply);
    });
    if (search) search.addEventListener('input', apply);

    /* ---- Lazy MathJax for abstracts -------------------------------------- */

    var engineRequested = false;

    function typeset(element) {
      if (window.MathJax && window.MathJax.typesetPromise) {
        window.MathJax.typesetPromise([element]).catch(function () { /* non-fatal */ });
      }
    }

    function ensureEngine(element) {
      if (window.MathJax && window.MathJax.typesetPromise) {
        typeset(element);
        return;
      }
      if (engineRequested) return;
      engineRequested = true;
      var script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js';
      script.async = true;
      script.onload = function () {
        if (window.MathJax && window.MathJax.startup && window.MathJax.startup.promise) {
          window.MathJax.startup.promise.then(function () {
            document.querySelectorAll('.paper-abstract[open] .paper-abstract-body').forEach(typeset);
          });
        }
      };
      document.head.appendChild(script);
    }

    list.addEventListener('toggle', function (event) {
      var details = event.target;
      if (details.matches && details.matches('.paper-abstract') && details.open) {
        var body = details.querySelector('.paper-abstract-body');
        if (body && /[$\\]/.test(body.textContent || '')) {
          ensureEngine(body);
        }
      }
    }, true);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
