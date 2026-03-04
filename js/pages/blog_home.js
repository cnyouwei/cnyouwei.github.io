(function (window) {
  var SiteApp = window.SiteApp || {};
  var SiteUtils = window.SiteUtils;

  function formatDate(dateString) {
    var date = new Date(dateString + 'T00:00:00');
    if (Number.isNaN(date.getTime())) return dateString;
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  }

  function typesetMathIn(node) {
    if (!node) return;

    function tryTypeset() {
      if (!window.MathJax || typeof window.MathJax.typesetPromise !== 'function') return false;
      window.MathJax.typesetPromise([node]).catch(function () {});
      return true;
    }

    if (tryTypeset()) return;

    var attempts = 0;
    var timer = window.setInterval(function () {
      attempts += 1;
      if (tryTypeset() || attempts >= 12) {
        window.clearInterval(timer);
      }
    }, 150);
  }

  function renderRecentPosts(root, posts) {
    if (!posts.length) {
      root.innerHTML = '<article class="blog-card"><h3>No posts yet</h3><p>Run `python3 scripts/build_site.py` after adding your first markdown post.</p></article>';
      return;
    }

    root.innerHTML = posts
      .map(function (post) {
        var tags = Array.isArray(post.tags) ? post.tags.slice(0, 2) : [];
        var tagMarkup = tags
          .map(function (tag) {
            return '<span class="blog-tag">' + SiteUtils.escapeHtml(tag) + '</span>';
          })
          .join('');

        return (
          '<article class="blog-card">' +
          '<div class="blog-meta"><time datetime="' + SiteUtils.escapeHtml(post.date) + '">' + formatDate(post.date) + '</time>' + tagMarkup + '</div>' +
          '<h3><a href="blogs/' + SiteUtils.escapeHtml(post.slug) + '.html">' + SiteUtils.escapeHtml(post.title) + '</a></h3>' +
          '<p>' + SiteUtils.escapeHtml(post.summary) + '</p>' +
          '<a href="blogs/' + SiteUtils.escapeHtml(post.slug) + '.html">Read post</a>' +
          '</article>'
        );
      })
      .join('');

    typesetMathIn(root);
  }

  function initRecentPosts() {
    var recentPostsRoot = document.getElementById('recentPosts');
    if (!recentPostsRoot) return;

    var scriptPosts = window.__BLOG_POSTS__;
    if (!Array.isArray(scriptPosts)) {
      recentPostsRoot.innerHTML = '<article class="blog-card"><h3>Blog unavailable</h3><p>The post index could not be loaded. Run `python3 scripts/build_site.py` and serve the site from the repository root.</p></article>';
      return;
    }

    renderRecentPosts(recentPostsRoot, scriptPosts);
  }

  SiteApp.initBlogHome = function initBlogHome() {
    initRecentPosts();
  };

  window.SiteApp = SiteApp;
})(window);
