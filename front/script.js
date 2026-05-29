// ===== КОНФИГУРАЦИЯ =====
const API_BASE_URL = 'http://127.0.0.1:8000'; // Базовый URL API

// ===== ФУНКЦИИ ДЛЯ РАБОТЫ С ПОЛЬЗОВАТЕЛЕМ =====
function getStoredUserId() {
    return parseInt(localStorage.getItem('movie_app_user_id')) || null;
}

// ===== ЗАГРУЗКА ОЦЕНОК ПОЛЬЗОВАТЕЛЯ =====
function loadUserRatings() {
    const userId = getStoredUserId();
    if (!userId) {
        alert("Сначала зарегистрируйтесь");
        window.location.href = 'index.html';
        return;
    }
    
    const list = document.getElementById('my-ratings-list');
    list.innerHTML = '<li>Загрузка...</li>';
    
    fetch(`${API_BASE_URL}/api/users/${userId}/ratings`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Ошибка загрузки оценок');
            }
            return response.json();
        })
        .then(data => {
            if (data.length === 0) {
                list.innerHTML = '<li>Вы еще не оценивали фильмы</li>';
            } else {
                list.innerHTML = '';
                data.forEach(rating => {
                    const item = document.createElement('li');
                    
                    // Формируем звёздочки для рейтинга
                    let stars = '';
                    for (let i = 1; i <= 5; i++) {
                        stars += i <= rating.rating ? '★' : '☆';
                    }
                    
                    // Форматируем дату
                    const dateStr = rating.created_at ? 
                        new Date(rating.created_at).toLocaleDateString('ru-RU') : 
                        'Неизвестно';
                    
                    item.innerHTML = `
                        <strong>${rating.title}</strong><br>
                        Оценка: <span class="rating-stars">${stars}</span> (${rating.rating}/5)<br>
                        <small>Дата: ${dateStr}</small>
                    `;
                    list.appendChild(item);
                });
            }
        })
        .catch(error => {
            console.error('Ошибка загрузки оценок:', error);
            list.innerHTML = '<li>Ошибка загрузки оценок</li>';
        });
}

// ===== ФУНКЦИИ ДЛЯ РАБОТЫ С ОЦЕНКАМИ =====
function submitRating(movieId, rating) {
    const userId = getStoredUserId();
    if (!userId) {
        alert('Сначала зарегистрируйтесь');
        return;
    }
    
    fetch(`${API_BASE_URL}/api/rate`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            user_id: userId,
            movie_id: movieId,
            rating: rating
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Ошибка сохранения оценки');
        }
        return response.json();
    })
    .then(() => {
        // Показываем уведомление
        alert('✓ Оценка сохранена');
        
        // Отключаем кнопки рейтинга для этого фильма
        const ratingButtons = document.querySelectorAll(`.rating-buttons[data-movie-id="${movieId}"] .rate-btn`);
        ratingButtons.forEach(btn => {
            btn.disabled = true;
        });
    })
    .catch(error => {
        console.error('Ошибка сохранения оценки:', error);
        alert('Ошибка сохранения оценки: ' + error.message);
    });
}

// ===== ЗАГРУЗКА ЖАНРОВ (для страницы genre.html) =====
async function loadGenres() {
    const container = document.getElementById('genres-container');
    if (!container) return;

    try {
        const response = await fetch(`${API_BASE_URL}/api/genres`);
        if (!response.ok) throw new Error('Ошибка загрузки жанров');
        
        const data = await response.json();
        const genres = data.genres;

        container.innerHTML = '';
        
        // Сортируем жанры по коду
        const sortedGenres = Object.entries(genres).sort((a, b) => a[0] - b[0]);
        
        sortedGenres.forEach(([code, name]) => {
            const label = document.createElement('label');
            label.className = 'genre-checkbox';
            label.innerHTML = `
                <input type="checkbox" name="genres" value="${name}">
                <span>${name}</span>
            `;
            container.appendChild(label);
        });
    } catch (error) {
        container.innerHTML = `<div class="error-message">Ошибка: ${error.message}</div>`;
        console.error('Ошибка загрузки жанров:', error);
    }
}

