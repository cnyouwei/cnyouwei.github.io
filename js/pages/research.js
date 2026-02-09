(function (window) {
  var SiteApp = window.SiteApp || {};
  var SiteUtils = window.SiteUtils;

  SiteApp.initResearch = function initResearch() {
    var filterButtons = SiteUtils.qsa('.filter-btn');
    var orderButtons = SiteUtils.qsa('.order-btn');
    var paperLists = SiteUtils.qsa('.paper-list');
    var paperCards = SiteUtils.qsa('.paper');
    var paperSearch = document.getElementById('paperSearch');
    var paperSections = SiteUtils.qsa('[data-paper-section]');
    var workingSection = SiteUtils.qs('[data-paper-section="working"]');
    var publicationSection = SiteUtils.qs('[data-paper-section="pub"]');
    var paperOrderMode = 'chronological';

    if (!paperCards.length) return;

    function setPaperExpanded(card, expanded) {
      var abstract = card.querySelector('.paper-abstract');
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
      var activeButton = filterButtons.find(function (button) {
        return button.classList.contains('active');
      });

      var activeFilter = activeButton ? activeButton.dataset.filter : 'all';
      var query = paperSearch ? paperSearch.value.trim().toLowerCase() : '';

      paperCards.forEach(function (card) {
        var cardType = card.dataset.type || '';
        var text = card.textContent.toLowerCase();
        var matchType = activeFilter === 'all' || activeFilter === cardType;
        var matchQuery = query.length === 0 || text.includes(query);
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
      SiteUtils.on(button, 'click', function () {
        filterButtons.forEach(function (item) {
          item.classList.remove('active');
        });
        button.classList.add('active');
        applyPaperFilters();
      });
    });

    if (paperSearch) {
      SiteUtils.on(paperSearch, 'input', applyPaperFilters);
    }

    orderButtons.forEach(function (button) {
      SiteUtils.on(button, 'click', function () {
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
  };

  window.SiteApp = SiteApp;
})(window);
