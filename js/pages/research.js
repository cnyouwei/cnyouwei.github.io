(function (window) {
  var SiteUtils = window.SiteUtils;

  // The home page ships the MathJax config but not the ~1 MB engine; abstracts
  // are collapsed, so we fetch and run it only when one with math is first
  // opened. The page config sets startup.typeset = false, so we typeset each
  // abstract explicitly once it is visible (correct box measurements).
  var MATHJAX_LOADER_SRC = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js';
  var mathJaxPromise = null;

  function abstractHasMath(element) {
    var text = element.textContent || '';
    return text.indexOf('$') !== -1 || text.indexOf('\\(') !== -1 || text.indexOf('\\[') !== -1;
  }

  function ensureMathJax() {
    if (mathJaxPromise) return mathJaxPromise;
    if (typeof SiteUtils.loadScript !== 'function') {
      mathJaxPromise = Promise.reject(new Error('loadScript unavailable'));
      return mathJaxPromise;
    }
    mathJaxPromise = SiteUtils.loadScript(MATHJAX_LOADER_SRC).then(function () {
      if (window.MathJax && window.MathJax.startup && window.MathJax.startup.promise) {
        return window.MathJax.startup.promise;
      }
    });
    return mathJaxPromise;
  }

  function typesetAbstract(abstract) {
    if (!abstract || abstract.dataset.mathTypeset === 'true') return;
    abstract.dataset.mathTypeset = 'true';
    if (!abstractHasMath(abstract)) return;
    ensureMathJax()
      .then(function () {
        if (window.MathJax && typeof window.MathJax.typesetPromise === 'function') {
          return window.MathJax.typesetPromise([abstract]);
        }
      })
      .catch(function () {
        abstract.dataset.mathTypeset = '';
      });
  }

  function initResearch() {
    var paperLists = SiteUtils.qsa('.paper-list');
    var paperCards = SiteUtils.qsa('.paper');
    var paperSearch = document.getElementById('paperSearch');
    var paperSections = SiteUtils.qsa('[data-paper-section]');
    var workingSection = SiteUtils.qs('[data-paper-section="working"]');
    var publicationSection = SiteUtils.qs('[data-paper-section="pub"]');
    var typeSelect = document.getElementById('typeFilter');
    var topicSelect = document.getElementById('topicFilter');
    var sortSelect = document.getElementById('sortOrder');
    var paperOrderMode = sortSelect ? sortSelect.value || 'chronological' : 'chronological';
    var paperTopicFilter = 'all';

    if (!paperCards.length) return;

    function paperTopicName(card) {
      return (card.dataset.topic || 'Other').trim() || 'Other';
    }

    function populateTopicOptions() {
      if (!topicSelect) return;
      var seen = {};
      paperCards.forEach(function (card) {
        seen[paperTopicName(card)] = true;
      });
      Object.keys(seen)
        .sort(function (left, right) {
          return left.toLowerCase().localeCompare(right.toLowerCase());
        })
        .forEach(function (topic) {
          var option = document.createElement('option');
          option.value = topic;
          option.textContent = topic;
          topicSelect.appendChild(option);
        });
    }

    function setPaperExpanded(card, expanded) {
      var abstract = card.querySelector('.paper-abstract');
      if (!abstract) return;
      card.classList.toggle('is-expanded', expanded);
      card.setAttribute('aria-expanded', expanded ? 'true' : 'false');
      abstract.hidden = !expanded;
      if (expanded) typesetAbstract(abstract);
    }

    function setupPaperExpansion() {
      if (!paperLists.length) return;

      paperCards.forEach(function (card) {
        setPaperExpanded(card, false);
      });

      paperLists.forEach(function (list) {
        SiteUtils.on(list, 'click', function (event) {
          var target = event.target;
          if (!(target instanceof HTMLElement)) return;
          if (target.closest('a')) return;

          var card = target.closest('.paper.paper-collapsible');
          if (!card) return;

          setPaperExpanded(card, !card.classList.contains('is-expanded'));
        });

        SiteUtils.on(list, 'keydown', function (event) {
          if (event.key !== 'Enter' && event.key !== ' ') return;
          var target = event.target;
          if (!(target instanceof HTMLElement)) return;

          var card = target.closest('.paper.paper-collapsible');
          if (!card || target !== card) return;

          event.preventDefault();
          setPaperExpanded(card, !card.classList.contains('is-expanded'));
        });
      });
    }

    function initPaperSorting() {
      paperSections.forEach(function (section) {
        var title = section.querySelector('.subsection-title');
        if (title && !title.dataset.defaultHeading) {
          title.dataset.defaultHeading = title.textContent || '';
        }
      });

      paperLists.forEach(function (list) {
        var parentSection = list.closest('[data-paper-section]');
        var sectionKey = parentSection ? parentSection.dataset.paperSection || '' : '';
        SiteUtils.qsa('.paper', list).forEach(function (card, index) {
          card.dataset.originalIndex = String(index);
          card.dataset.originalSection = sectionKey;
        });
      });
    }

    function removeTopicSubsections(list) {
      SiteUtils.qsa('.topic-subsection', list).forEach(function (item) {
        item.remove();
      });
    }

    function clearPaperList(list) {
      while (list.firstChild) {
        list.removeChild(list.firstChild);
      }
    }

    function compareByChronological(left, right) {
      var leftYear = Number(left.dataset.year || 0);
      var rightYear = Number(right.dataset.year || 0);
      var leftIndex = Number(left.dataset.originalIndex || 0);
      var rightIndex = Number(right.dataset.originalIndex || 0);
      if (leftYear !== rightYear) return rightYear - leftYear;
      return leftIndex - rightIndex;
    }

    function applyDefaultSectionHeadings() {
      paperSections.forEach(function (section) {
        var title = section.querySelector('.subsection-title');
        if (!title) return;
        if (title.dataset.defaultHeading) {
          title.textContent = title.dataset.defaultHeading;
        }
      });
    }

    function renderChronologicalLayout() {
      if (paperLists.length < 2) return;

      var workingList = paperLists[0];
      var publicationList = paperLists[1];

      removeTopicSubsections(workingList);
      removeTopicSubsections(publicationList);
      clearPaperList(workingList);
      clearPaperList(publicationList);

      var workingCards = paperCards
        .filter(function (card) {
          return (card.dataset.originalSection || '') === 'working';
        })
        .sort(compareByChronological);

      var publicationCards = paperCards
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

      var workingList = paperLists[0];
      var publicationList = paperLists[1];

      removeTopicSubsections(workingList);
      removeTopicSubsections(publicationList);
      clearPaperList(workingList);
      clearPaperList(publicationList);

      var cards = paperCards.slice().sort(function (left, right) {
        var leftTopic = (left.dataset.topic || 'Other').toLowerCase();
        var rightTopic = (right.dataset.topic || 'Other').toLowerCase();
        var byTopic = leftTopic.localeCompare(rightTopic);
        if (byTopic !== 0) return byTopic;
        return compareByChronological(left, right);
      });

      var groups = [];
      cards.forEach(function (card) {
        var topicName = (card.dataset.topic || 'Other').trim() || 'Other';
        var currentGroup = groups[groups.length - 1];
        if (!currentGroup || currentGroup.topic !== topicName) {
          groups.push({ topic: topicName, cards: [card] });
          return;
        }
        currentGroup.cards.push(card);
      });

      var title = workingSection ? workingSection.querySelector('.subsection-title') : null;
      if (title) title.textContent = 'Papers by Topic';

      var fragment = document.createDocumentFragment();
      groups.forEach(function (group) {
        var heading = document.createElement('div');
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
          var hasVisible = SiteUtils.qsa('.paper', workingSection).some(function (paper) {
            return !paper.classList.contains('hidden');
          });
          workingSection.classList.toggle('hidden', !hasVisible);
        }
        return;
      }

      paperSections.forEach(function (section) {
        var hasVisibleItems = SiteUtils.qsa('.paper', section).some(function (paper) {
          return !paper.classList.contains('hidden');
        });
        section.classList.toggle('hidden', !hasVisibleItems);
      });
    }

    function applyPaperFilters() {
      var activeFilter = typeSelect ? typeSelect.value || 'all' : 'all';
      var query = paperSearch ? paperSearch.value.trim().toLowerCase() : '';
      var topicFilterActive = paperTopicFilter !== 'all';

      paperCards.forEach(function (card) {
        var cardType = card.dataset.type || '';
        var text = card.textContent.toLowerCase();
        var matchType = activeFilter === 'all' || activeFilter === cardType;
        var matchQuery = query.length === 0 || text.includes(query);
        var matchTopic = !topicFilterActive || paperTopicName(card) === paperTopicFilter;
        card.classList.toggle('hidden', !(matchType && matchQuery && matchTopic));
      });

      if (paperOrderMode === 'topic') {
        renderTopicLayout();
      } else {
        renderChronologicalLayout();
      }

      updateResearchSectionVisibility();
    }

    if (typeSelect) {
      SiteUtils.on(typeSelect, 'change', applyPaperFilters);
    }

    if (paperSearch) {
      SiteUtils.on(paperSearch, 'input', applyPaperFilters);
    }

    if (sortSelect) {
      SiteUtils.on(sortSelect, 'change', function () {
        paperOrderMode = sortSelect.value || 'chronological';
        applyPaperFilters();
      });
    }

    if (topicSelect) {
      SiteUtils.on(topicSelect, 'change', function () {
        paperTopicFilter = topicSelect.value || 'all';
        applyPaperFilters();
      });
    }

    setupPaperExpansion();
    initPaperSorting();
    populateTopicOptions();
    applyPaperFilters();
  }

  initResearch();
})(window);
