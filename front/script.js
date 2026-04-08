// ===== КОНФИГУРАЦИЯ =====
const API_BASE_URL = ""; // Относительный путь (тот же хост)

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

    console.log('Получены фильмы:', movies);

    movies.forEach((movie, index) => {
        const shortTitle = movie.movie_title.substring(0, 50);
        
        const card = document.createElement('div');
        card.className = 'movie-card';

        // Постер — всегда показываем заглушку, поверх грузим изображение
        let posterHtml;
        if (movie.poster_url) {
            posterHtml = `
                <div class="movie-poster" style="position:relative;">
                    <!-- Заглушка (видна пока грузится или при ошибке) -->
                    <div style="position:absolute; inset:0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display:flex; align-items:center; justify-content:center; text-align:center; padding:15px; z-index:1;">
                        <span style="font-size:1rem; font-weight:600; color:white; text-shadow:1px 1px 3px rgba(0,0,0,0.5);">${shortTitle}</span>
                    </div>
                    <!-- Изображение поверх заглушки -->
                    <img src="${movie.poster_url}" alt="${movie.movie_title}" 
                         style="position:relative; z-index:2; width:100%; height:100%; object-fit:cover;"
                         onerror="this.style.display='none';"
                         loading="lazy">
                </div>`;
        } else {
            posterHtml = `<div class="movie-poster" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display:flex; align-items:center; justify-content:center; text-align:center; padding:15px;">
                <span style="font-size:1rem; font-weight:600; color:white;">🎬 ${shortTitle}</span>
            </div>`;
        }

        // Жанры
        const genresHtml = movie.genres.map(g => `<span class="genre-tag">${g}</span>`).join('');

        // Рейтинг
        let ratingHtml = '';
        if (type === 'genre') {
            const rating = movie.avg_rating ? movie.avg_rating.toFixed(1) : 'N/A';
            const count = movie.rating_count || 0;
            ratingHtml = `
                <div class="movie-rating">
                    <span>⭐ ${rating}</span>
                    <span>${count} оценок</span>
                </div>
            `;
        } else {
            const predicted = movie.predicted_rating.toFixed(1);
            const score = movie.recommendation_score.toFixed(1);
            ratingHtml = `
                <div class="movie-rating">
                    <span class="predicted-rating">🎯 Прогноз: ${predicted}</span>
                    <span>Скор: ${score}</span>
                </div>
            `;
        }

        card.innerHTML = `
            ${posterHtml}
            <div class="movie-info">
                <div class="movie-title" title="${movie.movie_title}">${movie.movie_title}</div>
                <div class="movie-genres">${genresHtml}</div>
                ${ratingHtml}
            </div>
        `;

        container.appendChild(card);
    });
}

// ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====
function showLoading(show) {
    const loadingSection = document.getElementById('loading-section');
    if (loadingSection) {
        loadingSection.style.display = show ? 'block' : 'none';
    }
}

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