// ===== ОБРАБОТКА ПОИСКА ПО ЖАНРАМ =====
async function handleGenreSearch(event) {
    event.preventDefault();

    // Получаем выбранные жанры
    const selectedGenres = Array.from(document.querySelectorAll('input[name="genres"]:checked'))
        .map(cb => cb.value);

    if (selectedGenres.length === 0) {
        alert('Пожалуйста, выберите хотя бы один жанр');
        return;
    }

    // Получаем параметры формы
    const sortBy = document.querySelector('input[name="sort_by"]:checked').value;
    const limit = document.getElementById('limit').value;

    // Показываем загрузку
    showLoading(true);
    hideResults();

    try {
        // Формируем URL с параметрами
        const params = new URLSearchParams();
        selectedGenres.forEach(genre => params.append('genres', genre));
        params.append('limit', limit);
        params.append('sort_by', sortBy);

        const response = await fetch(`${API_BASE_URL}/api/recommend/genre?${params.toString()}`);
        if (!response.ok) throw new Error('Ошибка получения рекомендаций');

        const data = await response.json();
        
        if (data.movies.length === 0) {
            showNoResults();
        } else {
            displayMovies(data.movies, 'genre');
            document.getElementById('results-count').textContent = 
                `(${data.count} фильмов)`;
            showResults();
        }
    } catch (error) {
        showError(error.message);
        console.error('Ошибка поиска по жанрам:', error);
    } finally {
        showLoading(false);
    }
}

// ===== ОБРАБОТКА ПОИСКА ПО ПРОФИЛЮ =====
async function handleProfileSearch(event) {
    event.preventDefault();

    // Получаем данные формы
    const gender = document.querySelector('input[name="gender"]:checked').value === 'true';
    const age = parseInt(document.getElementById('age').value);
    const occupation_label = parseInt(document.getElementById('occupation').value);
    const top_n = parseInt(document.getElementById('top_n').value);

    if (!occupation_label && occupation_label !== 0) {
        alert('Пожалуйста, выберите профессию');
        return;
    }

    // Показываем загрузку
    showLoading(true);
    hideResults();

    try {
        const requestBody = {
            gender: gender,
            age: age,
            occupation_label: occupation_label,
            top_k: 10,
            top_n: top_n
        };

        const response = await fetch(`${API_BASE_URL}/api/recommend/profile`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });

        if (!response.ok) throw new Error('Ошибка получения рекомендаций');

        const data = await response.json();
        
        if (data.movies.length === 0) {
            showNoResults();
        } else {
            displayMovies(data.movies, 'profile');
            document.getElementById('results-count').textContent = 
                `(${data.recommendations_count} рекомендаций)`;
            showResults();
        }
    } catch (error) {
        showError(error.message);
        console.error('Ошибка поиска по профилю:', error);
    } finally {
        showLoading(false);
    }
}

