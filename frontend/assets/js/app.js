// === App Initialization ===
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initHeader();
  initPage();
});

function initTheme() {
  const saved = localStorage.getItem('blog_theme') || 'light';
  document.documentElement.setAttribute('data-theme', saved);
  const toggle = document.querySelector('.theme-toggle');
  if (toggle) {
    toggle.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme');
      const next = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('blog_theme', next);
    });
  }
}

async function initHeader() {
  const navLinks = document.querySelectorAll('.nav-link');
  const current = window.location.pathname;
  navLinks.forEach(link => {
    const href = link.getAttribute('href') || '';
    if (current.includes(href.replace('/','')) && href !== '/') {
      link.classList.add('active');
    }
  });
}

async function initPage() {
  const page = window.location.pathname.split('/').pop() || 'index.html';
  const initFn = {
    'index.html': loadArticles,
    'article.html': loadArticle,
    'search.html': loadSearch,
    'editor.html': initEditorPage,
    'admin.html': loadAdmin,
  };
  if (initFn[page]) {
    try { await initFn[page](); }
    catch(e) { showToast(e.message || 'Load failed', 'error'); }
  }
}

// === Toast ===
function showToast(msg, type = 'success') {
  const el = document.getElementById('toast') || (() => {
    const t = document.createElement('div');
    t.id = 'toast'; t.className = `toast toast-${type}`;
    document.body.appendChild(t);
    return t;
  })();
  el.textContent = msg;
  el.className = `toast toast-${type} show`;
  setTimeout(() => el.classList.remove('show'), 3000);
}

// === Date formatting ===
function formatDate(d) {
  if (!d) return '';
  const date = new Date(d);
  return date.toLocaleDateString('zh-CN', { year: 'numeric', month: 'short', day: 'numeric' });
}