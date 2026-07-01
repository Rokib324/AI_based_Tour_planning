/**
 * TravelAI shared authentication utilities (JWT + Google OAuth).
 */
const TravelAuth = (() => {
  const API = '/api/users';
  const ROLE_DASHBOARDS = {
    client: '/dashboard/client/',
    tour_manager: '/dashboard/manager/',
    financial_approver: '/dashboard/finance/',
    admin: '/dashboard/admin/',
  };

  function getAccessToken() {
    return localStorage.getItem('access_token');
  }

  function getRefreshToken() {
    return localStorage.getItem('refresh_token');
  }

  function getStoredUser() {
    try {
      return JSON.parse(localStorage.getItem('user') || 'null');
    } catch {
      return null;
    }
  }

  function storeSession({ access, refresh, user }) {
    if (access) localStorage.setItem('access_token', access);
    if (refresh) localStorage.setItem('refresh_token', refresh);
    if (user) localStorage.setItem('user', JSON.stringify(user));
  }

  function clearSession() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    localStorage.removeItem('pending_verify_email');
  }

  function dashboardUrlForRole(role) {
    return ROLE_DASHBOARDS[role] || '/dashboard/';
  }

  function redirectToRoleDashboard(role) {
    window.location.href = dashboardUrlForRole(role);
  }

  async function refreshAccessToken() {
    const refresh = getRefreshToken();
    if (!refresh) return null;
    const res = await fetch(`${API}/token/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh }),
    });
    if (!res.ok) return null;
    const data = await res.json();
    localStorage.setItem('access_token', data.access);
    return data.access;
  }

  async function fetchWithAuth(url, options = {}) {
    let token = getAccessToken();
    const headers = { ...(options.headers || {}) };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    if (options.body && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }

    let res = await fetch(url, { ...options, headers });
    if (res.status === 401 && getRefreshToken()) {
      token = await refreshAccessToken();
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
        res = await fetch(url, { ...options, headers });
      }
    }
    return res;
  }

  async function fetchProfile() {
    const res = await fetchWithAuth(`${API}/profile/`);
    if (!res.ok) return null;
    const user = await res.json();
    localStorage.setItem('user', JSON.stringify(user));
    return user;
  }

  async function logout(redirectTo = '/auth/login/') {
    const refresh = getRefreshToken();
    if (refresh) {
      try {
        await fetchWithAuth(`${API}/logout/`, {
          method: 'POST',
          body: JSON.stringify({ refresh }),
        });
      } catch (_) { /* ignore */ }
    }
    clearSession();
    window.location.href = redirectTo;
  }

  async function requireAuth(expectedRole = null) {
    const token = getAccessToken();
    if (!token) {
      window.location.href = '/auth/login/';
      return null;
    }
    const user = await fetchProfile();
    if (!user) {
      clearSession();
      window.location.href = '/auth/login/';
      return null;
    }
    if (expectedRole && user.role !== expectedRole && user.role !== 'admin') {
      redirectToRoleDashboard(user.role);
      return null;
    }
    return user;
  }

  async function handleGoogleCredential(response) {
    const res = await fetch(`${API}/auth/google/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id_token: response.credential }),
    });
    const data = await res.json();
    if (!res.ok) {
      const msg = data.id_token?.[0] || data.detail || 'Google sign-in failed.';
      throw new Error(msg);
    }
    storeSession(data);
    redirectToRoleDashboard(data.user.role);
  }

  function initGoogleSignIn(buttonId, onError) {
    const clientId = window.GOOGLE_CLIENT_ID;
    if (!clientId) {
      if (onError) onError('Google login is not configured. Set GOOGLE_CLIENT_ID in .env');
      return;
    }
    google.accounts.id.initialize({
      client_id: clientId,
      callback: async (response) => {
        try {
          await handleGoogleCredential(response);
        } catch (err) {
          if (onError) onError(err.message);
        }
      },
    });
    const btn = document.getElementById(buttonId);
    if (btn) {
      google.accounts.id.renderButton(btn, {
        type: 'standard',
        theme: 'outline',
        size: 'large',
        width: btn.offsetWidth || 360,
        text: 'continue_with',
        shape: 'rectangular',
      });
    }
  }

  return {
    API,
    getAccessToken,
    getRefreshToken,
    getStoredUser,
    storeSession,
    clearSession,
    dashboardUrlForRole,
    redirectToRoleDashboard,
    fetchWithAuth,
    fetchProfile,
    logout,
    requireAuth,
    handleGoogleCredential,
    initGoogleSignIn,
  };
})();
