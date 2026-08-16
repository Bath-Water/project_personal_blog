// === Auth ===
async function login(emailOrUsername, password, remember) {
  const res = await apiPost('/auth/login', { email_or_username: emailOrUsername, password });
  if (res.data) {
    localStorage.setItem('blog_token', res.data.access_token);
    if (res.data.refresh_token) localStorage.setItem('blog_refresh', res.data.refresh_token);
    if (remember) localStorage.setItem('blog_remember', 'true');
    return true;
  }
  return false;
}

async function register(username, email, password) {
  await apiPost('/auth/register', { username, email, password });
  return true;
}

function logout() {
  localStorage.removeItem('blog_token');
  localStorage.removeItem('blog_refresh');
  window.location.href = '/login.html';
}

function checkAuth() {
  return !!getToken();
}

function requireAuth() {
  if (!checkAuth()) {
    window.location.href = '/login.html?redirect=' + encodeURIComponent(window.location.pathname);
  }
}