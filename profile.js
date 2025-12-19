let currentUser = null;
let portfolioItems = [];

document.addEventListener('DOMContentLoaded', async () => {
    if (!isAuthenticated()) {
        window.location.href = 'login.html';
        return;
    }

    await loadUserData();
    
    setupTabs();
    
    setupProfileForm();
    setupPasswordForm();
    setupPortfolioForm();
    
    await loadPortfolio();
    
    updatePortfolioStats();
});

async function loadUserData() {
    try {
        currentUser = await getCurrentUser();
        
        document.getElementById('profileEmail').value = currentUser.email || '';
        document.getElementById('profileUsername').value = currentUser.username || '';
        document.getElementById('profileFullName').value = currentUser.full_name || '';
        document.getElementById('profileTelegram').value = currentUser.telegram || '';
        document.getElementById('profilePhone').value = currentUser.phone || '';
        document.getElementById('profileIsPublic').checked = currentUser.is_profile_public || false;
        document.getElementById('profileShowEmail').checked = currentUser.show_email_in_profile !== false;
        

        updateDashboard();
    } catch (error) {
        showMessage('Ошибка при загрузке данных пользователя: ' + error.message, 'error');
        console.error('Ошибка загрузки данных:', error);
    }
}


function updateDashboard() {
    if (!currentUser) return;
    

    const greeting = currentUser.full_name || currentUser.username || 'Пользователь';
    document.getElementById('userGreeting').textContent = greeting;
    

    document.getElementById('dashboardEmail').textContent = currentUser.email || '-';
    document.getElementById('dashboardUsername').textContent = currentUser.username || '-';
    document.getElementById('dashboardFullName').textContent = currentUser.full_name || 'Не указано';
    document.getElementById('dashboardStatus').textContent = currentUser.is_active ? 'Активен' : 'Неактивен';
    document.getElementById('dashboardStatus').style.color = currentUser.is_active ? '#22c55e' : '#ef4444';
    

    if (currentUser.created_at) {
        const date = new Date(currentUser.created_at);
        const formattedDate = date.toLocaleDateString('ru-RU', { 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
        });
        document.getElementById('userSince').textContent = formattedDate;
    }
    

    updatePortfolioStats();
}


function updatePortfolioStats() {
    const totalCount = portfolioItems.length;
    const visibleCount = portfolioItems.filter(item => item.is_visible).length;
    
    document.getElementById('portfolioCount').textContent = totalCount;
    document.getElementById('visibleProjects').textContent = visibleCount;
}


function setupTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.dataset.tab;
            

            tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            

            tabContents.forEach(content => content.classList.remove('active'));
            document.getElementById(`${tabName}Tab`).classList.add('active');
        });
    });
}


function setupProfileForm() {
    const form = document.getElementById('profileForm');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const updateData = {
            email: document.getElementById('profileEmail').value,
            username: document.getElementById('profileUsername').value,
            full_name: document.getElementById('profileFullName').value.trim() || null,
            telegram: document.getElementById('profileTelegram').value.trim() || null,
            phone: document.getElementById('profilePhone').value.trim() || null,
            is_profile_public: document.getElementById('profileIsPublic').checked,
            show_email_in_profile: document.getElementById('profileShowEmail').checked
        };
        
        try {
            await updateProfile(updateData);
            showMessage('Профиль успешно обновлен в базе данных', 'success');
            await loadUserData();
        } catch (error) {
            showMessage(error.message || 'Ошибка при обновлении профиля', 'error');
            console.error('Ошибка обновления профиля:', error);
        }
    });
}


function setupPasswordForm() {
    const form = document.getElementById('passwordForm');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const password = document.getElementById('newPassword').value;
        if (!password || password.length < 6) {
            showMessage('Пароль должен содержать минимум 6 символов', 'error');
            return;
        }
        
        try {
            await updateProfile({ password });
            showMessage('Пароль успешно изменен в базе данных', 'success');
            form.reset();
        } catch (error) {
            showMessage(error.message || 'Ошибка при изменении пароля', 'error');
            console.error('Ошибка изменения пароля:', error);
        }
    });
}