// ===== ОТОБРАЖЕНИЕ ФИЛЬМОВ =====
function displayMovies(movies, type) {
    const container = document.getElementById('movies-container');
    container.innerHTML = '';

    console.log('API Response:', movies);

    if (!Array.isArray(movies)) {
        console.error('movies не является массивом:', movies);
        container.innerHTML = '<div class="error-message">Ошибка: данные получены в неверном формате</div>';
        showResults();
        return;
    }

    if (movies.length === 0) {
        showNoResults();
        return;
    }

    movies.forEach((movie, index) => {
        // ===== БЕЗОПАСНЫЕ ПОЛУЧЕНИЯ ПОЛЕЙ =====
        // movie_title - название фильма (genre: movie_title, profile: title)
        const movieTitle = (movie.movie_title || movie.title || "Без названия");
        const shortTitle = movieTitle.length > 50 ? movieTitle.substring(0, 50) : movieTitle;
        
        // genres - массив жанров (genre: genres, profile: genres)
        const genresArray = Array.isArray(movie.genres) ? movie.genres : (movie.genres ? [movie.genres] : []);
        const genresHtml = genresArray.map(g => `<span class="genre-tag">${g}</span>`).join('');
        
        // poster_url - URL постера (genre: poster_url, profile: poster_path)
        const posterUrl = (movie.poster_url || movie.poster_path || '').trim();
        
        // ===== ОТЛАДКА ПОСТЕРА =====
        if (posterUrl) {
            console.log(`poster_url for ${movieTitle}:`, posterUrl);
        }
        
        // rating fields
        // genre: avg_rating, rating_count; profile: predicted_rating, recommendation_score
        const avgRating = movie.avg_rating || movie.predicted_rating || 0;
        const ratingCount = movie.rating_count || 0;
        const recommendationScore = movie.recommendation_score || 0;
        
        // movie_id
        const movieId = movie.movie_id || movie.id || index + 1;
        
        const card = document.createElement('div');
        card.className = 'movie-card';

        // Постер — всегда показываем заглушку, поверх грузим изображение
        let posterHtml;
        if (posterUrl) {
            posterHtml = `
                <div class="movie-poster" style="position:relative;">
                    <!-- Заглушка (видна пока грузится или при ошибке) -->
                    <div style="position:absolute; inset:0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display:flex; align-items:center; justify-content:center; text-align:center; padding:15px; z-index:1;">
                        <span style="font-size:1rem; font-weight:600; color:white; text-shadow:1px 1px 3px rgba(0,0,0,0.5);">${shortTitle}</span>
                    </div>
                    <!-- Изображение поверх заглушки -->
                    <img src="${posterUrl}" alt="${movieTitle}" 
                         style="position:relative; z-index:2; width:100%; height:100%; object-fit:cover;"
                         onerror="this.style.display='none';"
                         loading="lazy">
                </div>`;
        } else {
            posterHtml = `<div class="movie-poster" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display:flex; align-items:center; justify-content:center; text-align:center; padding:15px;">
                <span style="font-size:1rem; font-weight:600; color:white;">🎬 ${shortTitle}</span>
            </div>`;
        }

        // Рейтинг
        let ratingHtml = '';
        if (type === 'genre') {
            const rating = (typeof avgRating === 'number') ? avgRating.toFixed(1) : 'N/A';
            ratingHtml = `
                <div class="movie-rating">
                    <span>⭐ ${rating}</span>
                    <span>${ratingCount} оценок</span>
                </div>
            `;
        } else {
            const predicted = (typeof avgRating === 'number') ? avgRating.toFixed(1) : 'N/A';
            const score = (typeof recommendationScore === 'number') ? recommendationScore.toFixed(1) : 'N/A';
            ratingHtml = `
                <div class="movie-rating">
                    <span class="predicted-rating">🎯 Прогноз: ${predicted}</span>
                    <span>Скор: ${score}</span>
                </div>
            `;
        }

        // Добавляем блок с кнопками рейтинга
        const ratingButtonsHtml = `
            <div class="rating-buttons" data-movie-id="${movieId}">
                <button class="rate-btn" data-rating="1">1</button>
                <button class="rate-btn" data-rating="2">2</button>
                <button class="rate-btn" data-rating="3">3</button>
                <button class="rate-btn" data-rating="4">4</button>
                <button class="rate-btn" data-rating="5">5</button>
            </div>
        `;

        card.innerHTML = `
            ${posterHtml}
            <div class="movie-info">
                <div class="movie-title" title="${movieTitle}">${movieTitle}</div>
                <div class="movie-genres">${genresHtml}</div>
                ${ratingHtml}
                ${ratingButtonsHtml}
            </div>
        `;

        container.appendChild(card);
    });
    
    // Добавляем обработчик кликов по кнопкам рейтинга
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('rate-btn')) {
            const movieId = e.target.parentElement.getAttribute('data-movie-id');
            const rating = parseInt(e.target.getAttribute('data-rating'));
            submitRating(movieId, rating);
        }
    });
}

// ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====
function showLoading(show) {
    const loadingSection = document.getElementById('loading-section');
    if (loadingSection) {
        loadingSection.style.display = show ? 'block' : 'none';
    }
}

// ===== ФУНКЦИЯ ВЫХОДА ИЗ АККАУНТА =====
function logout() {
    localStorage.removeItem('movie_app_user_id');
    window.location.href = 'index.html';
}

