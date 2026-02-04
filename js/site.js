/* ==========================================================================
   Site JS
   - Hash-based navigation (single HTML, multiple "pages")
   - Mobile menu toggle
   - Research filter + search
   ========================================================================== */

(function () {
  const pages = Array.from(document.querySelectorAll(".page"));
  const navLinks = Array.from(document.querySelectorAll(".nav .nav-link[data-page]"));
  const brand = document.querySelector(".brand");
  const navToggle = document.querySelector(".nav-toggle");
  const navList = document.querySelector(".nav-links");

  function setActiveNav(pageId) {
    navLinks.forEach((link) => {
      const isActive = link.dataset.page === pageId;
      link.classList.toggle("active", isActive);
      link.setAttribute("aria-current", isActive ? "page" : "false");
    });
  }

  function showPage(pageId, { pushState = true } = {}) {
    const target = document.getElementById(pageId);
    if (!target) return;

    pages.forEach((p) => p.classList.remove("active"));
    target.classList.add("active");

    // Trigger fade-in animation
    target.classList.remove("fade-in");
    // eslint-disable-next-line no-unused-expressions
    target.offsetHeight; // force reflow
    target.classList.add("fade-in");

    setActiveNav(pageId);

    // Close mobile menu on navigation
    if (navList && navList.classList.contains("open")) {
      navList.classList.remove("open");
      if (navToggle) navToggle.setAttribute("aria-expanded", "false");
    }

    window.scrollTo({ top: 0, behavior: "auto" });

    if (pushState) {
      history.pushState(null, "", "#" + pageId);
    }
  }

  function initialRoute() {
    const hash = (window.location.hash || "").replace("#", "");
    const valid = hash && document.getElementById(hash);
    showPage(valid ? hash : "home", { pushState: false });
  }

  // Bind nav clicks
  navLinks.forEach((link) => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      const pageId = link.dataset.page;
      showPage(pageId);
    });
  });

  if (brand) {
    brand.addEventListener("click", (e) => {
      e.preventDefault();
      showPage("home");
    });
  }

  window.addEventListener("hashchange", initialRoute);
  initialRoute();

  // Mobile menu toggle
  if (navToggle && navList) {
    navToggle.addEventListener("click", () => {
      const isOpen = navList.classList.toggle("open");
      navToggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
    });

    // Close menu when clicking outside
    document.addEventListener("click", (e) => {
      const target = e.target;
      if (!navList.classList.contains("open")) return;
      if (navList.contains(target) || navToggle.contains(target)) return;
      navList.classList.remove("open");
      navToggle.setAttribute("aria-expanded", "false");
    });
  }

  // ------------------------------------------------------------------------
  // Research filtering + search
  // ------------------------------------------------------------------------
  const filterButtons = Array.from(document.querySelectorAll(".filter-btn"));
  const searchInput = document.getElementById("paperSearch");
  const paperCards = Array.from(document.querySelectorAll(".paper"));

  function applyPaperFilters() {
    const activeBtn = filterButtons.find((b) => b.classList.contains("active"));
    const filter = activeBtn ? activeBtn.dataset.filter : "all";
    const q = (searchInput ? searchInput.value : "").trim().toLowerCase();

    paperCards.forEach((card) => {
      const type = card.dataset.type || "";
      const hay = card.innerText.toLowerCase();

      const passType = (filter === "all") ? true : (type === filter);
      const passSearch = q ? hay.includes(q) : true;

      card.classList.toggle("hidden", !(passType && passSearch));
    });

    // Optionally hide empty sections
    const sections = Array.from(document.querySelectorAll("[data-paper-section]"));
    sections.forEach((sec) => {
      const visible = Array.from(sec.querySelectorAll(".paper")).some((c) => !c.classList.contains("hidden"));
      sec.classList.toggle("hidden", !visible);
    });
  }

  filterButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      filterButtons.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      applyPaperFilters();
    });
  });

  if (searchInput) {
    searchInput.addEventListener("input", () => applyPaperFilters());
  }

  applyPaperFilters();
})();
