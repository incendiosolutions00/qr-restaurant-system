/**
 * QR Restaurant System — API Helper
 * Centralized API calls, JWT handling, toast notifications
 */
const API_BASE = '/api';

const api = {
    // ─── Token Management ─────────────────────────────────────────────────
    getToken() {
        return localStorage.getItem('access_token');
    },

    setTokens(access, refresh) {
        localStorage.setItem('access_token', access);
        localStorage.setItem('refresh_token', refresh);
    },

    clearTokens() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
    },

    getUser() {
        const u = localStorage.getItem('user');
        return u ? JSON.parse(u) : null;
    },

    setUser(user) {
        localStorage.setItem('user', JSON.stringify(user));
    },

    isLoggedIn() {
        return !!this.getToken();
    },

    // ─── HTTP Methods ─────────────────────────────────────────────────────
    async request(endpoint, options = {}) {
        const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;
        const headers = { 'Content-Type': 'application/json', ...options.headers };

        if (this.getToken() && !options.noAuth) {
            headers['Authorization'] = `Bearer ${this.getToken()}`;
        }

        try {
            const response = await fetch(url, { ...options, headers });

            if (response.status === 401 && !options.noAuth) {
                const refreshed = await this.refreshToken();
                if (refreshed) {
                    headers['Authorization'] = `Bearer ${this.getToken()}`;
                    return fetch(url, { ...options, headers }).then(r => this.handleResponse(r));
                } else {
                    this.clearTokens();
                    if (!window.location.pathname.includes('/login')) {
                        showToast('Session expired. Please log in again.', 'warning');
                        window.location.href = '/admin-panel/login/';
                    }
                    throw new Error('Session expired. Please log in again.');
                }
            }

            return this.handleResponse(response);
        } catch (error) {
            // Only show network error for actual fetch failures (no internet, server down)
            // Not for API errors (those have proper messages) or session expiry
            if (error instanceof TypeError) {
                showToast('Network error. Please check your connection.', 'danger');
            }
            throw error;
        }
    },

    async handleResponse(response) {
        const text = await response.text();
        const data = text ? JSON.parse(text) : {};
        if (!response.ok) {
            const errMsg = data.detail || Object.values(data).flat().join(', ') || 'Something went wrong';
            throw new Error(errMsg);
        }
        return data;
    },

    async refreshToken() {
        const refresh = localStorage.getItem('refresh_token');
        if (!refresh) return false;
        try {
            const res = await fetch(`${API_BASE}/token/refresh/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh }),
            });
            if (res.ok) {
                const data = await res.json();
                localStorage.setItem('access_token', data.access);
                return true;
            }
            return false;
        } catch { return false; }
    },

    // ─── Convenience Methods ──────────────────────────────────────────────
    get(endpoint) {
        return this.request(endpoint);
    },

    post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },

    put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    },

    patch(endpoint, data) {
        return this.request(endpoint, {
            method: 'PATCH',
            body: JSON.stringify(data),
        });
    },

    delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    },

    // Public (no auth)
    publicGet(endpoint) {
        return this.request(endpoint, { noAuth: true });
    },

    publicPost(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data),
            noAuth: true,
        });
    },

    // ─── Auth Shortcuts ───────────────────────────────────────────────────
    async login(username, password) {
        const tokens = await this.request('/login/', {
            method: 'POST',
            body: JSON.stringify({ username, password }),
            noAuth: true,
        });
        this.setTokens(tokens.access, tokens.refresh);

        const user = await this.get('/profile/');
        this.setUser(user);
        return user;
    },

    logout() {
        this.clearTokens();
        window.location.href = '/admin-panel/login/';
    },

    async register(data) {
        const result = await this.request('/register/', {
            method: 'POST',
            body: JSON.stringify(data),
            noAuth: true,
        });
        this.setTokens(result.tokens.access, result.tokens.refresh);
        this.setUser(result.user);
        return result.user;
    },
};


// ─── Toast Notification ─────────────────────────────────────────────────────
function showToast(message, type = 'success') {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const icons = {
        success: 'fas fa-check-circle',
        danger: 'fas fa-exclamation-circle',
        warning: 'fas fa-exclamation-triangle',
        info: 'fas fa-info-circle',
    };

    const toast = document.createElement('div');
    toast.className = `toast show align-items-center text-bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="${icons[type] || icons.info} me-2"></i>${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" onclick="this.closest('.toast').remove()"></button>
        </div>
    `;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}


// ─── Format Currency ────────────────────────────────────────────────────────
function formatPrice(amount) {
    return `Rs.${parseFloat(amount).toLocaleString('en-PK', { minimumFractionDigits: 0 })}`;
}


// ─── Format Date ────────────────────────────────────────────────────────────
function formatDate(dateStr) {
    return new Date(dateStr).toLocaleDateString('en-PK', {
        day: 'numeric', month: 'short', year: 'numeric',
        hour: '2-digit', minute: '2-digit',
    });
}