// ===== ФУНКЦИЯ ВХОДА ПОЛЬЗОВАТЕЛЯ =====
function loginUser(username, password) {
    fetch(`${API_BASE_URL}/api/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Ошибка входа');
        }
        return response.json();
    })
    .then(data => {
        // Сохраняем user_id и username
        localStorage.setItem('movie_app_user_id', data.user_id);
        localStorage.setItem('movie_app_username', data.username);
        
        // Обновляем интерфейс
        document.getElementById('auth-section').style.display = 'none';
        document.getElementById('user-info-section').style.display = 'block';
        document.getElementById('current-username').textContent = data.username;
    })
    .catch(error => {
        console.error('Ошибка входа:', error);
        document.getElementById('auth-message').textContent = 'Ошибка входа: ' + error.message;
    });
}

// ===== ФУНКЦИЯ РЕГИСТРАЦИИ ПОЛЬЗОВАТЕЛЯ =====
function registerUser(username, password) {
    console.log('registerUser called with username:', username);
    
    // Получаем данные анкеты
    const gender = document.getElementById('reg-gender')?.value || null;
    const age = document.getElementById('reg-age')?.value ? parseInt(document.getElementById('reg-age').value) : null;
    const profession = document.getElementById('reg-profession')?.value || null;
    
    console.log('Profile data:', { gender, age, profession });
    
    fetch(`${API_BASE_URL}/api/register`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
            username, 
            password,
            gender,
            age,
            profession
        })
    })
    .then(response => {
        console.log('Response status:', response.status);
        if (!response.ok) {
            throw new Error('Ошибка регистрации');
        }
        return response.json();
    })
    .then(data => {
        console.log('Registration successful:', data);
        // Сохраняем user_id и username
        localStorage.setItem('movie_app_user_id', data.user_id);
        localStorage.setItem('movie_app_username', username);
        
        // Обновляем интерфейс
        document.getElementById('auth-section').style.display = 'none';
        document.getElementById('user-info-section').style.display = 'block';
        document.getElementById('current-username').textContent = username;
    })
    .catch(error => {
        console.error('Ошибка регистрации:', error);
        document.getElementById('auth-message').textContent = 'Ошибка регистрации: ' + error.message;
    });
}

// ===== ФУНКЦИЯ ПЕРЕКЛЮЧЕНИЯ РЕЖИМОВ АУТЕНТИФИКАЦИИ =====
function setAuthMode(mode) {
    const loginTab = document.getElementById('tab-login');
    const registerTab = document.getElementById('tab-register');
    const submitBtn = document.getElementById('auth-submit-btn');
    const messageDiv = document.getElementById('auth-message');
    
    if (mode === 'login') {
        loginTab.classList.add('active');
        registerTab.classList.remove('active');
        submitBtn.textContent = 'Войти';
        messageDiv.textContent = '';
    } else {
        registerTab.classList.add('active');
        loginTab.classList.remove('active');
        submitBtn.textContent = 'Зарегистрироваться';
        messageDiv.textContent = '';
    }
    
    // Сбрасываем форму
    document.getElementById('username').value = '';
    document.getElementById('password').value = '';
}

// ===== ФУНКЦИЯ ПРОВЕРКИ ДОСТУПА К РЕКОМЕНДАЦИЯМ ПО ПРОФИЛЮ =====
async function checkProfileAccess() {
    console.log('checkProfileAccess started');
    
    const userId = localStorage.getItem('movie_app_user_id');
    const username = localStorage.getItem('movie_app_username');
    
    console.log('User state - userId:', userId, 'username:', username);
    
    if (!userId || !username) {
        alert('Войдите или зарегистрируйтесь и заполните анкету');
        return false;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/profile/${userId}`);
        console.log('Profile response status:', response.status);
        
        if (!response.ok) {
            console.log('Profile not found, redirecting to index');
            alert('Войдите или зарегистрируйтесь и заполните анкету');
            window.location.href = 'index.html';
            return false;
        }
        
        const profile = await response.json();
        console.log('Profile data:', profile);
        
        // Проверяем, заполнено ли хотя бы одно поле
        if (!profile.gender && !profile.age && !profile.profession) {
            alert('Войдите или зарегистрируйтесь и заполните анкету');
            window.location.href = 'my_profile.html';
            return false;
        }
        
        console.log('Access granted, profile is filled');
        return true;
    } catch (error) {
        console.error('Profile check error:', error);
        alert('Войдите или зарегистрируйтесь и заполните анкету');
        window.location.href = 'index.html';
        return false;
    }
}

