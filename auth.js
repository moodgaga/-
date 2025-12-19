const API_BASE_URL = 'http://localhost:8000/api/v1';

function getToken() {
    return localStorage.getItem('access_token');
}

function setToken(token) {
    localStorage.setItem('access_token', token);
}

function removeToken() {
    localStorage.removeItem('access_token');
}

function isAuthenticated() {
    return !!getToken();
}

async function apiRequest(endpoint, options = {}) {
    const token = getToken();
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers
        });
        
        if (response.status === 401) {
            removeToken();
            let errorMessage = 'Произошла ошибка';
            try {
                const error = await response.json();
                errorMessage = error.detail || error.message || errorMessage;
            } catch (e) {
                errorMessage = 'Неверное имя пользователя или пароль';
            }
            
            if (window.location.pathname.includes('login.html') || 
                window.location.pathname.includes('register.html')) {
                throw new Error(errorMessage);
            }
            
            window.location.href = 'login.html';
            return;
        }
        
        if (!response.ok) {
            let errorMessage = 'Произошла ошибка';
            try {
                const error = await response.json();
                errorMessage = error.detail || error.message || errorMessage;
            } catch (e) {
                errorMessage = `Ошибка ${response.status}: ${response.statusText}`;
            }
            throw new Error(errorMessage);
        }
        
        return await response.json();
    } catch (error) {
        if (error instanceof TypeError && error.message.includes('fetch')) {
            throw new Error('Не удалось подключиться к серверу. Убедитесь, что backend запущен на http://localhost:8000');
        }
        throw error;
    }
}

async function register(email, username, password, fullName) {
    const data = await apiRequest('/auth/register', {
        method: 'POST',
        body: JSON.stringify({
            email,
            username,
            password,
            full_name: fullName || null
        })
    });
    return data;
}

async function login(username, password) {
    try {
        const data = await apiRequest('/auth/login-json', {
            method: 'POST',
            body: JSON.stringify({
                username,
                password
            })
        });
        
        if (!data || !data.access_token) {
            throw new Error('Сервер не вернул токен доступа. Попробуйте еще раз.');
        }
        
        setToken(data.access_token);
        return data;
    } catch (error) {
        if (error.message.includes('fetch')) {
            throw new Error('Не удалось подключиться к серверу. Убедитесь, что backend запущен.');
        }
        throw error;
    }
}

async function getCurrentUser() {
    return await apiRequest('/users/me');
}

async function updateProfile(updateData) {
    return await apiRequest('/users/me', {
        method: 'PUT',
        body: JSON.stringify(updateData)
    });
}

async function getPortfolio() {
    return await apiRequest('/portfolio');
}

async function createPortfolioItem(itemData) {
    return await apiRequest('/portfolio', {
        method: 'POST',
        body: JSON.stringify(itemData)
    });
}

async function updatePortfolioItem(itemId, itemData) {
    return await apiRequest(`/portfolio/${itemId}`, {
        method: 'PUT',
        body: JSON.stringify(itemData)
    });
}

async function deletePortfolioItem(itemId) {
    return await apiRequest(`/portfolio/${itemId}`, {
        method: 'DELETE'
    });
}

function logout() {
    removeToken();
    window.location.href = 'index.html';
}

function checkAuth() {
    if (!isAuthenticated() && window.location.pathname.includes('profile.html')) {
        window.location.href = 'login.html';
    }
}

if (typeof window !== 'undefined') {
    window.addEventListener('DOMContentLoaded', checkAuth);
}
