/* Research filtering preserves server-rendered papers and their open abstracts. */
(function () {
  'use strict';
  var list = document.getElementById('papersList');
  if (!list) return;
  var controls = document.querySelector('[data-research-controls]');
  var typeFilter = document.getElementById('typeFilter');
  var topicFilter = document.getElementById('topicFilter');
  var sortOrder = document.getElementById('sortOrder');
  var search = document.getElementById('paperSearch');
  var status = document.getElementById('papers-status');
  var emptyNote = list.querySelector('.papers-empty');
  var papers = Array.from(list.querySelectorAll('.paper'));
  var originalGroups = Array.from(list.querySelectorAll('.paper-group'));
  var parents = new Map(papers.map(function (paper) { return [paper, paper.parentElement]; }));
  var topicContainer = null;

  function apply() {
    var type = typeFilter.value;
    var topic = topicFilter.value;
    var query = search.value.trim().toLowerCase();
    var visible = papers.filter(function (paper) {
      return (type === 'all' || paper.dataset.type === type) &&
        (topic === 'all' || paper.dataset.topic === topic) &&
        (!query || paper.dataset.search.indexOf(query) !== -1);
    });
    var visibleSet = new Set(visible);
    papers.forEach(function (paper) {
      parents.get(paper).appendChild(paper);
      paper.hidden = !visibleSet.has(paper);
    });
    if (topicContainer) { topicContainer.remove(); topicContainer = null; }
    var byTopic = sortOrder.value === 'topic';
    originalGroups.forEach(function (group) {
      group.hidden = byTopic || !group.querySelector('.paper:not([hidden])');
    });
    if (byTopic) {
      var groups = new Map();
      visible.forEach(function (paper) {
        var name = paper.dataset.topic || 'Other';
        if (!groups.has(name)) groups.set(name, []);
        groups.get(name).push(paper);
      });
      topicContainer = document.createElement('div');
      topicContainer.className = 'topic-groups';
      Array.from(groups.keys()).sort().forEach(function (name) {
        var section = document.createElement('section');
        section.className = 'paper-group';
        var heading = document.createElement('h3');
        heading.className = 'paper-group-title';
        heading.textContent = name;
        var wrap = document.createElement('div');
        wrap.className = 'paper-list';
        groups.get(name).sort(function (a, b) { return Number(b.dataset.year) - Number(a.dataset.year); })
          .forEach(function (paper) { wrap.appendChild(paper); });
        section.append(heading, wrap);
        topicContainer.appendChild(section);
      });
      list.insertBefore(topicContainer, emptyNote);
    }
    emptyNote.hidden = visible.length > 0;
    status.textContent = visible.length === papers.length ? papers.length + ' papers' :
      visible.length + ' of ' + papers.length + ' papers';
    document.dispatchEvent(new Event('wy:layoutchange'));
  }

  [typeFilter, topicFilter, sortOrder].forEach(function (control) { control.addEventListener('change', apply); });
  search.addEventListener('input', apply);
  apply();
  controls.hidden = false;

  /* Print the complete bibliography, then restore the reader's exact view. */
  var printState = null;
  function beginPrint() {
    if (printState) return;
    printState = {
      type: typeFilter.value, topic: topicFilter.value, order: sortOrder.value, query: search.value,
      abstracts: Array.from(list.querySelectorAll('.paper-abstract')).map(function (details) { return [details, details.open]; })
    };
    typeFilter.value = 'all';
    topicFilter.value = 'all';
    sortOrder.value = 'chronological';
    search.value = '';
    apply();
    printState.abstracts.forEach(function (pair) { pair[0].open = true; });
  }
  function endPrint() {
    if (!printState) return;
    var saved = printState;
    printState = null;
    typeFilter.value = saved.type;
    topicFilter.value = saved.topic;
    sortOrder.value = saved.order;
    search.value = saved.query;
    saved.abstracts.forEach(function (pair) { pair[0].open = pair[1]; });
    apply();
  }
  window.addEventListener('beforeprint', beginPrint);
  window.addEventListener('afterprint', endPrint);
  window.matchMedia('print').addEventListener('change', function (event) {
    if (event.matches) beginPrint();
    else endPrint();
  });

  list.addEventListener('toggle', function (event) {
    var details = event.target;
    if (!details.matches('.paper-abstract') || !details.open || !window.WY) return;
    var body = details.querySelector('.paper-abstract-body');
    if (body && /[$\\]/.test(body.textContent || '')) {
      window.WY.typesetMath([body]).catch(function () { window.WY.showMathRetry(body, [body]); });
    }
  }, true);
})();
