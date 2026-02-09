(function (window) {
  var SiteApp = window.SiteApp || {};
  var SiteUtils = window.SiteUtils;

  function initNavDropdowns() {
    var menuToggle = SiteUtils.qs('.menu-toggle');
    var siteNav = SiteUtils.qs('.site-nav');

    var navDropdowns = SiteUtils.qsa('.nav-dropdown');
    var navDropdownCloseTimers = new WeakMap();
    var navDropdownCloseDelayMs = 100;
    var navDropdownCanHover =
      typeof window.matchMedia === 'function' &&
      window.matchMedia('(hover: hover) and (pointer: fine)').matches;

    function setMobileNavOpen(shouldOpen) {
      if (!menuToggle || !siteNav) return;
      siteNav.classList.toggle('open', shouldOpen);
      menuToggle.setAttribute('aria-expanded', shouldOpen ? 'true' : 'false');
    }

    function setNavDropdownOpen(dropdown, shouldOpen) {
      dropdown.classList.toggle('is-open', shouldOpen);
      var toggle = dropdown.querySelector('.nav-dropdown__toggle');
      if (toggle) toggle.setAttribute('aria-expanded', shouldOpen ? 'true' : 'false');
    }

    function clearNavDropdownCloseTimer(dropdown) {
      var timerId = navDropdownCloseTimers.get(dropdown);
      if (typeof timerId === 'number') {
        window.clearTimeout(timerId);
        navDropdownCloseTimers.delete(dropdown);
      }
    }

    function scheduleNavDropdownClose(dropdown) {
      clearNavDropdownCloseTimer(dropdown);
      var timerId = window.setTimeout(function () {
        if (dropdown.dataset.pinned === 'true') return;
        if (dropdown.matches(':hover') || dropdown.matches(':focus-within')) return;
        setNavDropdownOpen(dropdown, false);
      }, navDropdownCloseDelayMs);
      navDropdownCloseTimers.set(dropdown, timerId);
    }

    function closeNavDropdowns(exceptDropdown) {
      navDropdowns.forEach(function (dropdown) {
        clearNavDropdownCloseTimer(dropdown);
        var shouldStayOpen = Boolean(exceptDropdown) && dropdown === exceptDropdown;
        setNavDropdownOpen(dropdown, shouldStayOpen);
        if (!shouldStayOpen) delete dropdown.dataset.pinned;
      });
    }

    if (navDropdowns.length > 0) {
      navDropdowns.forEach(function (dropdown) {
        var toggle = dropdown.querySelector('.nav-dropdown__toggle');
        if (!toggle) return;

        SiteUtils.on(toggle, 'click', function (event) {
          event.preventDefault();
          var nextIsOpen = !dropdown.classList.contains('is-open');
          if (!nextIsOpen) {
            closeNavDropdowns(null);
            return;
          }
          closeNavDropdowns(dropdown);
          dropdown.dataset.pinned = 'true';
        });

        if (navDropdownCanHover) {
          SiteUtils.on(dropdown, 'mouseenter', function () {
            if (dropdown.dataset.pinned === 'true') return;
            closeNavDropdowns(dropdown);
          });
          SiteUtils.on(dropdown, 'mouseleave', function () {
            if (dropdown.dataset.pinned === 'true') return;
            scheduleNavDropdownClose(dropdown);
          });
        }
      });

      SiteUtils.on(document, 'click', function (event) {
        var target = event.target;
        if (!(target instanceof Node)) return;
        var clickedInsideDropdown = navDropdowns.some(function (dropdown) {
          return dropdown.contains(target);
        });
        if (clickedInsideDropdown) return;
        closeNavDropdowns(null);
      });

      SiteUtils.on(document, 'keydown', function (event) {
        if (event.key !== 'Escape') return;
        closeNavDropdowns(null);
        setMobileNavOpen(false);
      });
    }

    if (menuToggle && siteNav) {
      setMobileNavOpen(false);

      SiteUtils.on(menuToggle, 'click', function () {
        var isOpen = !siteNav.classList.contains('open');
        setMobileNavOpen(isOpen);
        if (!isOpen) closeNavDropdowns(null);
      });

      SiteUtils.on(siteNav, 'click', function (event) {
        var target = event.target;
        if (!(target instanceof Element)) return;

        var clickedLink = target.closest('a.nav-link[href], a.nav-dropdown__item[href]');
        if (!clickedLink) return;

        closeNavDropdowns(null);
        setMobileNavOpen(false);
      });

      SiteUtils.on(document, 'click', function (event) {
        var target = event.target;
        if (!(target instanceof Node)) return;
        if (!siteNav.classList.contains('open')) return;
        if (siteNav.contains(target) || menuToggle.contains(target)) return;
        closeNavDropdowns(null);
        setMobileNavOpen(false);
      });

      if (typeof window.matchMedia === 'function') {
        var mobileMedia = window.matchMedia('(max-width: 820px)');
        var closeWhenDesktop = function (event) {
          if (event.matches) return;
          closeNavDropdowns(null);
          setMobileNavOpen(false);
        };
        if (typeof mobileMedia.addEventListener === 'function') {
          mobileMedia.addEventListener('change', closeWhenDesktop);
        } else if (typeof mobileMedia.addListener === 'function') {
          mobileMedia.addListener(closeWhenDesktop);
        }
      }
    }
  }

  function initSectionSpy() {
    var navLinks = SiteUtils.qsa('.nav-link[href^="#"]');
    var sections = navLinks
      .map(function (link) {
        var id = link.getAttribute('href');
        if (!id) return null;
        return document.querySelector(id);
      })
      .filter(Boolean);

    if (!sections.length || !navLinks.length) return;

    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          var id = '#' + entry.target.id;
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

  SiteApp.initNav = function initNav() {
    initNavDropdowns();
    initSectionSpy();
  };

  window.SiteApp = SiteApp;
})(window);