function setupPortfolioForm() {
    const form = document.getElementById('portfolioForm');
    const imageFileInput = document.getElementById('portfolioImageFile');
    const imagePreview = document.getElementById('portfolioImagePreview');
    const imagePreviewImg = document.getElementById('portfolioImagePreviewImg');
    

    imageFileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {

            if (file.size > 10 * 1024 * 1024) {
                showMessage('Файл слишком большой. Максимальный размер: 10 МБ', 'error');
                e.target.value = '';
                return;
            }
            

            const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
            if (!allowedTypes.includes(file.type)) {
                showMessage('Недопустимый формат файла. Используйте JPG, PNG, GIF или WEBP', 'error');
                e.target.value = '';
                return;
            }
            
            const reader = new FileReader();
            reader.onload = (event) => {
                imagePreviewImg.src = event.target.result;
                imagePreview.style.display = 'block';
            };
            reader.readAsDataURL(file);
        } else {
            imagePreview.style.display = 'none';
        }
    });
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const title = document.getElementById('portfolioTitle').value.trim();
        if (!title) {
            showMessage('Название проекта обязательно для заполнения', 'error');
            return;
        }
        const description = document.getElementById('portfolioDescription').value.trim() || null;
        const projectUrl = document.getElementById('portfolioProjectUrl').value.trim() || null;
        const technologies = document.getElementById('portfolioTechnologies').value.trim() || null;
        const isVisible = document.getElementById('portfolioVisible').checked;
        const imageFile = imageFileInput.files[0];
        
        let imageUrl = null;
        

        if (imageFile) {
            try {
                const formData = new FormData();
                formData.append('file', imageFile);
                
                const token = getToken();
                const response = await fetch('http://localhost:8000/api/v1/portfolio/upload-image', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    },
                    body: formData
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Ошибка при загрузке изображения');
                }
                
                const result = await response.json();
                imageUrl = result.image_url;
            } catch (error) {
                showMessage(error.message || 'Ошибка при загрузке изображения', 'error');
                console.error('Ошибка загрузки изображения:', error);
                return;
            }
        }
        
        const itemData = {
            title,
            description,
            image_url: imageUrl,
            project_url: projectUrl,
            technologies,
            is_visible: isVisible
        };
        
        try {
            await createPortfolioItem(itemData);
            showMessage('Проект успешно добавлен в базу данных', 'success');
            form.reset();
            imagePreview.style.display = 'none';
            await loadPortfolio();
            updatePortfolioStats();
        } catch (error) {
            showMessage(error.message || 'Ошибка при добавлении проекта', 'error');
            console.error('Ошибка создания проекта:', error);
        }
    });
}


async function loadPortfolio() {
    try {
        portfolioItems = await getPortfolio();
        renderPortfolio();
        updatePortfolioStats();
    } catch (error) {
        showMessage('Ошибка при загрузке портфолио: ' + error.message, 'error');
        console.error('Ошибка загрузки портфолио:', error);
    }
}