// ===== ОБРАБОТЧИК КНОПКИ "РЕКОМЕНДОВАТЬ ПО ПРОФИЛЮ" =====
document.addEventListener('DOMContentLoaded', function() {
    // Проверяем, на какой странице мы находимся и запускаем соответствующую инициализацию
    if (window.location.pathname.includes('my_profile.html')) {
        loadUserRatings();
        loadUserProfile(); // Загружаем профиль при загрузке страницы
    }
    
    // Обработчик кнопки "Рекомендовать по профилю" на главной странице
    document.getElementById('profile-rec-btn')?.addEventListener('click', async function(e) {
        e.preventDefault();
        const accessGranted = await checkProfileAccess();
        if (accessGranted) {
            window.location.href = 'recommend.html';
        }
    });
});

function showResults() {
    const resultsSection = document.getElementById('results-section');
    if (resultsSection) {
        resultsSection.style.display = 'block';
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

function hideResults() {
    const resultsSection = document.getElementById('results-section');
    if (resultsSection) {
        resultsSection.style.display = 'none';
    }
}

function showError(message) {
    const container = document.getElementById('movies-container');
    if (container) {
        container.innerHTML = `<div class="error-message">Ошибка: ${message}</div>`;
        showResults();
    }
}

// ===== ОБРАБОТЧИК КНОПКИ "ЗАРЕГИСТРИРОВАТЬСЯ" НА ГЛАВНОЙ СТРАНИЦЕ =====
document.addEventListener('DOMContentLoaded', function() {
    // Обработчик кнопки "Зарегистрироваться" на главной странице
    document.getElementById('nav-to-register')?.addEventListener('click', function(e) {
        e.preventDefault();
        setAuthMode('register');
        // Прокрутка к форме
        const authSection = document.getElementById('auth-section');
        if (authSection) {
            authSection.scrollIntoView({ behavior: 'smooth' });
        }
    });
    
    // Обработчик формы рекомендаций на recommend.html
    document.getElementById('recommend-form')?.addEventListener('submit', async function(e) {
        e.preventDefault();
        await handleRecommendByProfile();
    });
});

// ===== ФУНКЦИИ ДЛЯ РАБОТЫ С ПРОФИЛЕМ =====
function loadUserProfile() {
    const userId = getStoredUserId();
    if (!userId) {
        alert("Сначала зарегистрируйтесь");
        window.location.href = 'index.html';
        return;
    }
    
    fetch(`${API_BASE_URL}/api/profile/${userId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Ошибка загрузки профиля');
            }
            return response.json();
        })
        .then(data => {
            // Обновляем отображение на странице my_profile.html
            const displayGender = document.getElementById('display-gender');
            const displayAge = document.getElementById('display-age');
            const displayProfession = document.getElementById('display-profession');
            
            if (displayGender) {
                displayGender.textContent = data.gender ? (data.gender === 'male' ? 'Мужчина' : 'Женщина') : 'Не указано';
            }
            if (displayAge) {
                displayAge.textContent = data.age ? data.age : 'Не указан';
            }
            if (displayProfession) {
                // Словарь для отображения названий профессий
                const professionLabels = {
                    'academic/teacher': 'Академик / Преподаватель',
                    'artist': 'Художник / Артист',
                    'clerk/admin': 'Клерк / Администратор',
                    'student': 'Студент',
                    'customer_service': 'Обслуживание клиентов',
                    'medical': 'Врач / Медработник',
                    'executive/manager': 'Руководитель / Менеджер',
                    'farmer': 'Фермер',
                    'homemaker': 'Домохозяин/ка',
                    'journalist': 'Журналист',
                    'lawyer': 'Юрист',
                    'programmer': 'Программист',
                    'retired': 'Пенсионер',
                    'sales/marketing': 'Маркетолог / Продавец',
                    'scientist': 'Учёный',
                    'self-employed': 'Самозанятый',
                    'technician/engineer': 'Техник / Инженер',
                    'worker/craftsman': 'Рабочий / Ремесленник',
                    'unemployed': 'Безработный',
                    'writer': 'Писатель',
                    'other': 'Другое'
                };
                displayProfession.textContent = data.profession && professionLabels[data.profession]
                    ? professionLabels[data.profession]
                    : 'Не указана';
            }
            
            // Заполняем поля формы редактирования текущими значениями
            const editGender = document.getElementById('profile-gender');
            const editAge = document.getElementById('profile-age');
            const editProfession = document.getElementById('profile-profession');
            
            if (editGender) editGender.value = data.gender || '';
            if (editAge) editAge.value = data.age || '';
            if (editProfession) editProfession.value = data.profession || '';
        })
        .catch(error => {
            console.error('Ошибка загрузки профиля:', error);
            const messageDiv = document.getElementById('profile-message') || document.getElementById('profile-edit-message');
            messageDiv.textContent = 'Ошибка загрузки профиля: ' + error.message;
        });
}

function updateUserProfile() {
    const userId = getStoredUserId();
    if (!userId) {
        alert("Сначала зарегистрируйтесь");
        return;
    }
    
    const gender = document.getElementById('profile-gender')?.value || null;
    const age = document.getElementById('profile-age')?.value ? parseInt(document.getElementById('profile-age').value) : null;
    const profession = document.getElementById('profile-profession')?.value || null;
    
    fetch(`${API_BASE_URL}/api/profile/${userId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
            gender,
            age,
            profession
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Ошибка обновления профиля');
        }
        return response.json();
    })
    .then(data => {
        alert('✓ Профиль обновлен');
        // Перезагружаем страницу
        loadUserProfile();
    })
    .catch(error => {
        console.error('Ошибка обновления профиля:', error);
        document.getElementById('profile-message').textContent = 'Ошибка обновления профиля: ' + error.message;
    });
}

// ===== ОБРАБОТКА РЕКОМЕНДАЦИЙ ПО ПРОФИЛЮ (recommend.html) =====
async function handleRecommendByProfile() {
    const userId = getStoredUserId();
    if (!userId) {
        alert("Сначала зарегистрируйтесь");
        window.location.href = 'index.html';
        return;
    }
    
    // Проверяем, заполнена ли анкета
    try {
        const profileRes = await fetch(`${API_BASE_URL}/api/profile/${userId}`);
        if (profileRes.ok) {
            const profileData = await profileRes.json();
            if (!profileData.gender && !profileData.age && !profileData.profession) {
                if (!confirm("Анкета не заполнена. Перейти в профиль для заполнения?")) {
                    return;
                }
                window.location.href = 'my_profile.html';
                return;
            }
        }
    } catch (error) {
        console.error('Ошибка проверки профиля:', error);
    }
    
    const numMovies = parseInt(document.getElementById('rec-num')?.value) || 
                      parseInt(document.getElementById('num_movies')?.value);
    
    if (!numMovies || numMovies < 1) {
        alert("Укажите количество фильмов (от 1)");
        return;
    }
    
    // Показываем загрузку
    const loadingSection = document.getElementById('loading-section');
    const resultsSection = document.getElementById('results-section');
    const moviesContainer = document.getElementById('movies-container');
    
    if (loadingSection) loadingSection.style.display = 'block';
    if (resultsSection) resultsSection.style.display = 'none';
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/recommend/auto`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ num_movies: numMovies })
        });
        
        if (!response.ok) {
            if (response.status === 404) {
                throw new Error("Пользователь не найден");
            }
            throw new Error('Ошибка получения рекомендаций');
        }
        
        const data = await response.json();
        
        if (!moviesContainer) {
            console.log('Контейнер для фильмов не найден, результаты:', data);
            return;
        }
        
        if (data.movies.length === 0) {
            moviesContainer.innerHTML = `
                <div class="loading">
                    <p style="font-size: 3rem; margin-bottom: 15px;">😕</p>
                    <p>К сожалению, фильмы не найдены.</p>
                </div>
            `;
        } else {
            displayMovies(data.movies, 'profile');
        }
        
        if (resultsSection) resultsSection.style.display = 'block';
        
    } catch (error) {
        console.error('Ошибка рекомендаций:', error);
        if (moviesContainer) {
            moviesContainer.innerHTML = `<div class="error-message">Ошибка: ${error.message}</div>`;
        }
    } finally {
        if (loadingSection) loadingSection.style.display = 'none';
    }
}

function showNoResults() {
    const container = document.getElementById('movies-container');
    if (container) {
        container.innerHTML = `
            <div class="loading">
                <p style="font-size: 3rem; margin-bottom: 15px;">😕</p>
                <p>К сожалению, фильмы не найдены.</p>
                <p>Попробуйте изменить параметры поиска.</p>
            </div>
        `;
        showResults();
    }
}
