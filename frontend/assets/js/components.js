// === UI Components ===
function renderArticleCard(post) {
  const cover = post.cover_url ? `<img class="article-card-img" src="${post.cover_url}" alt="${post.title}">` : `<div class="article-card-img"></div>`;
  const tags = (post.tags || []).map(t => `<span class="article-tag">${t.name}</span>`).join('');
  return `
    <div class="article-card" onclick="location.href='/article.html?id=${post.id}'">
      ${cover}
      <div class="article-card-body">
        <div class="article-card-title">${escapeHtml(post.title)}</div>
        <div class="article-card-excerpt">${escapeHtml(post.excerpt || stripHtml(post.content))}</div>
        <div class="article-card-meta">
          <span>${formatDate(post.published_at || post.created_at)}</span>
          ${post.category ? `<span>· ${escapeHtml(post.category.name)}</span>` : ''}
        </div>
        ${tags ? `<div style="margin-top:8px">${tags}</div>` : ''}
      </div>
    </div>
  `;
}

function renderComment(comment) {
  const initial = (comment.nickname || 'U')[0].toUpperCase();
  return `
    <div class="comment">
      <div class="comment-avatar">${initial}</div>
      <div class="comment-body">
        <div class="comment-header">
          <span class="comment-nick">${escapeHtml(comment.nickname || 'Anonymous')}</span>
          <span class="comment-time">${formatDate(comment.created_at)}</span>
        </div>
        <div class="comment-content">${escapeHtml(comment.content)}</div>
      </div>
    </div>
  `;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text || '';
  return div.innerHTML;
}

function stripHtml(html) {
  const tmp = document.createElement('div');
  tmp.innerHTML = html || '';
  return tmp.textContent.trim().substring(0, 150);
}