// === API Client ===
const API_BASE = '/api';

function getToken() {
  return localStorage.getItem('blog_token');
}

async function api(path, options = {}) {
  const token = getToken();
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (res.status === 401) {
    localStorage.removeItem('blog_token');
    if (window.location.pathname !== '/login.html') {
      window.location.href = '/login.html?redirect=' + encodeURIComponent(window.location.pathname);
    }
    throw new Error('Unauthorized');
  }

  const data = await res.json();
  if (!res.ok) throw new Error(data.message || `HTTP ${res.status}`);
  return data;
}

// Convenience
const apiGet = (path) => api(path, { method: 'GET' });
const apiPost = (path, body) => api(path, { method: 'POST', body: JSON.stringify(body) });
const apiPut = (path, body) => api(path, { method: 'PUT', body: JSON.stringify(body) });
const apiPatch = (path, body) => api(path, { method: 'PATCH', body: JSON.stringify(body) });
const apiDelete = (path) => api(path, { method: 'DELETE' });