function renderPortfolio() {
    const container = document.getElementById('portfolioList');
    
    if (portfolioItems.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📁</div>
                <p>Портфолио пусто. Добавьте свой первый проект!</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = portfolioItems.map(item => `
        <div class="portfolio-card">
            <div class="portfolio-card-header">
                <div>
                    <h4 class="portfolio-card-title">${escapeHtml(item.title)}</h4>
                    ${item.is_visible ? '<span style="color: #22c55e; font-size: 0.75rem;">● Видимый</span>' : '<span style="color: var(--text-light); font-size: 0.75rem;">● Скрытый</span>'}
                </div>
                <div class="portfolio-card-actions">
                    <button class="btn-secondary" onclick="openEditModal(${item.id})" style="padding: 0.5rem 1rem; font-size: 0.875rem;">Редактировать</button>
                    <button class="btn-danger" onclick="deletePortfolioItemHandler(${item.id})">Удалить</button>
                </div>
            </div>
            ${item.description ? `<p class="portfolio-card-description">${escapeHtml(item.description)}</p>` : ''}
            ${item.technologies ? `<p class="portfolio-card-tech"><strong>Технологии:</strong> ${escapeHtml(item.technologies)}</p>` : ''}
            <div class="portfolio-card-links">
                ${item.project_url ? `<a href="${item.project_url}" target="_blank">🔗 Открыть проект</a>` : ''}
                ${item.image_url ? `<img src="${item.image_url.startsWith('http') ? item.image_url : `http://localhost:8000${item.image_url}`}" alt="${escapeHtml(item.title)}" style="max-width: 100%; border-radius: 8px; margin-top: 1rem;">` : ''}
            </div>
        </div>
    `).join('');
}


function openEditModal(itemId) {
    const item = portfolioItems.find(i => i.id === itemId);
    if (!item) return;
    
    document.getElementById('editPortfolioId').value = item.id;
    document.getElementById('editPortfolioTitle').value = item.title || '';
    document.getElementById('editPortfolioDescription').value = item.description || '';
    document.getElementById('editPortfolioProjectUrl').value = item.project_url || '';
    document.getElementById('editPortfolioTechnologies').value = item.technologies || '';
    document.getElementById('editPortfolioVisible').checked = item.is_visible;
    

    document.getElementById('editPortfolioImageFile').value = '';
    document.getElementById('editPortfolioImagePreview').style.display = 'none';
    

    const currentImageDiv = document.getElementById('editPortfolioCurrentImage');
    const currentImageImg = document.getElementById('editPortfolioCurrentImageImg');
    if (item.image_url) {
        currentImageImg.src = item.image_url.startsWith('http') ? item.image_url : `http://localhost:8000${item.image_url}`;
        currentImageDiv.style.display = 'block';
    } else {
        currentImageDiv.style.display = 'none';
    }
    
    document.getElementById('editModal').style.display = 'flex';
    

    const imageFileInput = document.getElementById('editPortfolioImageFile');
    const imagePreview = document.getElementById('editPortfolioImagePreview');
    const imagePreviewImg = document.getElementById('editPortfolioImagePreviewImg');
    
    imageFileInput.onchange = (e) => {
        const file = e.target.files[0];
        if (file) {

            if (file.size > 10 * 1024 * 1024) {
                showMessage('Файл слишком большой. Максимальный размер: 10 МБ', 'error');
                e.target.value = '';
                return;
            }
            

            const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
            if (!allowedTypes.includes(file.type)) {
                showMessage('Недопустимый формат файла. Используйте JPG, PNG, GIF или WEBP', 'error');
                e.target.value = '';
                return;
            }
            

            const reader = new FileReader();
            reader.onload = (event) => {
                imagePreviewImg.src = event.target.result;
                imagePreview.style.display = 'block';
                currentImageDiv.style.display = 'none';
            };
            reader.readAsDataURL(file);
        } else {
            imagePreview.style.display = 'none';
            if (item.image_url) {
                currentImageDiv.style.display = 'block';
            }
        }
    };
    

    const form = document.getElementById('editPortfolioForm');
    form.onsubmit = async (e) => {
        e.preventDefault();
        
        const title = document.getElementById('editPortfolioTitle').value.trim();
        if (!title) {
            showMessage('Название проекта обязательно для заполнения', 'error');
            return;
        }
        const description = document.getElementById('editPortfolioDescription').value.trim() || null;
        const projectUrl = document.getElementById('editPortfolioProjectUrl').value.trim() || null;
        const technologies = document.getElementById('editPortfolioTechnologies').value.trim() || null;
        const isVisible = document.getElementById('editPortfolioVisible').checked;
        const imageFile = imageFileInput.files[0];
        
        let imageUrl = item.image_url;
        

        if (imageFile) {
            try {
                const formData = new FormData();
                formData.append('file', imageFile);
                
                const token = getToken();
                const response = await fetch('http://localhost:8000/api/v1/portfolio/upload-image', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    },
                    body: formData
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Ошибка при загрузке изображения');
                }
                
                const result = await response.json();
                imageUrl = result.image_url;
            } catch (error) {
                showMessage(error.message || 'Ошибка при загрузке изображения', 'error');
                console.error('Ошибка загрузки изображения:', error);
                return;
            }
        }
        
        const updateData = {
            title,
            description,
            image_url: imageUrl,
            project_url: projectUrl,
            technologies,
            is_visible: isVisible
        };
        
        try {
            await updatePortfolioItem(itemId, updateData);
            showMessage('Проект успешно обновлен в базе данных', 'success');
            closeEditModal();
            await loadPortfolio();
            updatePortfolioStats();
        } catch (error) {
            showMessage(error.message || 'Ошибка при обновлении проекта', 'error');
            console.error('Ошибка обновления проекта:', error);
        }
    };
}


function closeEditModal() {
    document.getElementById('editModal').style.display = 'none';
    document.getElementById('editPortfolioForm').reset();
}


async function deletePortfolioItemHandler(itemId) {
    if (!confirm('Вы уверены, что хотите удалить этот проект?')) {
        return;
    }
    
    try {
        await deletePortfolioItem(itemId);
        showMessage('Проект успешно удален из базы данных', 'success');
        await loadPortfolio();
        updatePortfolioStats();
    } catch (error) {
        showMessage(error.message || 'Ошибка при удалении проекта', 'error');
        console.error('Ошибка удаления проекта:', error);
    }
}


function showMessage(text, type) {
    const messageEl = document.getElementById('message');
    messageEl.textContent = text;
    messageEl.className = `message ${type} show`;
    
    setTimeout(() => {
        messageEl.classList.remove('show');
    }, 5000);
}


function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

